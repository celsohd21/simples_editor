import os
import re
import structlog
import subprocess
import tempfile

logger = structlog.get_logger()

_ERROR_RE = re.compile(
    r"^(lexer|parser|semantic):(\d+):(\d+):\s*(.+)$",
    re.MULTILINE | re.IGNORECASE,
)


def parse_simplesc_errors(stderr: str) -> list[dict]:
    errors = []
    for match in _ERROR_RE.finditer(stderr):
        phase = match.group(1).lower()
        line = int(match.group(2))
        column = int(match.group(3))
        message = match.group(4).strip()
        errors.append({
            "phase": phase,
            "line": line,
            "column": column,
            "message": message,
        })
    if not errors and stderr.strip():
        errors.append({
            "phase": "erro",
            "line": 1,
            "column": 1,
            "message": stderr.strip(),
        })
    return errors


def compile_simples(code: str, timeout_s: int = 15) -> dict:
    max_code_kb = int(os.getenv('MAX_CODE_KB', '64'))
    code_kb = len(code.encode('utf-8')) / 1024

    if code_kb > max_code_kb:
        return {"ok": False, "errors": [{
            "phase": "validation",
            "line": 1,
            "column": 1,
            "message": f"Código excede {max_code_kb}KB ({code_kb:.1f}KB)"
        }]}

    with tempfile.TemporaryDirectory(prefix="simples-") as tmpdir:
        source_path = os.path.join(tmpdir, "program.simples")
        asm_path = os.path.join(tmpdir, "program.asm")

        with open(source_path, 'w', encoding='utf-8') as f:
            f.write(code)

        try:
            result = subprocess.run(
                ['simplesc', source_path, '-o', asm_path],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )

            if result.returncode != 0:
                errors = parse_simplesc_errors(result.stderr)
                return {"ok": False, "errors": errors}

            if not os.path.exists(asm_path):
                return {"ok": False, "errors": [{
                    "phase": "erro",
                    "line": 1,
                    "column": 1,
                    "message": "simplesc não gerou arquivo de saída"
                }]}

            with open(asm_path, 'r', encoding='utf-8') as f:
                nasm = f.read()

            logger.info("compile_success", nasm_size=len(nasm))
            return {"ok": True, "nasm": nasm}

        except subprocess.TimeoutExpired:
            return {"ok": False, "errors": [{
                "phase": "timeout",
                "line": 1,
                "column": 1,
                "message": f"Compilação excedeu {timeout_s}s"
            }]}

        except FileNotFoundError:
            return {"ok": False, "errors": [{
                "phase": "erro",
                "line": 1,
                "column": 1,
                "message": "Compilador 'simplesc' não encontrado no servidor"
            }]}

        except Exception as e:
            logger.error("compile_exception", error=str(e))
            return {"ok": False, "errors": [{
                "phase": "erro",
                "line": 1,
                "column": 1,
                "message": f"Erro interno: {str(e)}"
            }]}


def assemble_and_link(tmpdir: str, exec_timeout_s: int = 10) -> dict:
    asm_path = os.path.join(tmpdir, "program.asm")
    obj_path = os.path.join(tmpdir, "program.o")
    bin_path = os.path.join(tmpdir, "program")

    result = subprocess.run(
        ['nasm', '-f', 'elf32', asm_path, '-o', obj_path],
        capture_output=True, text=True, timeout=exec_timeout_s
    )
    if result.returncode != 0:
        return {"ok": False, "output": "", "error": "Falha na montagem NASM: " + (result.stderr or "")}

    result = subprocess.run(
        ['i686-linux-gnu-ld', '-m', 'elf_i386', obj_path, '-o', bin_path],
        capture_output=True, text=True, timeout=exec_timeout_s
    )
    if result.returncode != 0:
        return {"ok": False, "output": "", "error": "Falha na ligação: " + (result.stderr or "")}

    return {"ok": True, "bin_path": bin_path}


def run_simples(code: str, stdin_data: str = "", compile_timeout_s: int = 15, exec_timeout_s: int = 10) -> dict:
    compile_result = compile_simples(code, compile_timeout_s)
    if not compile_result['ok']:
        return compile_result

    with tempfile.TemporaryDirectory(prefix="simples-") as tmpdir:
        asm_path = os.path.join(tmpdir, "program.asm")
        with open(asm_path, 'w', encoding='utf-8') as f:
            f.write(compile_result['nasm'])

        link_result = assemble_and_link(tmpdir, compile_timeout_s)
        if not link_result['ok']:
            return {"ok": False, "errors": [{"phase": "erro", "line": 1, "column": 1, "message": link_result['error']}]}

        try:
            exec_result = subprocess.run(
                [link_result['bin_path']],
                input=stdin_data,
                capture_output=True,
                text=True,
                timeout=exec_timeout_s,
            )
            return {
                "ok": True,
                "nasm": compile_result['nasm'],
                "stdout": exec_result.stdout,
                "stderr": exec_result.stderr,
                "exit_code": exec_result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "errors": [{"phase": "runtime", "line": 1, "column": 1, "message": f"Execução excedeu {exec_timeout_s}s"}],
                "nasm": compile_result['nasm'],
            }
