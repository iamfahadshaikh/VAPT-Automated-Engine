# Quick Reference: New Scanner Features

## TL;DR - Three New Features

### 1️⃣ Tool Counter `[X/N]`
**See real-time progress during scans**
```
[1/46] assetfinder_basic      ✓ SUCCESS
[2/46] assetfinder_sorted     ✓ SUCCESS
[3/46] dnsrecon_std           ✓ SUCCESS
```

### 2️⃣ Missing Tool Menu
**When tool not installed, choose what to do**
```
Tool Not Found: gobuster

[1] Skip this tool
[2] Try to install now
[3] Exit and install manually

Enter choice (1-3): _
```

### 3️⃣ Custom Tool Manager
**Add new tools without touching code**
```bash
python3 automation_scanner_v2.py --manage-tools

[1] Add new tool
[2] List custom tools
[3] Remove tool
[4] Back to main menu
```

---

## Commands

### Scan with Progress Display
```bash
python3 automation_scanner_v2.py google.com --mode full
```

### Manage Custom Tools
```bash
python3 automation_scanner_v2.py --manage-tools
```

### Full Scan with Log
```bash
python3 automation_scanner_v2.py google.com --mode full 2>&1 | tee scan.log
```

### Skip Tool Checks
```bash
python3 automation_scanner_v2.py google.com --skip-install
```

### Auto-Install Missing
```bash
python3 automation_scanner_v2.py google.com --install-all
```

---

## Adding a Custom Tool (Step-by-Step)

```bash
$ python3 automation_scanner_v2.py --manage-tools
```

**Menu appears:**
```
[1] Add new tool
```

**Follow prompts:**
- Tool name: `nikto`
- Category: `[3] Web`
- Description: `Web server scanner`
- Method: `[2] apt`
- Package: `nikto`
- Verify: `nikto -V`
- Save? `y`
- Install now? `y`
```
[+] nikto verified successfully!
```

**Done!** Tool is now in `custom_tools.json` and ready to use.

---

## What's New vs. Old

| | Before | After |
|---|--------|-------|
| **Progress** | No visibility | `[23/96] tool ✓` |
| **Missing tool** | Silent skip | Interactive menu |
| **Add tool** | Edit code | `--manage-tools` |
| **Tool storage** | Hardcoded | `custom_tools.json` |
| **Share config** | Not portable | Copy JSON file |

---

## File Changes

**Modified:**
- `automation_scanner_v2.py` (+150 lines)

**New:**
- `tool_custom_installer.py` (380 lines)
- `IMPROVEMENTS_GUIDE.md` (documentation)
- `IMPLEMENTATION_SUMMARY_JAN2026.md` (technical details)

---

## Common Scenarios

### Scenario 1: Tool Missing During Scan

```
[4/46] gobuster_https_common

Tool Not Found: gobuster
Options: [1] Skip [2] Install [3] Exit

Enter choice: 2

[*] Installing gobuster...
[+] gobuster verified successfully!

[4/46] gobuster_https_common  ✓ SUCCESS
```

### Scenario 2: Add Tool for Team

```bash
# Person A adds tool
$ python3 automation_scanner_v2.py --manage-tools
# [1] Add nikto

# Person A shares file
$ cp custom_tools.json ~/shared/

# Person B uses it
$ cp ~/shared/custom_tools.json .
$ python3 automation_scanner_v2.py google.com
# nikto now available!
```

### Scenario 3: Long Running Full Scan

```bash
$ python3 automation_scanner_v2.py google.com --mode full 2>&1 | tee full_scan.log

# See progress like:
[1/96] assetfinder_basic          ✓ SUCCESS
[2/96] assetfinder_sorted         ✓ SUCCESS
[3/96] dnsrecon_std               ✓ SUCCESS
...
[96/96] nuclei_http_all_high      ✓ SUCCESS

[SUMMARY] Scan completed in 2 hours 34 minutes
```

---

## Installation Methods Supported

When adding a tool, choose from:

| Method | For | Example |
|--------|-----|---------|
| **pip** | Python packages | `pip install nikto` |
| **apt** | Ubuntu/Debian | `sudo apt-get install -y nikto` |
| **git** | GitHub projects | Clone repo + setup |
| **brew** | macOS | `brew install nikto` |
| **manual** | Custom setup | Write instructions |

---

## Tips & Tricks

### Tip 1: Save scan with full output
```bash
python3 automation_scanner_v2.py google.com --mode full 2>&1 | tee $(date +%s).log
```

### Tip 2: Skip slow/broken tools
When prompted "Tool Not Found", choose `[1] Skip`.
Scan will continue without that tool.

### Tip 3: Batch add tools
Add all custom tools once with `--manage-tools`, then share `custom_tools.json` with team.

### Tip 4: Auto-install everything
```bash
python3 automation_scanner_v2.py google.com --install-all --mode full
```

### Tip 5: Check what's installed
```bash
python3 automation_scanner_v2.py google.com --mode gate 2>&1 | grep "INSTALLED\|FAILED"
```

---

## Troubleshooting

**Q: Tool counter not showing?**
A: Use `2>&1` to capture stderr. Tool counter logs to stderr.

**Q: Custom tool not being used?**
A: 1) Check `custom_tools.json` exists
   2) Run `--manage-tools` and verify tool is listed
   3) Check verification command works: `nikto -V`

**Q: Lost custom_tools.json?**
A: Create backup first: `cp custom_tools.json custom_tools.json.backup`
   Then add tools again with `--manage-tools`

**Q: Installation timeout?**
A: Choose `[1] Skip`, then install manually:
   ```bash
   sudo apt-get install -y nikto
   ```

**Q: Can't install tool automatically?**
A: Choose `[3] Exit`, then:
   ```bash
   # Install manually
   sudo apt-get install -y toolname
   
   # Re-run scan
   python3 automation_scanner_v2.py google.com
   ```

---

## What to Read Next

- **IMPROVEMENTS_GUIDE.md** - Detailed usage guide with examples
- **IMPLEMENTATION_SUMMARY_JAN2026.md** - Technical implementation details
- **ARCHITECTURE.md** - Overall system design
- **README.md** - Main project documentation

---

## Requirements Coverage

✅ **Requirement 61** - Tool counter display (X/N format)
✅ **Requirement 62** - Interactive missing tool handling
✅ **Requirement 65** - Custom tool addition module

🔜 **Next Phase:**
- Requirement 6-17: DNS/Subdomain optimization
- Requirement 29-44: Tool gating by detection
- Requirement 52-55: Execution control & budgets
- Requirement 56-60: Output optimization

---

**Everything is production-ready! Start with:**
```bash
python3 automation_scanner_v2.py google.com --mode full 2>&1 | tee scan.log
```
