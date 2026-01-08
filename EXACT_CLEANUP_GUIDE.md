# EXACT CLEANUP IMPLEMENTATION GUIDE
**Follow this EXACTLY - no deviations**

---

## PART 1: VERIFY CURRENT STATE

### What You Should See

**automation_scanner_v2.py imports (line ~25):**
```python
from target_classifier import TargetClassifierBuilder, ScanContext, TargetType, TargetScope
```

**automation_scanner_v2.py __init__ (line ~70):**
```python
self.classifier = TargetClassifierBuilder.from_string(target, scheme=protocol)
self.context = ScanContext(self.classifier)
self.target = self.classifier.host
```

**automation_scanner_v2.py run_full_scan (line ~1140):**
```python
def run_full_scan(self):
    # ... calls run_dns_subdomain_tools, run_network_tools, etc.
```

---

## PART 2: STEP-BY-STEP REPLACEMENT

### REPLACEMENT 1: Update Imports (Lines ~25-50)

#### FIND THIS:
```python
from tool_manager import ToolManager
from vulnerability_analyzer import VulnerabilityAnalyzer
from tool_custom_installer import CustomToolInstaller, custom_tool_menu
from target_classifier import TargetClassifierBuilder, ScanContext, TargetType, TargetScope

# Phase 2: Intelligence Layer
try:
    from finding_schema import Finding, FindingCollection, FindingType, Severity
    from dalfox_parser import DalfoxParser, DalfoxOutputProcessor
    from deduplicator import FindingDeduplicator, DeduplicationReport
    from risk_engine import RiskEngine, RiskScore
    PHASE_2_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] Phase 2 modules not available: {e}")
    PHASE_2_AVAILABLE = False

# Phase 3: Enhanced Features (Dedup, OWASP, Noise Filter, Custom Tools)
try:
    from comprehensive_deduplicator import ComprehensiveDeduplicator
    from owasp_mapper import OWASPMapper
    from noise_filter import NoiseFilter
    from custom_tool_manager import CustomToolManager
    PHASE_3_AVAILABLE = True
except ImportError as e:
    print(f"[WARN] Phase 3 modules not available: {e}")
    PHASE_3_AVAILABLE = False
```

#### REPLACE WITH:
```python
from tool_manager import ToolManager
from vulnerability_analyzer import VulnerabilityAnalyzer
from tool_custom_installer import CustomToolInstaller, custom_tool_menu

# NEW ARCHITECTURE IMPORTS
from architecture_integration import ArchitectureIntegration
from target_profile import TargetProfile, TargetType
from decision_ledger import DecisionLedger
from architecture_guards import ArchitectureViolation
from execution_paths import get_executor
```

---

### REPLACEMENT 2: Update __init__ Method (Lines ~70-118)

#### FIND THIS:
```python
def __init__(self, target, protocol='https', output_dir=None, skip_tool_check=False, mode='gate', enable_exploit_tools=False, runtime_budget=None):
    # Target Classification (IMMUTABLE)
    try:
        self.classifier = TargetClassifierBuilder.from_string(target, scheme=protocol)
        self.context = ScanContext(self.classifier)
    except ValueError as e:
        print(f"[ERROR] Invalid target: {e}")
        sys.exit(1)
    
    # Use classifier for all target info
    self.target = self.classifier.host
    self.protocol = self.classifier.scheme
    self.mode = mode
    self.enable_exploit_tools = enable_exploit_tools
    self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    self.start_time = datetime.now()
    self.correlation_id = self.timestamp
    self.reachability = None
    
    output_dir = output_dir or f"scan_results_{self.target}_{self.timestamp}"
    self.output_dir = Path(output_dir)
    self.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Tool management
    self.tool_manager = ToolManager()
    if not skip_tool_check:
        self.tool_manager.scan_all_tools()
    
    # Results tracking
    self.tool_results = {}
    self.tool_outputs = {}  # Store tool outputs for merging
    self.errors = []
    self.vulnerabilities = []
    self.analyzer = VulnerabilityAnalyzer()
    
    # Phase 2: Intelligence Layer
    self.findings_collection = None
    self.risk_score = None
    self.deduplication_report = None
    
    # Phase 3: Enhanced Features
    self.dns_records = {}           # For DNS dedup (req 11)
    self.discovered_subdomains = []  # For subdomain dedup & resolution (req 13, 15)
    self.discovered_endpoints = []   # For endpoint dedup (req 36)
    self.all_findings = []           # For cross-tool finding dedup (req 56)
    
    # Tool execution tracking
    self.total_tools_planned = 0  # Will be calculated at scan start
    self.tools_executed_so_far = 0  # Global counter across all categories
    
    # Runtime budget (req 55)
    self.runtime_budget = runtime_budget or self.RUNTIME_BUDGET
    self.phase_start_time = None
    
    self.log(f"Target Classification: {self.classifier}", "INFO")
    self.log(f"Target Type: {self.classifier.target_type.value}", "INFO")
    self.log(f"Scope: {self.classifier.scope.value}", "INFO")
    self.log(f"Runtime Budget: {self.runtime_budget}s ({self.runtime_budget/60:.1f}m)", "INFO")
    
    self.log(f"Output directory: {self.output_dir}", "INFO")
    self.log(f"Correlation ID: {self.correlation_id}", "INFO")
```

