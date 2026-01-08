# EXACT METHODS TO DELETE FROM automation_scanner_v2.py

**Copy method names below, search for each in editor, delete entire method definition**

---

## METHOD 1: run_dns_subdomain_tools

**Search for:** `def run_dns_subdomain_tools`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~632-660 (~30 lines)  
**Why:** Orphaned - never called, replaced by ExecutionPaths

---

## METHOD 2: run_subdomain_enumeration

**Search for:** `def run_subdomain_enumeration`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~660-730 (~70 lines)  
**Why:** Orphaned - never called, replaced by ExecutionPaths

---

## METHOD 3: run_network_tools

**Search for:** `def run_network_tools`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~733-770 (~40 lines)  
**Why:** Orphaned - never called, replaced by ExecutionPaths

---

## METHOD 4: run_ssl_tls_tools

**Search for:** `def run_ssl_tls_tools`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~770-825 (~55 lines)  
**Why:** Orphaned - never called, replaced by ExecutionPaths

---

## METHOD 5: run_web_scanning_tools

**Search for:** `def run_web_scanning_tools`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~825-870 (~45 lines)  
**Why:** Orphaned - never called, replaced by ExecutionPaths

---

## METHOD 6: run_directory_enumeration_tools

**Search for:** `def run_directory_enumeration_tools`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~870-925 (~55 lines)  
**Why:** Orphaned - never called, replaced by ExecutionPaths

---

## METHOD 7: run_technology_detection_tools

**Search for:** `def run_technology_detection_tools`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~925-960 (~35 lines)  
**Why:** Orphaned - never called, replaced by ExecutionPaths

---

## METHOD 8: run_nuclei_scanner

**Search for:** `def run_nuclei_scanner`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~960-1005 (~45 lines)  
**Why:** Orphaned - never called, replaced by ExecutionPaths

---

## METHOD 9: run_vulnerability_scanners

**Search for:** `def run_vulnerability_scanners`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~1005-1095 (~90 lines)  
**Why:** Orphaned - never called, replaced by ExecutionPaths

---

## METHOD 10: _analyze_tool_output

**Search for:** `def _analyze_tool_output`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~427-450 (~25 lines)  
**Why:** Orphaned - never called, no tools populating data structures

---

## METHOD 11: _append_to_tool_output

**Search for:** `def _append_to_tool_output`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~329-335 (~8 lines)  
**Why:** Orphaned - never called

---

## METHOD 12: _handle_missing_tool

**Search for:** `def _handle_missing_tool`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~394-428 (~35 lines)  
**Why:** Orphaned - never called

---

## METHOD 13: _estimate_total_tools

**Search for:** `def _estimate_total_tools`  
**Delete:** Entire method from `def` to next `def`  
**Lines affected:** ~1094-1140 (~46 lines)  
**Why:** Incomplete logic, not called consistently, broken calculation

---

## DATA TO DELETE FROM __init__

In the `__init__` method, find and delete these lines:

```python
# DELETE THESE LINES:
self.tool_outputs = {}                          # Store tool outputs for merging
self.dns_records = {}                           # For DNS dedup (req 11)
self.discovered_subdomains = []                 # For subdomain dedup & resolution
self.discovered_endpoints = []                  # For endpoint dedup (req 36)
self.all_findings = []                          # For cross-tool finding dedup (req 56)
self.total_tools_planned = 0                    # Will be calculated at scan start
self.tools_executed_so_far = 0                  # Global counter across all categories
self.findings_collection = None                 # Phase 2: Intelligence Layer
self.risk_score = None                          # Phase 2
self.deduplication_report = None                # Phase 2
```

---

## IMPORTS TO DELETE

At the top of file (lines ~25-50), delete:

```python
# DELETE ENTIRE BLOCK:
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

---

## METHOD CALLS TO REMOVE

Find and delete these method calls from run_gate_scan() or anywhere they appear:

```python
# DELETE THESE CALLS:
self.deduplicate_all_findings()
self.apply_noise_filter()
self.map_to_owasp()
self.resolve_subdomains(self.discovered_subdomains)  # if self.discovered_subdomains
self._process_phase_2_findings()
self._parse_tool_outputs()
self._save_phase_2_reports()
```

---

## VALIDATION: Confirm Deletion

After deleting all the above:

### Test 1: File opens without errors
```bash
python3 -c "import automation_scanner_v2; print('✓ File OK')"
```

### Test 2: Class instantiates
```bash
python3 << 'EOF'
from automation_scanner_v2 import ComprehensiveSecurityScanner
s = ComprehensiveSecurityScanner('example.com', skip_tool_check=True)
print('✓ Scanner initialized')
EOF
```

### Test 3: Verify methods don't exist
```bash
python3 << 'EOF'
from automation_scanner_v2 import ComprehensiveSecurityScanner
s = ComprehensiveSecurityScanner('example.com', skip_tool_check=True)

