REFACTOR CHECKLIST - automation_scanner_v2.py
==============================================

This is the exact order. Do not skip. Do not reorder.

---

## PHASE 1: SETUP (5 mins)

- [ ] Open automation_scanner_v2.py
- [ ] Read REFACTOR_AUTOMATION_SCANNER_V2.md (takes 10 mins)
- [ ] Backup automation_scanner_v2.py as automation_scanner_v2_backup.py
- [ ] Test current scanner works: python3 automation_scanner_v2.py example.com --skip-install

---

## PHASE 2: IMPORTS (2 mins)

Location: Top of automation_scanner_v2.py, around line 25

**Delete**:
```python
from target_classifier import TargetClassifierBuilder, ScanContext, TargetType, TargetScope
```

**Add**:
```python
from architecture_integration import ArchitectureIntegration
from target_profile import TargetProfile, TargetType
from decision_ledger import DecisionLedger
from architecture_guards import ArchitectureViolation
from execution_paths import get_executor
```

**Verify**: No `classifier` or `context` imports remain

---

## PHASE 3: __init__ REFACTOR (10 mins)

Location: Lines ~70-105

**Find and replace entire init block**:

OLD:
```python
def __init__(self, target, protocol='https', ...):
    try:
        self.classifier = TargetClassifierBuilder.from_string(target, scheme=protocol)
        self.context = ScanContext(self.classifier)
    except ValueError as e:
        print(f"[ERROR] Invalid target: {e}")
        sys.exit(1)
    
    self.target = self.classifier.host
    self.protocol = self.classifier.scheme
```

NEW:
```python
def __init__(self, target, protocol='https', ...):
    try:
        self.profile = ArchitectureIntegration.create_profile_from_scanner_args(
            target=target,
            scheme=protocol,
            port=443 if protocol == 'https' else 80
        )
        self.ledger = ArchitectureIntegration.build_ledger(self.profile)
        ArchitectureIntegration.validate_architecture(self.profile, self.ledger)
    except ValueError as e:
        print(f"[ERROR] Invalid target: {e}")
        sys.exit(1)
    except ArchitectureViolation as e:
        print(f"[ERROR] Architecture violation: {e}")
        sys.exit(1)
    
    self.target = self.profile.host
    self.protocol = self.profile.scheme
```

**Verify**: 
- [ ] No self.classifier
- [ ] No self.context
- [ ] Has self.profile
- [ ] Has self.ledger
- [ ] Validation called

---

## PHASE 4: REPLACE run_full_scan() (10 mins)

Location: Lines ~1100-1200

**Replace entire method**:

```python
def run_full_scan(self):
    """Execute complete security assessment - ARCHITECTURE DRIVEN"""
    
    print("\n" + "="*80)
    print("INTELLIGENT SECURITY SCANNER - ARCHITECTURE DRIVEN")
    print(f"Target: {self.target}")
    print(f"Type: {self.profile.target_type.value.upper()}")
    print(f"Base Domain: {self.profile.base_domain or 'N/A'}")
    print("="*80)
    
    try:
        path = ArchitectureIntegration.route_execution(self.profile, self.ledger)
        
        if path == "root":
            self._run_root_domain_scan()
        elif path == "subdomain":
            self._run_subdomain_scan()
        elif path == "ip":
            self._run_ip_scan()
        else:
            raise ArchitectureViolation(f"Unknown execution path: {path}")
    
    except ArchitectureViolation as e:
        self.log(f"Architecture violation: {e}", "ERROR")
        sys.exit(1)
    except KeyboardInterrupt:
        self.log("Scan interrupted by user", "WARN")
    except Exception as e:
        self.log(f"Fatal error: {str(e)}", "ERROR")
    finally:
        self._finalize_scan(gate_mode=False)
```

**Verify**:
- [ ] Method routes to three paths only
- [ ] _run_root_domain_scan() called
- [ ] _run_subdomain_scan() called
- [ ] _run_ip_scan() called
- [ ] ArchitectureViolation caught

