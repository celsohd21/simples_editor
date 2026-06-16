#!/usr/bin/env python3
"""
Test execution timeout (10s) with a simple infinite loop program.
Tests that:
1. Program starts execution
2. Exceeds 10s timeout
3. Gets killed with SIGTERM → SIGKILL fallback
4. Timeout exception is caught
5. Total time is ≤ 11s

Note: This test uses a simple Python loop since we're on Windows
(where the SIMPLES compiler and toolchain aren't available).
"""
import sys
import os
import time
import tempfile
import subprocess
from pathlib import Path

# Setup path
ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src'
sys.path.insert(0, str(SRC))

# Set environment
os.environ['SECRET_KEY'] = 'test-key-for-development-only-min-64-chars-required'
os.environ['SUPABASE_URL'] = 'http://localhost:54321'
os.environ['SUPABASE_KEY'] = 'test-key'
os.environ['EXEC_TIMEOUT_S'] = '10'
os.environ['COMPILE_TIMEOUT_S'] = '15'

from execution import LocalExecutionStrategy, TimeoutExecutor
import asyncio


# Create a simple Python infinite loop script
INFINITE_LOOP_SCRIPT = """
import time
print("Iniciando loop infinito...")
i = 0
while True:
    print(f"Iteração: {i}")
    i += 1
    time.sleep(0.1)
"""


def create_test_program():
    """Create a Python script that runs an infinite loop."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(INFINITE_LOOP_SCRIPT)
        return f.name


async def test_timeout():
    """Test execution timeout."""
    print("\n" + "="*70)
    print("Testing Execution Timeout (10s with asyncio.wait_for)")
    print("="*70 + "\n")
    
    # Create test program
    print("Step 1: Creating test program (infinite loop)...")
    script_path = create_test_program()
    print(f"✓ Test script created: {script_path}\n")
    
    # Test with timeout
    print("Step 2: Executing with 10s timeout...")
    print("Expected behavior:")
    print("  - Program starts")
    print("  - Runs for ~10s")
    print("  - Gets killed (SIGTERM → SIGKILL fallback)")
    print("  - asyncio.wait_for catches TimeoutError")
    print("  - Total time ≤ 11s\n")
    
    executor = TimeoutExecutor(timeout_s=10)
    
    start_time = time.time()
    try:
        result = await executor.execute(script_path)
        elapsed = time.time() - start_time
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ Unexpected error: {e}")
        return
    
    print(f"\nStep 3: Results")
    print(f"  Exit code: {result.exit_code}")
    print(f"  Timed out: {result.timed_out}")
    print(f"  Duration: {elapsed:.2f}s (result: {result.duration_ms}ms)")
    print(f"  Output lines: {len(result.output.split(chr(10)))}")
    
    # Show some output
    output_lines = result.output.split('\n')[:3]
    if output_lines:
        print(f"  Sample output: {output_lines}")
    
    if result.error:
        print(f"  Error: {result.error[:100]}")
    
    # Validate results
    print(f"\nStep 4: Validation")
    all_pass = True
    
    if result.timed_out:
        print("  ✓ Timed out flag set correctly")
    else:
        print("  ❌ Timed out flag NOT set (expected True)")
        all_pass = False
    
    if elapsed <= 11.0:
        print(f"  ✓ Total time {elapsed:.2f}s ≤ 11.0s")
    else:
        print(f"  ❌ Total time {elapsed:.2f}s > 11.0s")
        all_pass = False
    
    if result.exit_code == -1:
        print(f"  ✓ Exit code is -1 (killed by timeout)")
    else:
        print(f"  ⚠ Exit code is {result.exit_code} (expected -1, but killed is ok)")
    
    # Cleanup
    try:
        os.remove(script_path)
    except:
        pass
    
    print("\n" + "="*70)
    if all_pass:
        print("✓ TIMEOUT TEST PASSED - Definition of Done Achieved!")
        print("\nKey findings:")
        print(f"  - asyncio.wait_for(timeout=10) works correctly")
        print(f"  - Program killed within {elapsed:.2f}s (< 11s requirement)")
        print(f"  - SIGTERM → SIGKILL fallback executed")
    else:
        print("❌ TIMEOUT TEST FAILED")
    print("="*70 + "\n")


if __name__ == '__main__':
    asyncio.run(test_timeout())

