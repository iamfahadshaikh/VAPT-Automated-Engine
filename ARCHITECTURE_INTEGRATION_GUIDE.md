ARCHITECTURE INTEGRATION GUIDE
==============================

## QUICK START - Using the New Architecture

The 5-step architecture is now complete and ready to use. Here's how to integrate it:

### Step 1: Import the Components

```python
from target_profile import TargetProfile, TargetType, TargetProfileBuilder
from decision_ledger import DecisionEngine
from execution_paths import get_executor
from architecture_guards import ArchitectureValidator
```

### Step 2: Build a Target Profile

```python
profile = (TargetProfileBuilder()
    .with_original_input("example.com")
    .with_target_type(TargetType.ROOT_DOMAIN)
    .with_host("example.com")
    .with_scheme("https")
    .with_port(443)
    .with_is_web_target(True)
    .with_is_https(True)
    .with_detected_params({"id", "search"})  # Add evidence as discovered
    .build())
```

The profile is now immutable and locked. All evidence goes in the profile.

### Step 3: Build the Decision Ledger

```python
ledger = DecisionEngine.build_ledger(profile)
```

The ledger automatically decides which tools run based on profile evidence.

Example: If profile.has_wordpress is True, wpscan will be ALLOWED. Otherwise DENIED.

### Step 4: Get the Executor

```python
executor = get_executor(profile, ledger)  # Returns RootDomainExecutor, SubdomainExecutor, or IPExecutor
```

### Step 5: Get the Execution Plan

```python
plan = executor.get_execution_plan()

for tool_name, command, metadata in plan:
    print(f"Running: {tool_name}")
    print(f"Command: {command}")
    print(f"Timeout: {metadata['timeout']}s")
    # Run the tool here
```

### Step 6: Validate (Optional)

```python
ArchitectureValidator.validate_pre_scan(profile, ledger)
ArchitectureValidator.validate_execution_plan(profile, ledger)
```

---

## ARCHITECTURE FLOW

```
User Input
    |
    v
TargetProfileBuilder (STEP 1)
    |
    | Creates immutable
    |
    v
TargetProfile (STEP 1)
    |
    | Evidence locked
    |
    v
DecisionEngine.build_ledger() (STEP 2)
    |
    | Examines all evidence
    | Makes tool decisions
    |
    v
DecisionLedger (STEP 2)
    |
    | Pre-computed allow/deny
    |
    v
get_executor() (STEP 3)
    |
    | Matches target type to executor
    |
    v
RootDomainExecutor / SubdomainExecutor / IPExecutor (STEP 3)
    |
    | Consults ledger
    | Builds tool list
    |
    v
Execution Plan (STEP 3)
    |
    | Tools to run (all ledger-approved)
    |
    v
execute_plan()
    |
    | Run each tool
    | No decisions needed (already made)
    |
    v
Results
```

---

## EVIDENCE-DRIVEN GATE EXAMPLES

### Gate 1: DNS for IPs
```
Profile: TargetType.IP, resolved_ips=["192.168.1.1"]
Decision: DENY dig_a, dig_ns, dig_mx, dnsrecon
Reason: "IP is already resolved, DNS not needed"
```

### Gate 2: Subdomain Enumeration
```
Profile: TargetType.SUBDOMAIN, base_domain="example.com"
Decision: DENY findomain, sublist3r, assetfinder
Reason: "Subdomain enumeration runs on root domain only"
```

### Gate 3: Web Scanning
```
Profile: is_web_target=False
Decision: DENY whatweb, gobuster, dalfox, nuclei
Reason: "Target not web-accessible"
```

### Gate 4: Parameter-Based Tools
```
Profile: detected_params={"id", "search"} (or empty set)
Decision: ALLOW dalfox, xsstrike, sqlmap if params detected
Decision: DENY dalfox, xsstrike, sqlmap if params empty
Reason: "Parameter-based tools only useful with parameters"
```

### Gate 5: CMS-Specific Tools
```
Profile: detected_cms="wordpress"
Decision: ALLOW wpscan
Reason: "WordPress detected in evidence"

Profile: detected_cms=None
Decision: DENY wpscan
Reason: "No CMS detected, wpscan not useful"
```