---

## PHASE 5: ADD THREE EXECUTION PATH METHODS (15 mins)

Add these three methods to ComprehensiveSecurityScanner class:

```python
def _run_root_domain_scan(self):
    """Root domain execution path - full reconnaissance"""
    self.log("Executing ROOT DOMAIN reconnaissance path", "INFO")
    
    executor = get_executor(self.profile, self.ledger)
    plan = executor.get_execution_plan()
    
    self.log(f"Execution plan: {len(plan)} tools", "INFO")
    
    for tool_name, command, metadata in plan:
        if not self.ledger.allows(tool_name):
            self.log(f"SKIPPED {tool_name} (ledger denied)", "WARN")
            continue
        
        if not self.should_continue(tool_name, critical=False):
            self.log(f"SKIPPED {tool_name} (runtime budget)", "WARN")
            continue
        
        self.log(f"Running {tool_name}...", "INFO")
        try:
            stdout, stderr, returncode = self.run_command(
                tool_name,
                command,
                timeout=metadata.get('timeout', 300)
            )
            self.save_output(tool_name, stdout, stderr, returncode)
        except Exception as e:
            self.log(f"ERROR: {tool_name} failed: {e}", "ERROR")

def _run_subdomain_scan(self):
    """Subdomain execution path - minimal reconnaissance"""
    self.log("Executing SUBDOMAIN reconnaissance path", "INFO")
    
    executor = get_executor(self.profile, self.ledger)
    plan = executor.get_execution_plan()
    
    self.log(f"Execution plan: {len(plan)} tools (minimal)", "INFO")
    
    for tool_name, command, metadata in plan:
        if not self.ledger.allows(tool_name):
            self.log(f"SKIPPED {tool_name} (ledger denied)", "WARN")
            continue
        
        if not self.should_continue(tool_name, critical=False):
            self.log(f"SKIPPED {tool_name} (runtime budget)", "WARN")
            continue
        
        self.log(f"Running {tool_name}...", "INFO")
        try:
            stdout, stderr, returncode = self.run_command(
                tool_name,
                command,
                timeout=metadata.get('timeout', 300)
            )
            self.save_output(tool_name, stdout, stderr, returncode)
        except Exception as e:
            self.log(f"ERROR: {tool_name} failed: {e}", "ERROR")

def _run_ip_scan(self):
    """IP address execution path - network only"""
    self.log("Executing IP ADDRESS reconnaissance path", "INFO")
    
    executor = get_executor(self.profile, self.ledger)
    plan = executor.get_execution_plan()
    
    self.log(f"Execution plan: {len(plan)} tools (network only)", "INFO")
    
    for tool_name, command, metadata in plan:
        if not self.ledger.allows(tool_name):
            self.log(f"SKIPPED {tool_name} (ledger denied)", "WARN")
            continue
        
        if not self.should_continue(tool_name, critical=False):
            self.log(f"SKIPPED {tool_name} (runtime budget)", "WARN")
            continue
        
        self.log(f"Running {tool_name}...", "INFO")
        try:
            stdout, stderr, returncode = self.run_command(
                tool_name,
                command,
                timeout=metadata.get('timeout', 300)
            )
            self.save_output(tool_name, stdout, stderr, returncode)
        except Exception as e:
            self.log(f"ERROR: {tool_name} failed: {e}", "ERROR")
```

**Verify**:
- [ ] All three methods exist
- [ ] Each method checks ledger
- [ ] No cross-calling between methods

---

## PHASE 6: DELETE DEAD CODE (20 mins)

**Delete these methods entirely**:

- [ ] run_dns_subdomain_tools()
- [ ] run_subdomain_enumeration()
- [ ] run_network_tools()
- [ ] run_ssl_tls_tools()
- [ ] run_web_scanning_tools()
- [ ] run_vulnerability_scanners()
- [ ] run_directory_enumeration_tools()
- [ ] run_technology_detection_tools()
- [ ] run_nuclei_scanner()
- [ ] _analyze_tool_output()

