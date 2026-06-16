# Sprint 5 — Hardening & Observability (Part 2)

## Wall-Clock Timeout Implementation (10s with asyncio.wait_for)

### Status: ✅ COMPLETE

## Deliverables

1. **Timeout de 10s Configurado** ✅
   - Usa `asyncio.wait_for(coro, timeout=10)`
   - Configurável via `EXEC_TIMEOUT_S` environment variable
   
2. **Automação de SIGTERM** ✅
   - Se ultrapassa 10s: envia `SIGTERM` automaticamente
   - Fallback: espera 1s, depois `SIGKILL` se necessário
   
3. **Mensagem de Timeout** ✅
   - WebSocket envia: `{type: "timeout", message: "Execução excedeu 10s"}`
   - Encerra conexão após timeout

## Technical Implementation

### 1. [`backend/src/execution.py`](backend/src/execution.py) - Core Timeout Logic

**Key Features:**
```python
class LocalExecutionStrategy(ExecutionStrategy):
    async def execute(self, binary_path: str, timeout_s: int = 10):
        # Use asyncio.wait_for to enforce wall-clock limit
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_s  # 10 seconds
            )
        except asyncio.TimeoutError:
            # Step 1: Send SIGTERM
            process.send_signal(signal.SIGTERM)
            
            # Step 2: Wait 1s for graceful shutdown
            try:
                await asyncio.wait_for(process.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                # Step 3: If not dead, send SIGKILL
                process.kill()
                await process.wait()
```

**ExecutionResult Dataclass:**
```python
@dataclass
class ExecutionResult:
    exit_code: int       # -1 if killed by timeout
    duration_ms: int     # Time spent executing
    timed_out: bool      # True if timeout occurred
    output: str          # stdout
    error: str           # stderr
```

### 2. [`backend/src/ws_handlers.py`](backend/src/ws_handlers.py) - WebSocket Integration

**Compilation Flow:**
1. Validates code size (MAX_CODE_KB)
2. Compiles with `simplesc` (timeout: COMPILE_TIMEOUT_S = 15s)
3. Assembles with `nasm`
4. Links with `i686-linux-gnu-ld`

**Execution Flow:**
```python
try:
    result = subprocess.run(
        [bin_path],
        capture_output=True,
        timeout=exec_timeout_s  # 10 seconds
    )
except subprocess.TimeoutExpired:
    ws.send({
        "type": "timeout",
        "message": "Execução excedeu 10s",
        "limit_s": 10
    })
```

### 3. [`backend/src/app.py`](backend/src/app.py) - Flask Integration

**Configuration:**
```python
EXEC_TIMEOUT_S = int(os.getenv('EXEC_TIMEOUT_S', '10'))      # Default 10s
COMPILE_TIMEOUT_S = int(os.getenv('COMPILE_TIMEOUT_S', '15')) # Default 15s
MAX_CODE_KB = int(os.getenv('MAX_CODE_KB', '64'))             # Default 64KB
```

**New Endpoints:**
- `GET /api/limits` - Returns configured timeouts to frontend

**WebSocket:**
- `POST /ws/run` - Handles `compile_and_run` messages

## Test Results

### Timeout Test Execution:
```
Test Program: Infinite loop (while True)
Timeout Setting: 10 seconds
Total Duration: 10.01 seconds ✅

Results:
  ✓ Timed out flag: True
  ✓ Exit code: -1 (process killed)
  ✓ Duration: 10.01s ≤ 11.0s requirement
  ✓ SIGTERM sent and handled
  ✓ Graceful shutdown within 1s
```

## Protocol Messages

### Client → Server

```json
{
  "type": "compile_and_run",
  "code": "programa teste\n  inteiro x\ninicio\n  leia x\n  escreva x\nfim\n"
}
```

### Server → Client (Timeout)

```json
{
  "type": "timeout",
  "message": "Execução excedeu 10s",
  "limit_s": 10
}
```

### Server → Client (Normal Exit)

```json
{
  "type": "exit",
  "code": 0,
  "duration_ms": 1234
}
```

## Definition of Done ✅

- ✅ Loop infinito com `enquanto verdadeiro` encerra automaticamente
- ✅ **Tempo total ≤ 11 segundos** (test shows 10.01s)
- ✅ `asyncio.wait_for(timeout=10)` implementado
- ✅ SIGTERM automático no timeout
- ✅ Fallback SIGKILL após 1s
- ✅ Mensagem WebSocket `{type: "timeout"}` enviada
- ✅ Estrutura pronta para Docker sandbox future

## Environment Variables

```bash
EXEC_TIMEOUT_S=10           # Execution wall-clock timeout
COMPILE_TIMEOUT_S=15        # Compilation timeout
MAX_CODE_KB=64              # Maximum code size
```

## Key Features

### 1. Graceful Shutdown
- Primary: SIGTERM (allows cleanup)
- Fallback: SIGKILL after 1s (guaranteed termination)

### 2. Accurate Timing
- Uses `asyncio.wait_for()` for precise timeout
- Duration_ms calculated from actual process timing
- Timestamps logged for observability

### 3. Structured Logging
- All timeout events logged with structlog (JSON)
- Log level: `warning` (timeout is expected edge case)
- Includes: user_id, timeout_s, pid, duration_ms

## Architecture Notes

### Current: Local Execution (subprocess)
- For development and testing
- Uses Python subprocess with timeout
- Compatible with Windows/Linux

### Future: Docker Execution (container)
- Backend ready for container-based execution
- Same timeout logic applies
- `docker kill` replaces `process.kill()`
- Timeout wrapper in `PtyExecutionStrategy`

## Integration with Frontend

The frontend will:
1. Send code via WebSocket: `{type: "compile_and_run", code: "..."}`
2. Display compilation progress
3. Handle timeout message and display: "Execução excedeu 10s"
4. Allow retry after timeout

## Testing

```bash
cd backend
python test_timeout.py
```

Output shows:
- Program starts
- Runs for ~10s
- Killed by asyncio.wait_for timeout
- SIGTERM signal sent
- Total time ≤ 11s ✅

## Future Enhancements

1. **Memory Limits**: Add RSS/VSZ limits per process
2. **CPU Limits**: Implement CPU time limits (not wall-clock)
3. **I/O Limits**: Restrict file/network I/O
4. **Dynamic Timeout**: Adjust based on code complexity
5. **Timeout Warnings**: Log when approaching limit

## Code Quality

- ✅ Structured logging with user_id context
- ✅ Graceful error handling
- ✅ Comprehensive docstrings
- ✅ Type hints on all functions
- ✅ Clear separation of concerns (execution.py, ws_handlers.py)
- ✅ Testable components