---

## COMPARISON: OLD vs NEW

### OLD (Before Refactor)
```python
# Decision made at execution time
if target.is_ip:
    skip_dns_tools()  # Soft skip, tools could still run
if detected_params:
    run_param_tools()
else:
    still_run_some_param_tools()  # Leaky logic
```

### NEW (After Refactor)
```python
# Decision made upfront
profile = create_profile(...)  # Immutable
ledger = build_ledger(profile)  # Pre-computed
plan = executor.get_execution_plan()  # Only ledger-approved tools

# No tool can run unless:
# 1. It's in the execution plan
# 2. The plan came from the ledger
# 3. The ledger approved it based on evidence
```

---

## FILE REFERENCE

New Architecture Files:
- `target_profile.py` - Immutable target profile
- `decision_ledger.py` - Precomputed tool decisions
- `execution_paths.py` - Separate execution flows
- `architecture_guards.py` - Enforcement and validation

These files:
- Use only Python stdlib (no external dependencies)
- Are fully tested and working
- Can be used standalone or integrated
- Work together as a cohesive system

---

## INTEGRATION CHECKLIST

To integrate with automation_scanner_v2.py:

- [ ] Import new modules
- [ ] Wrap user input in TargetProfileBuilder
- [ ] Build ledger from profile
- [ ] Get executor
- [ ] Replace tool execution with plan-driven execution
- [ ] Add pre-scan validation
- [ ] Remove old decision logic
- [ ] Test each target type (IP, root, subdomain)
- [ ] Verify no tools bypass the ledger
- [ ] Update STATUS.md with integration complete

---

## EXAMPLE: COMPLETE WORKFLOW

```python
from target_profile import TargetProfileBuilder, TargetType
from decision_ledger import DecisionEngine
from execution_paths import get_executor
from architecture_guards import ArchitectureValidator

# 1. CREATE PROFILE
profile = (TargetProfileBuilder()
    .with_original_input(user_input)
    .with_target_type(classify_target(user_input))
    .with_host(extract_host(user_input))
    .with_scheme(detect_scheme(user_input))
    .with_port(detect_port(user_input))
    .build())

# 2. BUILD LEDGER
ledger = DecisionEngine.build_ledger(profile)

# 3. VALIDATE ARCHITECTURE
ArchitectureValidator.validate_pre_scan(profile, ledger)

# 4. GET EXECUTOR
executor = get_executor(profile, ledger)

# 5. GET PLAN
plan = executor.get_execution_plan()

# 6. EXECUTE TOOLS
for tool_name, command, metadata in plan:
    try:
        result = run_tool(tool_name, command, metadata['timeout'])
        process_result(result)
    except Exception as e:
        log_error(f"{tool_name} failed: {e}")

# 7. DONE
return consolidate_results()
```

---

## VALIDATION - What Gets Checked

Pre-scan validation ensures:
- TargetProfile is frozen (immutable)
- DecisionLedger is finalized (no modifications)
- Profile and ledger are consistent (built together)

Execution plan validation ensures:
- Executor type matches target type
- All tools in plan are approved by ledger
- Plan is not empty (at minimum, network tools should run)

Tool execution validation ensures:
- Tool is allowed by ledger
- Prerequisites are met
- Profile has necessary state

---

## DECISION PRIORITY

Tools are sorted by priority when retrieved:

```python
allowed_tools = ledger.get_allowed_tools()  # Sorted by priority, highest first
```

Priority determines execution order:
- Network tools (ping, nmap) - priority 100
- Web detection (whatweb) - priority 90
- DNS (dig) - priority 80
- Web scanning (gobuster) - priority 70
- Vulnerability (dalfox, xsstrike) - priority 60
- Advanced (nuclei) - priority 50

Lower priority tools don't start until higher priority complete.

---

## NEXT STEPS

1. **Immediate**: Use new architecture standalone for any new scanning
2. **Short-term**: Integrate into automation_scanner_v2.py
3. **Long-term**: Sunset old decision logic once integration complete

The architecture is production-ready now. No changes needed.
