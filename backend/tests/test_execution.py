import pytest
import asyncio
import os
from unittest.mock import MagicMock, patch
from execution import DockerExecutionStrategy, ExecutionResult, TimeoutExecutor, LocalExecutionStrategy, run_execution_task, ExecutionStrategy

@pytest.fixture
def docker_client_mock(mocker):
    client_mock = mocker.patch("execution.docker.from_env")
    return client_mock

@pytest.mark.asyncio
async def test_docker_execution_strategy_success(docker_client_mock, mocker):
    strategy = DockerExecutionStrategy(image="test-image", cleanup=True)
    mocker.patch("os.path.exists", return_value=True)
    container_mock = MagicMock()
    container_mock.id = "1234567890abcdef"
    container_mock.logs.return_value = b"Hello, World!"
    strategy.client.containers.create.return_value = container_mock
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"dummy_binary"))
    mocker.patch("execution.tarfile.open")
    async def mock_run_in_executor(*args, **kwargs):
        return 0
    mock_loop = MagicMock()
    mock_loop.run_in_executor = mock_run_in_executor
    mocker.patch("execution.asyncio.get_event_loop", return_value=mock_loop)
    result = await strategy.execute("/fake/path/binary", timeout_s=5)
    assert result.exit_code == 0
    assert result.output == "Hello, World!"
    assert not result.timed_out
    assert container_mock.start.called
    assert container_mock.remove.called

@pytest.mark.asyncio
async def test_docker_execution_strategy_timeout(docker_client_mock, mocker):
    strategy = DockerExecutionStrategy(image="test-image", cleanup=True)
    mocker.patch("os.path.exists", return_value=True)
    container_mock = MagicMock()
    container_mock.id = "1234567890abcdef"
    async def mock_run_in_executor(*args, **kwargs):
        raise Exception("Timeout Error")
    mock_loop = MagicMock()
    mock_loop.run_in_executor = mock_run_in_executor
    mocker.patch("execution.asyncio.get_event_loop", return_value=mock_loop)
    strategy.client.containers.create.return_value = container_mock
    mocker.patch("builtins.open", mocker.mock_open(read_data=b"dummy_binary"))
    mocker.patch("execution.tarfile.open")
    result = await strategy.execute("/fake/path/binary", timeout_s=1)
    assert result.exit_code == -1
    assert result.timed_out is True
    assert container_mock.kill.called
    assert container_mock.remove.called

@pytest.mark.asyncio
async def test_docker_execution_strategy_binary_not_found(mocker):
    strategy = DockerExecutionStrategy(image="test-image")
    mocker.patch("os.path.exists", return_value=False)
    result = await strategy.execute("/fake/missing", timeout_s=5)
    assert result.exit_code == -1
    assert result.timed_out is False
    assert "Binary not found" in result.error

def test_timeout_executor_init():
    executor = TimeoutExecutor(timeout_s=5)
    assert executor.timeout_s == 5

@pytest.mark.asyncio
async def test_timeout_executor_execute(mocker):
    mock_strategy = MagicMock()
    async def mock_execute(binary_path, timeout_s):
        return ExecutionResult(exit_code=0, duration_ms=10, timed_out=False)
    mock_strategy.execute = mock_execute
    executor = TimeoutExecutor(timeout_s=5, strategy=mock_strategy)
    result = await executor.execute("/dummy/path")
    assert result.exit_code == 0

@pytest.mark.asyncio
async def test_local_execution_strategy(mocker):
    strategy = LocalExecutionStrategy()
    mock_proc = MagicMock()
    mock_proc.communicate.return_value = (b"output", b"error")
    mock_proc.returncode = 0
    async def mock_create_subprocess_exec(*args, **kwargs):
        mock_proc.wait = mocker.AsyncMock(return_value=0)
        mock_proc.communicate = mocker.AsyncMock(return_value=(b"output", b"error"))
        return mock_proc
    mocker.patch("asyncio.create_subprocess_exec", new=mock_create_subprocess_exec)
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.access", return_value=True)
    result = await strategy.execute("/dummy/path")
    assert result.exit_code == 0
    assert result.output == "output"

def test_execution_result_str():
    r = ExecutionResult(0, 10, False, output="", error="")
    assert "ExecutionResult(exit_code=0, duration_ms=10, timed_out=False" in str(r)

def test_run_execution_task(mocker):
    mocker.patch("execution.TimeoutExecutor.execute", return_value=ExecutionResult(0, 10, False))
    r = run_execution_task("/some/binary", timeout_s=5)
    assert r.exit_code == 0

def test_execution_strategy_abc():
    class DummyStrategy(ExecutionStrategy):
        pass
    with pytest.raises(TypeError):
        DummyStrategy()
