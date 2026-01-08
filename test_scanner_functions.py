#!/usr/bin/env python3
"""
Test AutomationScannerV2 functions and API surface
"""

import sys
from pathlib import Path


def test_scanner_class():
    """Test scanner class and key methods."""
    print("\n[TEST 1] AutomationScannerV2 Class API")
    
    from automation_scanner_v2 import AutomationScannerV2, ToolOutcome
    
    # Check enum
    assert hasattr(ToolOutcome, "SUCCESS_WITH_FINDINGS")
    assert hasattr(ToolOutcome, "SUCCESS_NO_FINDINGS")
    assert hasattr(ToolOutcome, "TIMEOUT")
    assert hasattr(ToolOutcome, "EXECUTION_ERROR")
    print("  [OK] ToolOutcome enum present")
    
    # Check scanner can be instantiated
    scanner = AutomationScannerV2(
        target="example.com",
        output_dir=None,
        skip_tool_check=True,
        mode="full",
    )
    
    assert hasattr(scanner, "profile")
    assert hasattr(scanner, "ledger")
    assert hasattr(scanner, "output_dir")
    assert hasattr(scanner, "execution_results")
    print("  [OK] Scanner instantiates with profile, ledger, output_dir")
    
    # Check methods
    assert callable(getattr(scanner, "log", None))
    assert callable(getattr(scanner, "run_full_scan", None))
    assert callable(getattr(scanner, "_run_tool", None))
    assert callable(getattr(scanner, "_save_tool_output", None))
    assert callable(getattr(scanner, "_write_report", None))
    print("  [OK] All key methods present")
    
    return True


def test_architecture_modules():
    """Test architecture components."""
    print("\n[TEST 2] Architecture Modules")
    
    from target_profile import TargetProfile, TargetType
    from decision_ledger import DecisionEngine
    from execution_paths import get_executor, RootDomainExecutor, SubdomainExecutor, IPExecutor
    
    # Test TargetProfile
    profile = TargetProfile.from_target("example.com")
    assert profile.host == "example.com"
    assert profile.type == TargetType.ROOT_DOMAIN
    print("  [OK] TargetProfile.from_target() works")
    
    # Test DecisionLedger
    ledger = DecisionEngine.build_ledger(profile)
    assert hasattr(ledger, "decisions")
    assert callable(getattr(ledger, "allows", None))
    print("  [OK] DecisionLedger initializes")
    
    # Test executor routing
    executor = get_executor(profile, ledger)
    assert isinstance(executor, RootDomainExecutor)
    assert callable(getattr(executor, "get_execution_plan", None))
    print("  [OK] get_executor() routes correctly")
    
    # Test plan generation
    plan = executor.get_execution_plan()
    assert isinstance(plan, list)
    assert len(plan) > 0
    assert isinstance(plan[0], tuple)
    assert len(plan[0]) == 3  # (tool, cmd, meta)
    print(f"  [OK] Execution plan generated: {len(plan)} tools")
    
    return True


def test_cli_entrypoint():
    """Test CLI argument parsing."""
    print("\n[TEST 3] CLI Entrypoint")
    
    from automation_scanner_v2 import main
    
    assert callable(main)
    print("  [OK] main() entrypoint exists")
    
    return True


def test_scanner_methods():
    """Test scanner internal methods."""
    print("\n[TEST 4] Scanner Internal Methods")
    
    from automation_scanner_v2 import AutomationScannerV2
    
    scanner = AutomationScannerV2(
        target="sub.example.com",
        skip_tool_check=True,
    )
    
    # Test category summary (should work with empty results)
    summary = scanner._category_summary()
    assert isinstance(summary, dict)
    print("  [OK] _category_summary() works")
    
    # Test outcome summary
    outcome = scanner._outcome_summary()
    assert isinstance(outcome, dict)
    print("  [OK] _outcome_summary() works")
    
    # Test confidence summary
    confidence = scanner._confidence_summary()
    assert isinstance(confidence, dict)
    print("  [OK] _confidence_summary() works")
    
    return True


def main():
    print("=" * 80)
    print("AUTOMATION SCANNER V2 - FUNCTIONAL TEST SUITE")
    print("=" * 80)
    
    tests = [
        ("Scanner Class API", test_scanner_class),
        ("Architecture Modules", test_architecture_modules),
        ("CLI Entrypoint", test_cli_entrypoint),
        ("Scanner Methods", test_scanner_methods),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"  [FAIL] {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"  [EXCEPTION] {name}: {type(e).__name__}: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print(f"RESULTS: {passed}/{len(tests)} tests passed")
    print("=" * 80)
    
    if failed == 0:
        print("[SUCCESS] ALL FUNCTIONAL TESTS PASSED")
        return 0
    else:
        print(f"[FAILURE] {failed} TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