**Delete old DNS variants**:
- [ ] host_any(), host_verbose(), dig_any(), dig_trace()
- [ ] nslookup_debug(), dnsenum_full()

**Delete old Nmap variants**:
- [ ] nmap_null_scan(), nmap_fin_scan(), nmap_xmas_scan(), nmap_ack_scan()
- [ ] All timing profile variants

**Delete TLS bloat**:
- [ ] All testssl_* variants
- [ ] All sslyze_* variants

**Delete Web bloat**:
- [ ] All duplicate gobuster/ffuf calls
- [ ] Recursive dirsearch calls

**Delete decision logic**:
- [ ] All self.context.should_run_*() calls
- [ ] All if "." in self.target checks
- [ ] All classifier.is_ip checks

**Verify**:
- [ ] No methods starting with run_ except _run_*_scan()
- [ ] No self.context references
- [ ] No self.classifier references

---

## PHASE 7: UPDATE run_gate_scan() (5 mins)

Location: Find run_gate_scan() method

**Replace with**:

```python
def run_gate_scan(self):
    """Gate scan - ARCHITECTURE DRIVEN"""
    
    print("\n" + "="*80)
    print("GATE SECURITY ASSESSMENT - ARCHITECTURE DRIVEN")
    print(f"Target: {self.target} ({self.profile.target_type.value})")
    print("="*80)
    
    try:
        path = ArchitectureIntegration.route_execution(self.profile, self.ledger)
        
        if path == "root":
            self._run_root_domain_scan()
        elif path == "subdomain":
            self._run_subdomain_scan()
        elif path == "ip":
            self._run_ip_scan()
    
    except ArchitectureViolation as e:
        self.log(f"Architecture violation: {e}", "ERROR")
        sys.exit(1)
    except KeyboardInterrupt:
        self.log("Gate scan interrupted by user", "WARN")
    finally:
        self._finalize_scan(gate_mode=True)
```

**Verify**:
- [ ] Old run_gate_dns(), run_gate_ssl(), run_gate_web(), run_gate_vuln() deleted
- [ ] Only routes to three paths

---

## PHASE 8: VALIDATION (5 mins)

Run these tests:

```bash
# Test 1: Root domain
python3 automation_scanner_v2.py example.com --skip-install --mode gate 2>&1 | head -20

# Check for errors
# Should show: "ROOT DOMAIN reconnaissance path"
# Should show: "Execution plan: X tools"
# Should NOT show: TargetClassifierBuilder, self.context, or decisions being made

# Test 2: Subdomain
python3 automation_scanner_v2.py api.example.com --skip-install --mode gate 2>&1 | head -20

# Check for:
# Should show: "SUBDOMAIN reconnaissance path"
# Should show: fewer tools than root

# Test 3: IP
python3 automation_scanner_v2.py 192.168.1.1 --skip-install --mode gate 2>&1 | head -20

# Check for:
# Should show: "IP ADDRESS reconnaissance path"
# Should NOT run DNS tools
```

**Verify**:
- [ ] All three modes work
- [ ] No TargetClassifierBuilder errors
- [ ] No ArchitectureViolation errors
- [ ] Correct path executed
- [ ] Tools counted correctly

---

## FINAL CHECKS

- [ ] No references to classifier
- [ ] No references to context
- [ ] All profile references use self.profile
- [ ] All ledger references use self.ledger
- [ ] Every tool checked against ledger
- [ ] Three paths completely separate
- [ ] ~500 lines of dead code deleted
- [ ] Tests pass

---

## ROLLBACK (if needed)

```bash
cp automation_scanner_v2_backup.py automation_scanner_v2.py
```

---

Total Time: ~1.5 hours
Risk: LOW
Reversibility: HIGH

DO NOT SKIP STEPS.
DO NOT REORDER.

Follow checklist exactly.
