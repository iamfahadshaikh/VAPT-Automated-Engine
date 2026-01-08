#!/usr/bin/env python3
"""
COMPREHENSIVE TEST RUNNER - All tests, APIs, and modules in one command
Executes all validation in sequence and produces a unified report
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_command(name: str, cmd: str, capture=True) -> tuple[bool, str]:
    """Run a command and return (success, output)"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=capture,
            text=True,
            timeout=300,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT (300s)"
    except Exception as e:
        return False, str(e)


def main():
    workspace = Path(__file__).parent
    start_time = datetime.now()
    
    print("\n" + "=" * 100)
    print("COMPREHENSIVE FULL TEST SUITE - ALL FUNCTIONS, APIs, AND MODULES")
    print("=" * 100)
    print(f"Workspace: {workspace}")
    print(f"Started: {start_time.isoformat()}")
    print("=" * 100 + "\n")
    
    tests = [
        (
            "1. MODULE IMPORT VALIDATION",
            f"{sys.executable} {workspace / 'test_all_modules.py'}",
        ),
        (
            "2. SCANNER CORE FUNCTIONS",
            f"{sys.executable} {workspace / 'test_scanner_functions.py'}",
        ),
        (
            "3. INTELLIGENCE EXTRACTION & FINDINGS",
            f"{sys.executable} {workspace / 'test_intelligence_extraction.py'}",
        ),
        (
            "4. CACHE GATING LOGIC",
            f"{sys.executable} {workspace / 'test_cache_gating.py'}",
        ),
        (
            "5. INTEGRATION TESTS",
            f"{sys.executable} {workspace / 'test_integration.py'}",
        ),
        (
            "6. FULL TEST SUITE",
            f"{sys.executable} {workspace / 'test_suite.py'}",
        ),
    ]
    
    results = []
    
    for test_name, cmd in tests:
        print(f"\n{'='*100}")
        print(f"{test_name}")
        print(f"{'='*100}")
        print(f"Command: {cmd}\n")
        
        success, output = run_command(test_name, cmd, capture=True)
        
        # Print output
        if output:
            print(output)
        
        status = "[PASS]" if success else "[FAIL]"
        results.append((test_name, success))
        print(f"\n{status}")
    
    # SUMMARY REPORT
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    passed = sum(1 for _, s in results if s)
    failed = sum(1 for _, s in results if not s)
    
    print("\n" + "=" * 100)
    print("FINAL SUMMARY")
    print("=" * 100)
    print(f"Total Tests: {len(results)}")
    print(f"Passed: {passed} [OK]")
    print(f"Failed: {failed} [FAIL]")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")
    print(f"Duration: {duration:.2f}s")
    print("=" * 100)
    
    print("\nDETAILED RESULTS:")
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {test_name}")
    
    print("\n" + "=" * 100)
    if failed == 0:
        print("SUCCESS: ALL TESTS PASSED! Scanner is fully operational.")
    else:
        print(f"WARNING: {failed} test(s) failed. Review output above for details.")
    print("=" * 100 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