# These should raise AttributeError:
methods_deleted = [
    'run_dns_subdomain_tools',
    'run_subdomain_enumeration',
    'run_network_tools',
    'run_ssl_tls_tools',
    'run_web_scanning_tools',
    'run_directory_enumeration_tools',
    'run_nuclei_scanner',
    'run_vulnerability_scanners',
    '_analyze_tool_output',
]

for method in methods_deleted:
    try:
        getattr(s, method)
        print(f'✗ {method} still exists!')
    except AttributeError:
        print(f'✓ {method} deleted')
EOF
```

### Test 4: Verify new methods exist
```bash
python3 << 'EOF'
from automation_scanner_v2 import ComprehensiveSecurityScanner
s = ComprehensiveSecurityScanner('example.com', skip_tool_check=True)

# These should work:
methods_added = [
    '_run_root_domain_scan',
    '_run_subdomain_scan',
    '_run_ip_scan',
    '_execute_tool',
]

for method in methods_added:
    try:
        getattr(s, method)
        print(f'✓ {method} exists')
    except AttributeError:
        print(f'✗ {method} missing!')
EOF
```

---

## LINE COUNT VERIFICATION

### Before Deletions
```bash
wc -l automation_scanner_v2.py
# Should show: ~1353 lines
```

### After Deletions (before additions)
```bash
wc -l automation_scanner_v2.py
# Should show: ~800-900 lines
```

### After All Changes (deletions + additions)
```bash
wc -l automation_scanner_v2.py
# Should show: ~1000-1100 lines
```

---

## QUICK DELETE SCRIPT (Optional)

If you want to use a script to verify what needs deleting:

```python
# analyze_methods.py
import ast

with open('automation_scanner_v2.py', 'r') as f:
    tree = ast.parse(f.read())

methods_to_delete = [
    'run_dns_subdomain_tools',
    'run_subdomain_enumeration',
    'run_network_tools',
    'run_ssl_tls_tools',
    'run_web_scanning_tools',
    'run_directory_enumeration_tools',
    'run_technology_detection_tools',
    'run_nuclei_scanner',
    'run_vulnerability_scanners',
    '_analyze_tool_output',
    '_append_to_tool_output',
    '_handle_missing_tool',
    '_estimate_total_tools',
]

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        if node.name in methods_to_delete:
            print(f"DELETE: {node.name} (line {node.lineno})")
```

Run with:
```bash
python3 analyze_methods.py
```

---

## SUMMARY TABLE

| # | Method | Location | Size | Reason |
|---|--------|----------|------|--------|
| 1 | run_dns_subdomain_tools | ~632 | 30 | Orphaned |
| 2 | run_subdomain_enumeration | ~660 | 70 | Orphaned |
| 3 | run_network_tools | ~733 | 40 | Orphaned |
| 4 | run_ssl_tls_tools | ~770 | 55 | Orphaned |
| 5 | run_web_scanning_tools | ~825 | 45 | Orphaned |
| 6 | run_directory_enumeration_tools | ~870 | 55 | Orphaned |
| 7 | run_nuclei_scanner | ~960 | 45 | Orphaned |
| 8 | run_vulnerability_scanners | ~1005 | 90 | Orphaned |
| 9 | _analyze_tool_output | ~427 | 25 | Orphaned |
| 10 | _append_to_tool_output | ~329 | 8 | Orphaned |
| 11 | _handle_missing_tool | ~394 | 35 | Orphaned |
| 12 | _estimate_total_tools | ~1094 | 46 | Broken logic |
| 13 | run_technology_detection_tools | ~923 | 35 | Orphaned |
| **TOTAL** | | | **~580** | **LINES** |

---

## CONFIRMATION CHECKLIST

- [ ] Backed up automation_scanner_v2.py
- [ ] Deleted run_dns_subdomain_tools()
- [ ] Deleted run_subdomain_enumeration()
- [ ] Deleted run_network_tools()
- [ ] Deleted run_ssl_tls_tools()
- [ ] Deleted run_web_scanning_tools()
- [ ] Deleted run_directory_enumeration_tools()
- [ ] Deleted run_technology_detection_tools()
- [ ] Deleted run_nuclei_scanner()
- [ ] Deleted run_vulnerability_scanners()
- [ ] Deleted _analyze_tool_output()
- [ ] Deleted _append_to_tool_output()
- [ ] Deleted _handle_missing_tool()
- [ ] Deleted _estimate_total_tools()
- [ ] Deleted unused data from __init__
- [ ] Deleted unused imports
- [ ] File opens: `python3 -c "import automation_scanner_v2"`
- [ ] No AttributeErrors for methods called
- [ ] Line count reduced from 1,353 to ~1,000-1,100

✓ When all checked: Ready for new additions
