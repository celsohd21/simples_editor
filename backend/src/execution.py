"""
Execution strategy for compiled programs with timeout handling.
Implements wall-clock timeout (10s) with asyncio.wait_for and graceful shutdown.
"""
import asyncio
import json
import subprocess
import sys
import structlog
import signal
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


logger = structlog.get_logger()


@dataclass
class ExecutionResult:
    """Result of program execution."""
    exit_code: int
    duration_ms: int
    timed_out: bool
    output: str = ""
    error: str = ""


class ExecutionStrategy(ABC):
    """Abstract base class for execution strategies."""
    
    @abstractmethod
    async def execute(self, binary_path: str, timeout_s: int = 10) -> ExecutionResult:
        """Execute a compiled binary with timeout."""
        pass


class LocalExecutionStrategy(ExecutionStrategy):
    """
    Executes compiled binary locally (subprocess) with wall-clock timeout.
    Uses asyncio.wait_for() to enforce the 10s limit.
    
    Flow:
    1. Start process
    2. Wrap in asyncio.wait_for(timeout=10)
    3. If timeout: kill process with SIGTERM
    4. If not killed: wait 1s then SIGKILL
    """
    
    async def execute(self, binary_path: str, timeout_s: int = 10) -> ExecutionResult:
        """
        Execute binary with timeout.
        
        Args:
            binary_path: Path to compiled executable (or script to run)
            timeout_s: Timeout in seconds (default 10s)
            
        Returns:
            ExecutionResult with exit code, duration, timeout flag
        """
        start_time = datetime.now()
        process = None
        
        try:
            # Determine if binary_path is a Python script
            is_python_script = binary_path.endswith('.py')
            
            if is_python_script:
                # Run Python script
                cmd = [sys.executable, binary_path]
            else:
                # Run compiled binary
                cmd = [binary_path]
            
            # Create subprocess for execution
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE,
            )
            
            logger.info(
                "execution_started",
                binary=binary_path,
                timeout_s=timeout_s,
                pid=process.pid
            )
            
            # Run with timeout using asyncio.wait_for
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_s
                )
                
                # Process completed normally
                exit_code = process.returncode
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                
                logger.info(
                    "execution_completed",
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                    timed_out=False
                )
                
                return ExecutionResult(
                    exit_code=exit_code,
                    duration_ms=duration_ms,
                    timed_out=False,
                    output=stdout.decode("utf-8", errors="replace"),
                    error=stderr.decode("utf-8", errors="replace")
                )
                
            except asyncio.TimeoutError:
                # Timeout exceeded - graceful shutdown
                logger.warning(
                    "execution_timeout",
                    timeout_s=timeout_s,
                    pid=process.pid
                )
                
                # Step 1: Send SIGTERM
                try:
                    process.send_signal(signal.SIGTERM)
                    logger.info("execution_sigterm_sent", pid=process.pid)
                except ProcessLookupError:
                    logger.warning("execution_process_already_dead", pid=process.pid)
                
                # Step 2: Wait 1s for graceful shutdown
                try:
                    await asyncio.wait_for(process.wait(), timeout=1.0)
                    logger.info("execution_sigterm_success", pid=process.pid)
                except asyncio.TimeoutError:
                    # Process didn't die from SIGTERM, use SIGKILL
                    logger.warning("execution_sigterm_failed", pid=process.pid)
                    try:
                        process.kill()
                        await process.wait()
                        logger.info("execution_sigkill_sent", pid=process.pid)
                    except ProcessLookupError:
                        logger.warning("execution_already_dead", pid=process.pid)
                
                # Collect any partial output
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=0.5
                    )
                except asyncio.TimeoutError:
                    stdout, stderr = b"", b""
                
                duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                
                return ExecutionResult(
                    exit_code=-1,  # Killed by timeout
                    duration_ms=duration_ms,
                    timed_out=True,
                    output=stdout.decode("utf-8", errors="replace"),
                    error=stderr.decode("utf-8", errors="replace")
                )
                
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(
                "execution_error",
                error=str(e),
                duration_ms=duration_ms
            )
            
            # Cleanup process if still alive
            if process and process.returncode is None:
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
            
            return ExecutionResult(
                exit_code=-1,
                duration_ms=duration_ms,
                timed_out=False,
                error=str(e)
            )


class TimeoutExecutor:
    """
    Wrapper for executing binaries with timeout enforcement.
    Provides synchronous interface for WebSocket handlers.
    """
    
    def __init__(self, timeout_s: int = 10, strategy: Optional[ExecutionStrategy] = None):
        """
        Initialize executor.
        
        Args:
            timeout_s: Execution timeout in seconds
            strategy: ExecutionStrategy instance (default: LocalExecutionStrategy)
        """
        self.timeout_s = timeout_s
        self.strategy = strategy or LocalExecutionStrategy()
    
    async def execute(self, binary_path: str) -> ExecutionResult:
        """Execute with timeout enforcement."""
        return await self.strategy.execute(binary_path, self.timeout_s)


def run_execution_task(binary_path: str, timeout_s: int = 10) -> ExecutionResult:
    """
    Convenience function to run execution in asyncio event loop.
    
    Usage:
        result = run_execution_task("/path/to/binary")
        print(f"Timed out: {result.timed_out}")
        print(f"Output: {result.output}")
    """
    executor = TimeoutExecutor(timeout_s)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(executor.execute(binary_path))
    finally:
        loop.close()
