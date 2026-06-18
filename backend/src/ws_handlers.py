"""
WebSocket handlers for code compilation and execution.
Protocol: /ws/run endpoint handles compile_and_run messages with timeout enforcement.
"""
import json
import subprocess
import tempfile
import os
import structlog
from flask_sock import Sock
from flask import request

logger = structlog.get_logger()


def create_ws_handlers(sock: Sock, exec_timeout_s: int = 10, compile_timeout_s: int = 15):
    """
    Create WebSocket handlers with configured timeouts.
    
    Args:
        sock: Flask-Sock instance
        exec_timeout_s: Execution timeout in seconds (default 10)
        compile_timeout_s: Compilation timeout in seconds (default 15)
    """
    
    @sock.route('/ws/run')
    def ws_run(ws):
        """
        WebSocket endpoint for compile_and_run.
        
        Protocol:
        - Client sends: {type: "compile_and_run", code: "programa...\n"}
        - Server responds with compilation/execution events
        - Client can send: {type: "stdin", data: "input\n"}
        - Server sends: {type: "stdout", data: "output\n"} or {type: "timeout"}
        """
        user_id = getattr(request, 'user_id', 'anonymous')
        
        logger.info(
            "ws_run_connected",
            user_id=user_id,
            remote_addr=request.remote_addr
        )
        
        try:
            while True:
                try:
                    # Receive message from client
                    message_str = ws.receive(timeout=None)
                    if message_str is None:
                        break
                    
                    message = json.loads(message_str)
                    message_type = message.get('type')
                    
                    logger.info(
                        "ws_message_received",
                        user_id=user_id,
                        message_type=message_type
                    )
                    
                    if message_type == "compile_and_run":
                        handle_compile_and_run(ws, message, user_id, compile_timeout_s, exec_timeout_s)
                    
                    elif message_type == "stdin":
                        # Will be handled by execution strategy in future
                        logger.info("ws_stdin_received", user_id=user_id)
                    
                    elif message_type == "stop":
                        from metrics import EXECUTIONS
                        EXECUTIONS.labels(status='stop').inc()
                        logger.info("ws_stop_requested", user_id=user_id)
                        ws.send(json.dumps({"type": "exit", "code": -15, "duration_ms": 0}))
                        break
                    
                    elif message_type == "ping":
                        ws.send(json.dumps({"type": "pong"}))
                    
                    else:
                        logger.warning("ws_unknown_message_type", message_type=message_type)
                
                except json.JSONDecodeError as e:
                    logger.warning("ws_invalid_json", error=str(e))
                    ws.send(json.dumps({"type": "internal_error", "message": "Invalid JSON"}))
                    continue
                
        except Exception as e:
            logger.error(
                "ws_error",
                user_id=user_id,
                error=str(e)
            )
        finally:
            logger.info(
                "ws_run_disconnected",
                user_id=user_id
            )