#### REPLACE WITH:
```python
def __init__(self, target, protocol='https', output_dir=None, skip_tool_check=False, mode='gate', enable_exploit_tools=False, runtime_budget=None):
    # Create immutable profile using new architecture
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
    
    # Extract from immutable profile
    self.target = self.profile.host
    self.protocol = self.profile.scheme
    self.mode = mode
    self.enable_exploit_tools = enable_exploit_tools
    self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    self.start_time = datetime.now()
    self.correlation_id = self.timestamp
    self.reachability = None
    
    output_dir = output_dir or f"scan_results_{self.target}_{self.timestamp}"
    self.output_dir = Path(output_dir)
    self.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Tool management
    self.tool_manager = ToolManager()
    if not skip_tool_check:
        self.tool_manager.scan_all_tools()
    
    # Results tracking
    self.tool_results = {}
    self.errors = []
    self.vulnerabilities = []
    self.analyzer = VulnerabilityAnalyzer()
    
    # Runtime budget
    self.runtime_budget = runtime_budget or self.RUNTIME_BUDGET
    self.phase_start_time = None
    
    self.log(f"Target Profile: {self.profile.host}", "INFO")
    self.log(f"Target Type: {self.profile.target_type.value}", "INFO")
    self.log(f"Runtime Budget: {self.runtime_budget}s ({self.runtime_budget/60:.1f}m)", "INFO")
    self.log(f"Output directory: {self.output_dir}", "INFO")
    self.log(f"Correlation ID: {self.correlation_id}", "INFO")
```

---

### REPLACEMENT 3: Update run_full_scan() (Line ~1140)

#### FIND THIS:
```python
def run_full_scan(self):
    """Execute complete security assessment (full mode)"""
    
    # Estimate total tools
    self.total_tools_planned = self._estimate_total_tools()
    
    print("\n" + "="*80)
    print("INTELLIGENT SECURITY SCANNER - GATED EXECUTION")
    print(f"Target: {self.target}")
    print(f"Classification: {self.classifier.target_type.value.upper()}")
    print(f"Scope: {self.classifier.scope.value}")
    print(f"Estimated Tools: ~{self.total_tools_planned} (vs old 325+)")
    print(f"Start Time: {self.start_time.isoformat()}")
    print("="*80)
    
    try:
        # Phase 1: Early detection (tech stack, params, reflection) - req 52
        if self.should_continue("Early Detection"):
            self.run_early_detection()
        
        # Phase 2: Infrastructure scanning (gated by target type) - req 52
        try:
            if self.should_continue("DNS/Subdomain", critical=False):
                self.run_dns_subdomain_tools()
                self.run_subdomain_enumeration()
                # Resolve discovered subdomains (req 15)
                if self.discovered_subdomains:
                    self.resolve_subdomains(self.discovered_subdomains)
            
            if self.should_continue("Network", critical=False):
                self.run_network_tools()
            
            if self.should_continue("SSL/TLS", critical=False):
                self.run_ssl_tls_tools()
        except RuntimeError as e:
            self.log(f"Phase 2 fail-fast: {e}", "ERROR")
        
        # Phase 3: Web/application scanning (gated by detection) - req 52
        try:
            if self.should_continue("Web Scanning", critical=False):
                self.run_web_scanning_tools()
                self.run_directory_enumeration_tools()
                self.run_technology_detection_tools()
        except RuntimeError as e:
            self.log(f"Phase 3 fail-fast: {e}", "ERROR")
        
        # Phase 4: Vulnerability scanning (gated by detection) - req 52
        try:
            if self.should_continue("Vulnerability", critical=False):
                self.run_nuclei_scanner()
                self.run_vulnerability_scanners()
        except RuntimeError as e:
            self.log(f"Phase 4 fail-fast: {e}", "ERROR")
        
    except KeyboardInterrupt:
        self.log("Scan interrupted by user", "WARN")
    except Exception as e:
        self.log(f"Fatal error: {str(e)}", "ERROR")
    finally:
        self._finalize_scan(gate_mode=False)
```

