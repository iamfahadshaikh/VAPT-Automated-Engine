# Project Architecture: Security Tool Orchestrator v3.0

**Current Status**: Phase 1 Complete (Tool Orchestration) | Phase 2 Planned (Intelligence Layer)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Execution Pipeline](#execution-pipeline)
5. [Tool Ecosystem](#tool-ecosystem)
6. [File Structure](#file-structure)
7. [Current Limitations](#current-limitations)
8. [Future Architecture (Phase 2)](#future-architecture-phase-2)

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER ENTRY POINT                         │
│  python3 automation_scanner_v2.py <target> [options]        │
└────────────────────────────┬────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
         ┌────▼────┐                  ┌────▼────┐
         │  GATE   │                  │   FULL  │
         │  MODE   │                  │  MODE   │
         │ 5-10min │                  │ 2-8hrs  │
         └────┬────┘                  └────┬────┘
              │                             │
              └──────────────┬──────────────┘
                             │
           ┌─────────────────▼─────────────────┐
           │  COMPREHENSIVE SECURITY SCANNER   │
           │      Tool Orchestration Engine    │
           └──────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐        ┌────▼─────┐        ┌────▼─────┐
   │Tool      │        │Execution │        │Output    │
   │Detection │        │Engine    │        │Manager   │
   │& Install │        │          │        │          │
   └──────────┘        └──────────┘        └──────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼──────┐       ┌────▼──────┐       ┌────▼──────┐
   │32 Tools   │       │Raw Output │       │Execution  │
   │Organized │       │Files      │       │Logs       │
   │by         │       │(325+)     │       │(JSON)     │
   │Category   │       │           │       │           │
   └───────────┘       └───────────┘       └───────────┘
```

---

## Component Architecture

### Layer 1: Entry Point
**File**: `automation_scanner_v2.py` (Main class: `ComprehensiveSecurityScanner`)

**Responsibilities**:
- Parse command-line arguments
- Initialize scanner with target/protocol/mode
- Route to gate or full scan
- Orchestrate high-level execution flow

**Key Methods**:
```python
__init__()                          # Initialize scanner
run_gate_scan()                     # 5-10 min quick assessment
run_full_scan()                     # Comprehensive 2-8 hour scan
_finalize_scan()                    # Cleanup & reporting
```

---

### Layer 2: Tool Management
**File**: `tool_manager.py` (Class: `ToolManager`)

**Responsibilities**:
- Detect installed tools on system
- Install missing tools (apt, pip, brew, go)
- Provide tool status and availability
- Manage tool metadata

**Key Methods**:
```python
scan_all_tools()                    # Detect all 32 tools
check_tool_installed(tool_name)     # Boolean check
install_tool(tool_name)             # Install specific tool
get_tool_status()                   # Report on all tools
```

**Manages**: 32 tools across 8 categories
- DNS/Subdomain: assetfinder, dnsrecon, dig, host, dnsenum, nslookup, findomain, theharvester
- Network: nmap, ping, traceroute, whois
- SSL/TLS: testssl.sh, sslyze, sslscan, openssl
- Web: wpscan, wapiti, whatweb, ffuf, golismero
- Directory: gobuster, dirsearch
- Tech: Wappalyzer, retire
- Templates: nuclei
- Vulnerabilities: xsstrike, dalfox, xsser, ssrfmap, nosqlmap, dotdotpwn, sqlmap, commix

---

### Layer 3: Execution Engine
**File**: `automation_scanner_v2.py` (Methods: `_execute_tools()`, `run_command()`)

**Responsibilities**:
- Execute commands sequentially
- Capture stdout/stderr
- Track execution metadata (timestamp, correlation ID)
- Handle errors gracefully (continue on failure)
- Save individual output files

**Key Methods**:
```python
run_command(tool_name, command, timeout)      # Execute single command
_execute_tools(tools, category)               # Run batch of tools
```

**Features**:
- ✅ No timeout constraints (all optional)
- ✅ Automatic stdout/stderr capture
- ✅ Per-command output file (e.g., `dig_a.txt`, `nmap_syn.txt`)
- ✅ Correlation ID for tracking
- ✅ Error logging without stopping

---

### Layer 4: Tool Category Functions
**File**: `automation_scanner_v2.py` (Methods: `run_*_tools()`)

**Responsibilities**:
- Define tool variants for each category
- Build command strings with parameters
- Organize commands logically

**Functions** (8 categories):
```python
run_dns_subdomain_tools()           # 77 commands - DNS + Subdomain enum
run_network_tools()                 # 30 commands - nmap, ping, traceroute, whois
run_ssl_tls_tools()                 # 41 commands - testssl, sslyze, sslscan, openssl
run_web_scanning_tools()            # 44 commands - wpscan, wapiti, whatweb, ffuf, golismero
run_directory_enumeration_tools()   # 16 commands - gobuster, dirsearch
run_technology_detection_tools()    # 7 commands - Wappalyzer, retire
run_nuclei_scanner()                # 15 commands - Nuclei templates
run_vulnerability_scanners()        # 95 commands - XSS, SQLi, SSRF, RCE, etc.
```

**Total**: 325+ commands, each with separate output file

---

### Layer 5: Output Management
**File**: `automation_scanner_v2.py` (Methods: `save_output()`, etc.)

**Responsibilities**:
- Create timestamped output directory
- Save individual tool outputs
- Generate execution metadata

**Output Structure**:
```
scan_results_target.com_YYYYMMDD_HHMMSS/
├── dig_a.txt                       # DNS A records
├── dig_aaaa.txt                    # DNS AAAA records
├── nmap_syn.txt                    # nmap SYN scan
├── testssl_basic.txt               # SSL/TLS scan
├── wpscan_https_basic.txt          # WordPress scan
├── xsstrike_https_basic.txt        # XSS detection
├── gobuster_https_common.txt       # Directory enumeration
├── nuclei_https_cves.txt           # Nuclei CVE templates
│
├── EXECUTIVE_SUMMARY.txt           # Human-readable report
├── vulnerability_report.json       # Structured findings
└── tool_execution.log              # Execution metadata
```

**Metadata per file**:
```
======================================================================
Tool: dig_a
Target: dev-erp.sisschools.org
Correlation ID: 20260105_143022
Execution Time: 2026-01-05T14:30:22.123456
Return Code: 0
======================================================================
STDOUT:
[tool output]
STDERR:
[errors if any]
```

---

### Layer 6: Configuration
**File**: `scanner_config.py`

**Responsibilities**:
- Define tool metadata
- Store default parameters
- Configuration constants

**Manages**:
```python
TOOL_COMMANDS = {
    'nmap': ['nmap', 'sudo nmap', '/usr/bin/nmap'],
    'dig': ['dig', '/usr/bin/dig'],
    # ... all 32 tools
}

DEFAULT_CONFIG = {
    'timeout_per_command': None,        # No timeout
    'output_format': 'text',
    'log_level': 'INFO',
    'protocol': 'https',
}
```

---

### Layer 7: Vulnerability Analysis
**File**: `vulnerability_analyzer.py` (Class: `VulnerabilityAnalyzer`)

**Responsibilities**:
- Parse basic tool outputs
- Extract vulnerabilities (very basic)
- Calculate CVSS scores (placeholder)
- Generate remediation guidance (template-based)

**⚠️ LIMITATIONS** (Phase 1):
- No actual parsing of tool outputs
- CVSS scores are guessed/templated
- Remediation is generic
- No deduplication across tools
- No correlation of signals

**What it does**:
```python
def analyze_tool_output(tool_name, output)
    # Very basic: check for keywords
    if "vulnerability" in output.lower():
        return {"found": True, "confidence": 0.3}
    # Not real parsing
```

---

## Data Flow

### Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│ USER: python3 automation_scanner_v2.py target.com -p https   │
└────────────────────────┬─────────────────────────────────────┘
                         │
                    PARSE ARGS
                         │
        ┌────────────────┴────────────────┐
        │                                 │
   ┌────▼──────┐                   ┌────▼──────┐
   │ Gate Mode │                   │ Full Mode │
   │ 6 tools   │                   │ 32 tools  │
   │ 8 commands│                   │ 325+ cmds │
   └────┬──────┘                   └────┬──────┘
        │                              │
        └──────────────┬───────────────┘
                       │
                 INITIALIZE
                 - Extract domain
                 - Build URLs
                 - Create output dir
                       │
                       │
               ┌───────▼────────┐
               │ TOOL DETECTION │
               │ Check 32 tools │
               └───────┬────────┘
                       │
        ┌──────────────▼──────────────┐
        │   BUILD COMMAND LIST        │
        │ (Tool + Category + Variant) │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  FOR EACH COMMAND:          │
        │  1. Build command string    │
        │  2. Execute via subprocess  │
        │  3. Capture stdout/stderr   │
        │  4. Save to file            │
        │  5. Log metadata            │
        │  6. Continue on error       │
        └──────────────┬──────────────┘
                       │
          ┌────────────▼────────────┐
          │ COLLECT ALL OUTPUTS     │
          │ (325+ individual files) │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │ PARSE (Basic)           │
          │ Extract keywords        │
          │ Build finding list      │
          │ ⚠️ Very Limited         │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │ GENERATE REPORTS        │
          │ - Executive summary     │
          │ - JSON findings         │
          │ - Remediation guidance  │
          └────────────┬────────────┘
                       │
          ┌────────────▼────────────┐
          │ FINALIZE SCAN           │
          │ - Calculate time        │
          │ - Save reports          │
          │ - Display summary       │
          └────────────────────────┘
```

---

## Execution Pipeline

### Phase: Initialization
```
Input: target.com -p https --mode full --skip-install
    │
    ├─ Parse arguments
    ├─ Create ComprehensiveSecurityScanner instance
    ├─ Extract domain (domain = "com", subdomain = "target.com")
    ├─ Build URLs: https://target.com, http://target.com
    ├─ Create output directory: scan_results_target.com_20260105_143022/
    └─ Skip tool detection (--skip-install)
```

### Phase: Gate Mode (If Selected)
```
Run 6 essential tools, 8 commands:
1. dig -a (DNS A records)
2. dig -ns (DNS nameservers)
3. sslscan (SSL/TLS scan)
4. whatweb (tech detection)
5. dalfox url (XSS check)
6. xsstrike (XSS check - second opinion)

Time: 5-10 minutes
Decision: If risk > 25 → FAIL, else PASS
```

### Phase: Full Scan (If Selected)
```
Run all 32 tools, 325+ commands across 8 categories:

1. DNS & Subdomain (77 commands)
   - assetfinder (2), dnsrecon (9), dig (14), host (12), etc.
   - Smart logic: Only run subdomain tools on base domain
   
2. Network (30 commands)
   - nmap (19 variants - all scan types)
   - ping (4), traceroute (4), whois (2)
   
3. SSL/TLS (41 commands)
   - testssl.sh (15), sslyze (12), sslscan (5), openssl (7)
   
4. Web Scanning (44 commands)
   - wpscan (10), wapiti (10), whatweb (6), ffuf (6), golismero (6)
   - Run on both HTTPS and HTTP
   
5. Directory Enumeration (16 commands)
   - gobuster (8 variants), dirsearch (8 variants)
   
6. Technology Detection (7 commands)
   - Wappalyzer (2), retire (5)
   
7. Nuclei Templates (15 commands)
   - CVE, vulnerabilities, misconfig, takeovers, etc.
   
8. Vulnerability & Injection (95 commands)
   - xsstrike (10), dalfox (10), xsser (9), sqlmap (10), commix (9), etc.

Time: 2-8 hours
Output: 325+ separate text files
```

### Phase: Output Collection & Reporting
```
Aggregate 325+ tool outputs:
├─ Read each file
├─ Extract basic metadata
├─ Count successes/failures
├─ Generate EXECUTIVE_SUMMARY.txt
├─ Generate vulnerability_report.json
└─ Calculate overall statistics
```

---

## Tool Ecosystem

### Organization by Category

```
CATEGORY 1: DNS & SUBDOMAIN ENUMERATION
├─ DNS Tools (run on target)
│  ├─ assetfinder (2 variants)
│  ├─ dnsrecon (9 variants)
│  ├─ dig (14 variants - A, AAAA, MX, NS, SOA, etc.)
│  ├─ host (12 variants)
│  ├─ dnsenum (3 variants)
│  ├─ nslookup (8 variants)
│  └─ whois (1 variant)
│
└─ Subdomain Tools (run on base domain only - SMART LOGIC)
   ├─ assetfinder (2 variants)
   ├─ findomain (4 variants)
   ├─ theharvester (6 variants - different sources)
   └─ [removed: sublist3r - outdated, unreliable]

CATEGORY 2: NETWORK RECONNAISSANCE
├─ nmap (19 variants)
│  ├─ Port scanning: -sL, -sn, -sS, -sT, -sA, -sN, -sF, -sX
│  ├─ Service detection: -sV, -sO, -A, --script vuln/safe/discovery
│  └─ Coverage: -p-, --top-ports, -p 1-1000
├─ ping (4 variants)
├─ traceroute (4 variants)
└─ whois (2 variants)

CATEGORY 3: SSL/TLS ANALYSIS
├─ testssl.sh (15 variants)
├─ sslyze (12 variants)
├─ sslscan (5 variants)
└─ openssl (7 variants)

CATEGORY 4: WEB APPLICATION SCANNING
├─ wpscan (10 variants - WordPress specific)
├─ wapiti (10 variants - OWASP standard)
├─ whatweb (6 variants - tech fingerprinting)
├─ ffuf (6 variants - directory fuzzing)
└─ golismero (6 variants - comprehensive scanning)
   └─ All run on both HTTPS and HTTP

CATEGORY 5: DIRECTORY & FILE ENUMERATION
├─ gobuster (8 variants)
│  ├─ common wordlist
│  ├─ big wordlist
│  ├─ with extensions (.php, .html, .bak, .txt)
│  └─ different flag combinations
└─ dirsearch (8 variants)
   └─ Similar coverage to gobuster

CATEGORY 6: TECHNOLOGY & VERSION DETECTION
├─ Wappalyzer (2 variants)
│  ├─ Basic detection
│  └─ JSON output for parsing
└─ retire (5 variants)
   ├─ JavaScript library vulnerability detection
   └─ Different source paths and formats

CATEGORY 7: TEMPLATE-BASED VULNERABILITY SCANNING
└─ nuclei (15 variants)
   ├─ CVE templates
   ├─ Vulnerability templates
   ├─ Misconfiguration templates
   ├─ Exposed panels detection
   ├─ Takeover detection
   ├─ Technology-specific templates
   ├─ Network templates
   ├─ Default credentials
   ├─ SSL/TLS templates
   ├─ HTTP headers analysis
   ├─ Info disclosure
   └─ Severity filtering (critical, high)

CATEGORY 8: VULNERABILITY & INJECTION TESTING
├─ xsstrike (10 variants - XSS detection)
├─ dalfox (10 variants - XSS detection)
├─ xsser (9 variants - XSS detection)
├─ ssrfmap (6 variants - SSRF detection)
├─ nosqlmap (7 variants - NoSQL injection)
├─ dotdotpwn (6 variants - Path traversal)
├─ sqlmap (10 variants - SQL injection)
│  └─ With --enable-exploit flag
└─ commix (9 variants - Command injection)
   └─ With --enable-exploit flag
```

---

## File Structure

```
.
├── automation_scanner_v2.py         # Main orchestrator (1006 lines)
│   └─ ComprehensiveSecurityScanner class
│   └─ 8 category functions
│   └─ Gate/Full scan routing
│
├── tool_manager.py                  # Tool detection & installation
│   └─ ToolManager class
│   └─ Supports: apt, pip, brew, go
│
├── scanner_config.py                # Configuration constants
│   └─ Tool metadata
│   └─ Default parameters
│
├── vulnerability_analyzer.py        # Basic analysis (Phase 1)
│   └─ VulnerabilityAnalyzer class
│   └─ ⚠️ Placeholder implementation
│
├── automation_scanner.py            # Legacy entry point (deprecated)
│
└── scan_results_<target>_<timestamp>/
    ├── dig_a.txt                    # Individual tool outputs (325+)
    ├── dig_aaaa.txt
    ├── nmap_syn.txt
    ├── testssl_full.txt
    ├── wpscan_https_basic.txt
    ├── xsstrike_https_crawl.txt
    ├── gobuster_https_common.txt
    ├── nuclei_https_cves.txt
    │
    ├── EXECUTIVE_SUMMARY.txt        # Reports
    ├── vulnerability_report.json
    ├── remediation_report.json
    └── tool_execution.log
```

---

## Current Limitations

### Phase 1 Architecture Constraints

#### 1. **No Parsing of Tool Outputs**
**Problem**: 
- Tool outputs are saved as raw text
- No extraction of actual vulnerabilities
- System treats all outputs as equal

**Example**:
```
xsstrike finds: XSS on /search?q → saves full output to xsstrike_https_crawl.txt
dalfox finds: XSS on /search?q   → saves full output to dalfox_https_crawl.txt
Result: 2 separate findings (should be 1)
```

#### 2. **No Deduplication**
**Problem**:
- Same vulnerability detected by multiple tools = multiple findings
- No correlation across tools
- Manual review needed

**Example**:
```
Risk Score Calculation (Current):
- xsstrike finds XSS → +1 vulnerability
- dalfox finds XSS   → +1 vulnerability
- xsser finds XSS    → +1 vulnerability
Risk = 3 vulnerabilities (should be 1)
```

#### 3. **Tool-Centric, Not Risk-Centric**
**Problem**:
- Decision logic based on "tool execution success"
- Not based on "vulnerability severity"

**Example**:
```
Gate Decision (Current):
6/6 tools successful → PASS
Even if SQLi + RCE + Exposed Creds found

Correct Decision (Phase 2):
risk_score > threshold → FAIL
```

#### 4. **No Signal Correlation**
**Problem**:
- Can't combine signals to increase confidence
- Can't detect attack chains
- Can't prioritize by exploitability

**Example**:
```
Current: 3 separate findings
Phase 2 needed:
- Exposed admin panel (Wappalyzer)
- No authentication check (nuclei)
- SQL Injection in admin (sqlmap)
= HIGH RISK RCE (confirmed)
```

#### 5. **No Intelligent Branching**
**Problem**:
- All tools run regardless of earlier results
- No conditional execution
- No optimization based on findings

**Example**:
```
Current:
1. Target unreachable → sqlmap still runs (wastes time)
2. Port 80 closed → ffuf still runs (wastes time)
3. Old framework detected → exploit tools run (might miss newer issues)

Phase 2 needed:
1. If target unreachable → skip exploitation tools
2. If port closed → skip directory enumeration
3. Adapt tool selection based on tech stack
```

---

## Future Architecture (Phase 2)

### What Phase 2 Adds

```
PHASE 1 (Current)                 PHASE 2 (Intelligence Layer)
┌──────────────────────┐          ┌──────────────────────┐
│ Tool Orchestration   │          │ Finding Intelligence │
│                      │          │                      │
│ ✅ Execution         │    →     │ ✅ Parsing           │
│ ✅ Logging           │          │ ✅ Deduplication     │
│ ✅ Output Files      │          │ ✅ Correlation       │
│ ❌ Parsing           │          │ ✅ Risk Scoring      │
│ ❌ Deduplication     │          │ ✅ Gate Decisions    │
│ ❌ Intelligence      │          │ ✅ Prioritization    │
└──────────────────────┘          └──────────────────────┘
```

### New Components (Phase 2)

```
finding_parser.py
├── XSSParser
├── SQLiParser
├── SSRFParser
├── RCEParser
├── and 20+ more
└── All return canonical Finding objects

deduplicator.py
├── Deduplicate across tools
├── Merge evidence from multiple sources
├── Increase confidence (tool agreement)
└── Create "meta-findings"

risk_engine.py
├── Calculate actual risk (not just CVSS)
├── Consider: exploitability, exposure, authentication
├── Build attack graphs
└── Prioritize findings

gate_decision.py
├── Autonomous pass/fail logic
├── Risk threshold evaluation
├── Compliance checking
└── Reporting for deployment pipelines
```

### Phase 2 Data Model

```python
class Finding:
    tool: str                # "xsstrike"
    finding_type: str        # "xss"
    url: str                 # "https://site.com/search"
    parameter: str           # "q"
    payload: str             # "alert(1)"
    confidence: float        # 0.95
    severity: str            # "high"
    cvss: float              # 7.5
    exploitability: str      # "easily exploitable"
    evidence: List[str]      # Proof from tool
    tools_found_by: List[str]# ["xsstrike", "dalfox"]
    
class RiskScore:
    overall: float           # 0-100
    components: Dict         # CVE risk, exploit risk, etc.
    top_findings: List       # Prioritized findings
    recommendations: List    # "Fix this first"
```

### Phase 2 Deployment Integration

```python
# CI/CD Pipeline Example
result = scanner.run_full_scan(target)
risk = risk_engine.calculate(result.findings)

if risk.overall > deployment_threshold:
    pipeline.fail("Critical vulnerabilities found")
    notify_team(risk.top_findings)
else:
    pipeline.pass("Security gate cleared")
    deploy_to_production()
```

---

## Summary: Current State

| Aspect | Phase 1 (Current) | Phase 2 (Planned) |
|--------|-------------------|-------------------|
| **Tool Coverage** | 32 tools, 325+ commands | Same + parsing |
| **Execution** | ✅ Perfect | ✅ Perfect |
| **Output Files** | ✅ All saved | ✅ All saved |
| **Parsing** | ❌ None | ✅ Comprehensive |
| **Deduplication** | ❌ None | ✅ Full |
| **Risk Calculation** | ⚠️ Basic | ✅ Intelligent |
| **Gate Decisions** | ❌ Manual | ✅ Autonomous |
| **Time to Deploy** | ~30 min review | ~2 min review |

---

## Key Takeaways

1. **You have Phase 1 infrastructure**: Excellent execution engine
2. **You need Phase 2 intelligence**: Parser + deduplicator + risk engine
3. **Keep them separate**: Orchestrator ≠ Intelligence (loose coupling)
4. **This is good architecture**: Hard problems (execution) are solved
5. **Next hard problems**: Parsing, deduplication, correlation (Phase 2)

---

**Document Version**: 1.0  
**Last Updated**: January 5, 2026  
**Status**: Phase 1 Complete, Phase 2 Design In Progress