def handle_compile_and_run(ws, message, user_id, compile_timeout_s, exec_timeout_s):
    """
    Handle compile_and_run message.
    
    Steps:
    1. Validate code size
    2. Create temp directory
    3. Write code to file
    4. Run simplesc with timeout
    5. If success: assemble and link
    6. Execute binary with asyncio.wait_for timeout
    7. Send results or timeout message
    """
    code = message.get('code', '')
    
    # Validate code size
    max_code_kb = int(os.getenv('MAX_CODE_KB', '64'))
    code_kb = len(code.encode('utf-8')) / 1024
    
    if code_kb > max_code_kb:
        from metrics import COMPILATIONS
        COMPILATIONS.labels(status='error').inc()
        logger.warning(
            "code_too_large",
            user_id=user_id,
            code_kb=code_kb,
            max_code_kb=max_code_kb
        )
        ws.send(json.dumps({
            "type": "compile_error",
            "message": f"Código excede {max_code_kb}KB"
        }))
        return
    
    # Send compile started
    ws.send(json.dumps({"type": "compile_started"}))
    
    # Create temp directory
    with tempfile.TemporaryDirectory(prefix="simples-") as tmpdir:
        try:
            source_path = os.path.join(tmpdir, "program.simples")
            asm_path = os.path.join(tmpdir, "program.asm")
            obj_path = os.path.join(tmpdir, "program.o")
            bin_path = os.path.join(tmpdir, "program")
            
            # Write source code
            with open(source_path, 'w') as f:
                f.write(code)
            
            logger.info(
                "code_written",
                user_id=user_id,
                source_path=source_path,
                code_size_kb=code_kb
            )
            
            # Compile with simplesc
            try:
                result = subprocess.run(
                    ['simplesc', source_path, '-o', asm_path],
                    capture_output=True,
                    text=True,
                    timeout=compile_timeout_s
                )
                
                if result.returncode != 0:
                    from metrics import COMPILATIONS
                    COMPILATIONS.labels(status='error').inc()
                    logger.warning(
                        "compile_error",
                        user_id=user_id,
                        stderr=result.stderr[:500]
                    )
                    ws.send(json.dumps({
                        "type": "compile_error",
                        "phase": "simplesc",
                        "message": result.stderr or "Compilation failed"
                    }))
                    return
                
                logger.info(
                    "compile_success",
                    user_id=user_id,
                    asm_path=asm_path
                )
                
                # Read and send generated assembly
                with open(asm_path, 'r') as f:
                    asm_code = f.read()
                
                ws.send(json.dumps({
                    "type": "asm_generated",
                    "asm": asm_code[:10000]  # Limit output
                }))
                
            except subprocess.TimeoutExpired:
                from metrics import COMPILATIONS
                COMPILATIONS.labels(status='error').inc()
                logger.error(
                    "compile_timeout",
                    user_id=user_id,
                    timeout_s=compile_timeout_s
                )
                ws.send(json.dumps({
                    "type": "compile_error",
                    "phase": "simplesc",
                    "message": f"Compilação excedeu {compile_timeout_s}s"
                }))
                return
            
            # Assemble with nasm
            try:
                result = subprocess.run(
                    ['nasm', '-f', 'elf32', asm_path, '-o', obj_path],
                    capture_output=True,
                    text=True,
                    timeout=compile_timeout_s
                )
                
                if result.returncode != 0:
                    from metrics import COMPILATIONS
                    COMPILATIONS.labels(status='error').inc()
                    logger.warning("assemble_error", user_id=user_id)
                    ws.send(json.dumps({
                        "type": "assemble_error",
                        "message": result.stderr or "Assembly failed"
                    }))
                    return
                
                logger.info("assemble_success", user_id=user_id)
                
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                from metrics import COMPILATIONS
                COMPILATIONS.labels(status='error').inc()
                logger.error("assemble_error", user_id=user_id, error=str(e))
                ws.send(json.dumps({
                    "type": "assemble_error",
                    "message": str(e)
                }))
                return
            
            # Link with i686-linux-gnu-ld
            try:
                result = subprocess.run(
                    ['i686-linux-gnu-ld', '-m', 'elf_i386', '-dynamic-linker',
                     '/lib/ld-linux.so.2', obj_path, '-lc', '-o', bin_path],
                    capture_output=True,
                    text=True,
                    timeout=compile_timeout_s
                )
                
                if result.returncode != 0:
                    from metrics import COMPILATIONS
                    COMPILATIONS.labels(status='error').inc()
                    logger.warning("link_error", user_id=user_id)
                    ws.send(json.dumps({
                        "type": "link_error",
                        "message": result.stderr or "Linking failed"
                    }))
                    return
                
                from metrics import COMPILATIONS
                COMPILATIONS.labels(status='success').inc()
                logger.info("link_success", user_id=user_id)
                
            except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                from metrics import COMPILATIONS
                COMPILATIONS.labels(status='error').inc()
                logger.error("link_error", user_id=user_id, error=str(e))
                ws.send(json.dumps({
                    "type": "link_error",
                    "message": str(e)
                }))
                return
            
            # Execute with timeout
            ws.send(json.dumps({"type": "exec_started"}))
            
            logger.info(
                "execution_starting",
                user_id=user_id,
                binary=bin_path,
                timeout_s=exec_timeout_s
            )
            
            try:
                result = subprocess.run(
                    [bin_path],
                    capture_output=True,
                    text=True,
                    timeout=exec_timeout_s
                )
                
                # Execution completed normally
                output = result.stdout
                error = result.stderr
                exit_code = result.returncode
                
                if output:
                    ws.send(json.dumps({
                        "type": "stdout",
                        "data": output
                    }))
                
                if error:
                    ws.send(json.dumps({
                        "type": "stderr",
                        "data": error
                    }))
                
                from metrics import EXECUTIONS
                EXECUTIONS.labels(status='success' if exit_code == 0 else 'error').inc()
                logger.info(
                    "execution_completed",
                    user_id=user_id,
                    exit_code=exit_code,
                    timed_out=False
                )
                
                ws.send(json.dumps({
                    "type": "exit",
                    "code": exit_code,
                    "duration_ms": 0
                }))
                
            except subprocess.TimeoutExpired:
                # TIMEOUT OCCURRED - key part of Sprint 5
                from metrics import EXECUTIONS
                EXECUTIONS.labels(status='timeout').inc()
                logger.warning(
                    "execution_timeout",
                    user_id=user_id,
                    timeout_s=exec_timeout_s
                )
                
                ws.send(json.dumps({
                    "type": "timeout",
                    "message": f"Execução excedeu {exec_timeout_s}s",
                    "limit_s": exec_timeout_s
                }))
        
        except Exception as e:
            from metrics import EXECUTIONS
            EXECUTIONS.labels(status='error').inc()
            logger.error(
                "execution_exception",
                user_id=user_id,
                error=str(e)
            )
            ws.send(json.dumps({
                "type": "internal_error",
                "message": str(e)
            }))


def register_ws_handlers(app, sock, exec_timeout_s: int = 10, compile_timeout_s: int = 15):
    """Register WebSocket handlers with Flask app."""
    create_ws_handlers(sock, exec_timeout_s, compile_timeout_s)
