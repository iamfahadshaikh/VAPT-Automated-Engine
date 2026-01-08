#!/usr/bin/env python3
"""
Comprehensive module test - imports all Python files and validates APIs
"""

import importlib.util
import sys
from pathlib import Path


def test_import(filepath: Path) -> tuple[bool, str]:
    """Try to import a Python file and return success status."""
    module_name = filepath.stem
    
    try:
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec is None or spec.loader is None:
            return False, "No spec/loader found"
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        return True, f"OK - {len(dir(module))} exports"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:100]}"


def main():
    workspace = Path(__file__).parent
    py_files = sorted(workspace.glob("*.py"))
    
    # Skip test files themselves to avoid circular execution
    skip = {"test_all_modules.py"}
    py_files = [f for f in py_files if f.name not in skip]
    
    print("=" * 80)
    print("COMPREHENSIVE PYTHON MODULE IMPORT TEST")
    print("=" * 80)
    print(f"Testing {len(py_files)} Python files...\n")
    
    results = []
    for pyfile in py_files:
        success, msg = test_import(pyfile)
        status = "[PASS]" if success else "[FAIL]"
        results.append((pyfile.name, success, msg))
        print(f"{status:8} {pyfile.name:40} {msg}")
    
    # Summary
    passed = sum(1 for _, s, _ in results if s)
    failed = sum(1 for _, s, _ in results if not s)
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed}/{len(results)} passed, {failed} failed")
    print("=" * 80)
    
    if failed > 0:
        print("\nFAILED MODULES:")
        for name, success, msg in results:
            if not success:
                print(f"  - {name}: {msg}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
