import sys
sys.path.insert(0, r'C:\Users\FahadShaikh\Desktop\something')

from automation_scanner_v2 import AutomationScannerV2, ToolOutcome
from target_profile import TargetProfile
from decision_ledger import DecisionEngine
from execution_paths import get_executor

def test_tool_outcome():
    """Test ToolOutcome enum"""
    assert hasattr(ToolOutcome, 'SUCCESS_WITH_FINDINGS')
    assert hasattr(ToolOutcome, 'SUCCESS_NO_FINDINGS')
    assert hasattr(ToolOutcome, 'TIMEOUT')
    assert hasattr(ToolOutcome, 'EXECUTION_ERROR')
    print("✓ ToolOutcome enum")

def test_target_profile():
    """Test TargetProfile factory and properties"""
    p1 = TargetProfile.from_target("example.com")
    p2 = TargetProfile.from_target("api.example.com")
    p3 = TargetProfile.from_target("192.168.1.1")
    
    assert p1.type.name == "ROOT_DOMAIN"
    assert p2.type.name == "SUBDOMAIN"
    assert p3.type.name == "IP"
    assert p1.runtime_budget == 1800
    assert p2.runtime_budget == 900
    assert p3.runtime_budget == 600
    print("✓ TargetProfile.from_target()")

def test_decision_engine():
    """Test DecisionEngine builds ledger"""
    profile = TargetProfile.from_target("test.com")
    ledger = DecisionEngine.build_ledger(profile)
    
    allowed = ledger.get_allowed_tools()
    denied = ledger.get_denied_tools()
    
    assert len(allowed) > 0
    assert isinstance(allowed, list)
    print(f"✓ DecisionEngine ({len(allowed)} allowed, {len(denied)} denied)")

def test_execution_routing():
    """Test executor routing by target type"""
    p_ip = TargetProfile.from_target("10.0.0.1")
    p_root = TargetProfile.from_target("example.com")
    p_sub = TargetProfile.from_target("api.example.com")
    
    ledger = DecisionEngine.build_ledger(p_root)
    
    exec_ip = get_executor(p_ip, ledger)
    exec_root = get_executor(p_root, ledger)
    exec_sub = get_executor(p_sub, ledger)
    
    assert "IP" in exec_ip.__class__.__name__
    assert "Root" in exec_root.__class__.__name__
    assert "Subdomain" in exec_sub.__class__.__name__
    print("✓ Execution routing")

def test_scanner_instantiation():
    """Test scanner creates with all components"""
    scanner = AutomationScannerV2(target="example.com", output_dir="./test")
    
    assert scanner.target == "example.com"
    assert hasattr(scanner, 'profile')
    assert hasattr(scanner, 'ledger')
    assert hasattr(scanner, 'executor')
    assert scanner.executor is not None
    print("✓ Scanner instantiation")

def test_execution_plan():
    """Test execution plan generation"""
    scanner = AutomationScannerV2(target="example.com")
    plan = scanner.executor.get_execution_plan()
    
    assert isinstance(plan, list)
    assert len(plan) > 0
    assert len(plan[0]) == 3
    print(f"✓ Execution plan ({len(plan)} tools)")

def test_architecture_integration():
    """Test end-to-end architecture flow"""
    profile = TargetProfile.from_target("example.com")
    ledger = DecisionEngine.build_ledger(profile)
    executor = get_executor(profile, ledger)
    plan = executor.get_execution_plan()
    
    tool_names = [t[0] for t in plan]
    allowed_tools = ledger.get_allowed_tools()
    
    for tool in tool_names:
        assert tool in allowed_tools
    print("✓ Architecture integration")

if __name__ == "__main__":
    print("=" * 70)
    print("COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_tool_outcome,
        test_target_profile,
        test_decision_engine,
        test_execution_routing,
        test_scanner_instantiation,
        test_execution_plan,
        test_architecture_integration,
    ]
    
    passed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: {e}")
    
    print(f"\nRESULTS: {passed}/{len(tests)} tests passed")
    exit(0 if passed == len(tests) else 1)