import pytest
import json
from unittest.mock import MagicMock
from ws_handlers import handle_compile_and_run

@pytest.fixture
def mock_ws():
    ws = MagicMock()
    return ws

def test_handle_compile_and_run_size_limit(mock_ws, mocker):
    mocker.patch("os.getenv", return_value="1") # 1KB limit
    large_code = "a" * 2048 # 2KB
    message = {"code": large_code}

    handle_compile_and_run(mock_ws, message, "user1", 15, 10)

    # Assert correct warning sent
    calls = mock_ws.send.call_args_list
    assert len(calls) == 1
    response = json.loads(calls[0][0][0])
    assert response["type"] == "compile_error"
    assert "Código excede" in response["message"]

def test_handle_compile_and_run_compile_error(mock_ws, mocker):
    mocker.patch("os.getenv", return_value="64")
    message = {"code": "invalid code"}

    # Mock file writing and subprocess
    mocker.patch("builtins.open", mocker.mock_open())

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "Syntax Error"
    mocker.patch("subprocess.run", return_value=mock_result)

    handle_compile_and_run(mock_ws, message, "user1", 15, 10)

    calls = mock_ws.send.call_args_list
    assert len(calls) == 2
    assert json.loads(calls[0][0][0])["type"] == "compile_started"
    assert json.loads(calls[1][0][0])["type"] == "compile_error"
    assert json.loads(calls[1][0][0])["message"] == "Syntax Error"

def test_handle_compile_and_run_success(mock_ws, mocker):
    mocker.patch("os.getenv", return_value="64")
    message = {"code": "valid code"}

    # Needs to return success for simplesc, nasm, ld and the final execution
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = "Program Output"
    mock_result.stderr = ""
    mocker.patch("subprocess.run", return_value=mock_result)

    # Mock open for writing and reading ASM
    mocker.patch("builtins.open", mocker.mock_open(read_data="dummy_asm"))

    handle_compile_and_run(mock_ws, message, "user1", 15, 10)

    calls = mock_ws.send.call_args_list
    responses = [json.loads(c[0][0]) for c in calls]
    types = [r["type"] for r in responses]

    assert "compile_started" in types
    assert "asm_generated" in types
    assert "exec_started" in types
    assert "stdout" in types
    assert "exit" in types

import subprocess
def test_handle_compile_and_run_timeout(mock_ws, mocker):
    mocker.patch("os.getenv", return_value="64")
    message = {"code": "valid code"}

    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="test", timeout=15))

    handle_compile_and_run(mock_ws, message, "user1", 15, 10)

    calls = mock_ws.send.call_args_list
    types = [json.loads(c[0][0])["type"] for c in calls]
    assert "compile_started" in types
    assert "compile_error" in types

from ws_handlers import create_ws_handlers, register_ws_handlers

def test_register_ws_handlers(mocker):
    mock_app = MagicMock()
    mock_sock = MagicMock()

    register_ws_handlers(mock_app, mock_sock)

    mock_sock.route.assert_called_with('/ws/run')

def test_handle_compile_and_run_link_error(mock_ws, mocker):
    mocker.patch("os.getenv", return_value="64")
    message = {"code": "valid code"}
    mocker.patch("builtins.open", mocker.mock_open())

    def side_effect(cmd, **kwargs):
        res = MagicMock()
        if 'simplesc' in cmd:
            res.returncode = 0
        elif 'nasm' in cmd:
            res.returncode = 0
        elif 'i686-linux-gnu-ld' in cmd:
            res.returncode = 1
            res.stderr = "Linking Error"
        return res

    mocker.patch("subprocess.run", side_effect=side_effect)

    handle_compile_and_run(mock_ws, message, "user1", 15, 10)
    calls = mock_ws.send.call_args_list
    types = [json.loads(c[0][0])["type"] for c in calls]
    assert "link_error" in types

def test_handle_compile_and_run_assemble_error(mock_ws, mocker):
    mocker.patch("os.getenv", return_value="64")
    message = {"code": "valid code"}
    mocker.patch("builtins.open", mocker.mock_open())

    def side_effect(cmd, **kwargs):
        res = MagicMock()
        if 'simplesc' in cmd:
            res.returncode = 0
        elif 'nasm' in cmd:
            res.returncode = 1
            res.stderr = "Assemble Error"
        return res

    mocker.patch("subprocess.run", side_effect=side_effect)

    handle_compile_and_run(mock_ws, message, "user1", 15, 10)
    calls = mock_ws.send.call_args_list
    types = [json.loads(c[0][0])["type"] for c in calls]
    assert "assemble_error" in types

from ws_handlers import create_ws_handlers
def test_create_ws_handlers(mocker):
    mock_sock = MagicMock()
    create_ws_handlers(mock_sock)
    assert mock_sock.route.called

def test_handle_compile_and_run_exception(mock_ws, mocker):
    mocker.patch("os.getenv", return_value="64")
    message = {"code": "valid code"}
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("subprocess.run", side_effect=Exception("Unexpected Error"))

    handle_compile_and_run(mock_ws, message, "user1", 15, 10)
    calls = mock_ws.send.call_args_list
    types = [json.loads(c[0][0])["type"] for c in calls]
    assert "internal_error" in types

def test_handle_compile_and_run_subprocess_exception(mock_ws, mocker):
    mocker.patch("os.getenv", return_value="64")
    message = {"code": "valid code"}
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("subprocess.run", side_effect=Exception("Execution Error"))
    handle_compile_and_run(mock_ws, message, "user1", 15, 10)
    calls = mock_ws.send.call_args_list
    types = [json.loads(c[0][0])["type"] for c in calls]
    assert "internal_error" in types

def test_handle_compile_and_run_exec_timeout(mock_ws, mocker):
    mocker.patch("os.getenv", return_value="64")
    message = {"code": "valid code"}
    mocker.patch("builtins.open", mocker.mock_open())
    import subprocess

    def side_effect(cmd, **kwargs):
        res = MagicMock()
        if 'simplesc' in cmd:
            res.returncode = 0
        elif 'nasm' in cmd:
            res.returncode = 0
        elif 'i686-linux-gnu-ld' in cmd:
            res.returncode = 0
        else:
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=10)
        return res
    mocker.patch("subprocess.run", side_effect=side_effect)

    handle_compile_and_run(mock_ws, message, "user1", 15, 10)
    calls = mock_ws.send.call_args_list
    types = [json.loads(c[0][0])["type"] for c in calls]
    assert "timeout" in types

def test_ws_run_messages(mocker):
    from ws_handlers import create_ws_handlers
    import json

    mock_sock = MagicMock()
    mock_app = MagicMock()

    # Store the route decorator
    route_func = None
    def mock_route(path):
        def decorator(f):
            nonlocal route_func
            route_func = f
            return f
        return decorator
    mock_sock.route = mock_route

    create_ws_handlers(mock_sock)

    # Simulate ws
    mock_ws = MagicMock()

    # Return different messages
    messages = [
        json.dumps({"type": "compile_and_run", "code": "valid"}),
        json.dumps({"type": "stdin", "data": "dummy"}),
        json.dumps({"type": "stop"}),
        json.dumps({"type": "ping"}),
        "invalid json",
        None # to exit loop
    ]

    msg_iter = iter(messages)
    def mock_receive(timeout=None):
        return next(msg_iter)

    mock_ws.receive.side_effect = mock_receive

    mocker.patch("ws_handlers.handle_compile_and_run")

    class MockRequest:
        user_id = 'user1'
        remote_addr = '127.0.0.1'

    mocker.patch("ws_handlers.request", new=MockRequest())

    route_func(mock_ws)

    assert mock_ws.send.called