#### REPLACE WITH:
```python
def run_full_scan(self):
    """Execute complete security assessment (full mode)"""
    
    print("\n" + "="*80)
    print("INTELLIGENT SECURITY SCANNER - FULL EXECUTION")
    print(f"Target: {self.target}")
    print(f"Target Type: {self.profile.target_type.value.upper()}")
    print(f"Start Time: {self.start_time.isoformat()}")
    print("="*80)
    
    try:
        # Route to correct execution path
        path = ArchitectureIntegration.route_execution(self.profile, self.ledger)
        
        if path == "root":
            self.log("Executing ROOT DOMAIN reconnaissance path", "INFO")
            self._run_root_domain_scan()
        elif path == "subdomain":
            self.log("Executing SUBDOMAIN reconnaissance path", "INFO")
            self._run_subdomain_scan()
        elif path == "ip":
            self.log("Executing IP ADDRESS reconnaissance path", "INFO")
            self._run_ip_scan()
        else:
            raise ArchitectureViolation(f"Unknown execution path: {path}")
    
    except KeyboardInterrupt:
        self.log("Scan interrupted by user", "WARN")
    except ArchitectureViolation as e:
        self.log(f"Architecture violation: {e}", "ERROR")
        sys.exit(1)
    except Exception as e:
        self.log(f"Fatal error: {str(e)}", "ERROR")
    finally:
        self._finalize_scan(gate_mode=False)
```

---

### REPLACEMENT 4: Add Three Execution Methods

#### ADD THIS (after run_gate_scan method, around line 1250):

```python
def _run_root_domain_scan(self):
    """Execute root domain reconnaissance using executor and ledger"""
    try:
        executor = get_executor(self.profile, self.ledger)
        plan = executor.get_execution_plan()
        
        self.log(f"Executing {len(plan)} tools for root domain", "INFO")
        
        for tool_name, command, metadata in plan:
            if not self.should_continue(f"{tool_name}", critical=False):
                break
            
            # Check ledger before executing
            if not self.ledger.allows(tool_name):
                self.log(f"[SKIP] {tool_name} - denied by ledger ({self.ledger.get_reason(tool_name)})", "WARN")
                continue
            
            timeout = metadata.get('timeout', 300)
            self._execute_tool(tool_name, command, timeout)
    
    except Exception as e:
        self.log(f"Error in root domain scan: {e}", "ERROR")

def _run_subdomain_scan(self):
    """Execute subdomain reconnaissance using executor and ledger"""
    try:
        executor = get_executor(self.profile, self.ledger)
        plan = executor.get_execution_plan()
        
        self.log(f"Executing {len(plan)} tools for subdomain", "INFO")
        
        for tool_name, command, metadata in plan:
            if not self.should_continue(f"{tool_name}", critical=False):
                break
            
            # Check ledger before executing
            if not self.ledger.allows(tool_name):
                self.log(f"[SKIP] {tool_name} - denied by ledger ({self.ledger.get_reason(tool_name)})", "WARN")
                continue
            
            timeout = metadata.get('timeout', 300)
            self._execute_tool(tool_name, command, timeout)
    
    except Exception as e:
        self.log(f"Error in subdomain scan: {e}", "ERROR")

def _run_ip_scan(self):
    """Execute IP address reconnaissance using executor and ledger"""
    try:
        executor = get_executor(self.profile, self.ledger)
        plan = executor.get_execution_plan()
        
        self.log(f"Executing {len(plan)} tools for IP address", "INFO")
        
        for tool_name, command, metadata in plan:
            if not self.should_continue(f"{tool_name}", critical=False):
                break
            
            # Check ledger before executing
            if not self.ledger.allows(tool_name):
                self.log(f"[SKIP] {tool_name} - denied by ledger ({self.ledger.get_reason(tool_name)})", "WARN")
                continue
            
            timeout = metadata.get('timeout', 300)
            self._execute_tool(tool_name, command, timeout)
    
    except Exception as e:
        self.log(f"Error in IP scan: {e}", "ERROR")

def _execute_tool(self, tool_name: str, command: str, timeout: int):
    """Execute a single tool with logging"""
    self.log(f"[RUN] {tool_name}", "INFO")
    stdout, stderr, returncode = self.run_command(tool_name, command, timeout)
    
    if returncode == 0:
        self.log(f"[OK] {tool_name}", "INFO")
    else:
        self.log(f"[FAIL] {tool_name} (code: {returncode})", "WARN")
    
    self.tool_results[tool_name] = {
        'returncode': returncode,
        'stdout': stdout,
        'stderr': stderr,
        'timestamp': datetime.now().isoformat()
    }
```

---

## PART 3: DELETE DEAD CODE

### Methods to DELETE from automation_scanner_v2.py

Delete these ENTIRE methods:

```python
# DELETE: run_dns_subdomain_tools()          # Line ~632
# DELETE: run_subdomain_enumeration()        # Line ~660
# DELETE: run_network_tools()                # Line ~733
# DELETE: run_ssl_tls_tools()                # Line ~770
# DELETE: run_web_scanning_tools()           # Line ~825
# DELETE: run_directory_enumeration_tools()  # Line ~870
# DELETE: run_technology_detection_tools()   # Line ~923
# DELETE: run_nuclei_scanner()               # Line ~955
# DELETE: run_vulnerability_scanners()       # Line ~1002
# DELETE: _analyze_tool_output()             # Line ~427
# DELETE: _append_to_tool_output()           # Line ~329
# DELETE: _handle_missing_tool()             # Line ~394
# DELETE: _estimate_total_tools()            # Line ~1094
```

Search for each and delete the entire method definition.

---

### Lines to DELETE from automation_scanner_v2.py

#### DELETE unused data initialization (from __init__):
```python
self.tool_outputs = {}  # DELETE
self.dns_records = {}  # DELETE
self.discovered_subdomains = []  # DELETE
self.discovered_endpoints = []  # DELETE
self.all_findings = []  # DELETE
self.total_tools_planned = 0  # DELETE
self.tools_executed_so_far = 0  # DELETE
self.findings_collection = None  # DELETE
self.risk_score = None  # DELETE
self.deduplication_report = None  # DELETE
```

#### DELETE method calls (from run_gate_scan or wherever they appear):
```python
# DELETE these calls:
self.deduplicate_all_findings()
self.apply_noise_filter()
self.map_to_owasp()
self.resolve_subdomains(...)
self._process_phase_2_findings()
self._parse_tool_outputs()
self._save_phase_2_reports()
```

---

## PART 4: DELETE DUPLICATE FILE

### Delete target_classifier.py

```bash
# Delete the file
rm target_classifier.py

# Or on Windows:
# del target_classifier.py
```

This file is now completely replaced by target_profile.py.

---

## PART 5: VALIDATION

### Test 1: Imports Work
```bash
python3 -c "import automation_scanner_v2; print('✓ Imports OK')"
```

Should show:
```
✓ Imports OK
```

### Test 2: Scanner Initializes
```bash
python3 -c "
from automation_scanner_v2 import ComprehensiveSecurityScanner
s = ComprehensiveSecurityScanner('example.com', protocol='https', skip_tool_check=True)
print(f'✓ Scanner initialized for {s.target}')
print(f'✓ Target type: {s.profile.target_type.value}')
"
```

Should show:
```
✓ Scanner initialized for example.com
✓ Target type: root_domain
```

### Test 3: Root Domain Detection
```bash
python3 -c "
from automation_scanner_v2 import ComprehensiveSecurityScanner
s = ComprehensiveSecurityScanner('example.com', skip_tool_check=True)
print(f'✓ {s.target} is {s.profile.target_type.value}')
"
```

### Test 4: Subdomain Detection
```bash
python3 -c "
from automation_scanner_v2 import ComprehensiveSecurityScanner
s = ComprehensiveSecurityScanner('api.example.com', skip_tool_check=True)
print(f'✓ {s.target} is {s.profile.target_type.value}')
print(f'✓ Base domain: {s.profile.base_domain}')
"
```

### Test 5: IP Detection
```bash
python3 -c "
from automation_scanner_v2 import ComprehensiveSecurityScanner
s = ComprehensiveSecurityScanner('8.8.8.8', skip_tool_check=True)
print(f'✓ {s.target} is {s.profile.target_type.value}')
print(f'✓ Resolved IPs: {s.profile.resolved_ips}')
"
```

### Test 6: Ledger Created
```bash
python3 -c "
from automation_scanner_v2 import ComprehensiveSecurityScanner
s = ComprehensiveSecurityScanner('example.com', skip_tool_check=True)
print(f'✓ Ledger built: {s.ledger is not None}')
allowed_tools = [t for t, d in s.ledger.decisions.items() if d.decision.value == 'allow']
print(f'✓ Tools allowed: {len(allowed_tools)}')
"
```

### Test 7: Quick Scan
```bash
python3 automation_scanner_v2.py example.com --mode gate --skip-install 2>&1 | head -50
```

Should show:
```
[...] [INFO] Target Profile: example.com
[...] [INFO] Target Type: root_domain
[...] [INFO] Executing ROOT DOMAIN reconnaissance path
[...] [RUN] dig_a
```

---

## SUMMARY OF CHANGES

| Step | File | Change | Impact |
|------|------|--------|--------|
| 1 | automation_scanner_v2.py | Update imports | -30 lines |
| 2 | automation_scanner_v2.py | Replace __init__ | -40 lines |
| 3 | automation_scanner_v2.py | Replace run_full_scan() | -50 lines |
| 4 | automation_scanner_v2.py | Add 4 methods | +150 lines |
| 5 | automation_scanner_v2.py | Delete 13 methods | -400 lines |
| 6 | automation_scanner_v2.py | Delete unused data | -20 lines |
| 7 | --- | Delete target_classifier.py | -350 lines |
| **TOTAL** | --- | --- | **-740 lines** |

---

## ROLLBACK INSTRUCTIONS (if needed)

```bash
# Restore from backup
cp automation_scanner_v2.py.backup automation_scanner_v2.py
cp target_classifier.py.backup target_classifier.py

# Verify
python3 -c "import automation_scanner_v2; print('✓ Restored')"
```

---

## VERIFICATION CHECKLIST

After all changes:

- [ ] automation_scanner_v2.py line count: ~700 (was 1,353)
- [ ] target_classifier.py: DELETED
- [ ] All imports from new architecture
- [ ] __init__ uses ArchitectureIntegration
- [ ] run_full_scan() routes to correct path
- [ ] _run_root_domain_scan() exists and works
- [ ] _run_subdomain_scan() exists and works
- [ ] _run_ip_scan() exists and works
- [ ] _execute_tool() exists and checks ledger
- [ ] All 13 orphaned methods DELETED
- [ ] No references to ScanContext remain
- [ ] No references to TargetClassifier remain
- [ ] Imports work: `python3 -c "import automation_scanner_v2"`
- [ ] Scanner initializes: `ComprehensiveSecurityScanner('example.com')`
- [ ] Root domain test PASSES
- [ ] Subdomain test PASSES
- [ ] IP test PASSES

✓ When all checked, cleanup is COMPLETE.
