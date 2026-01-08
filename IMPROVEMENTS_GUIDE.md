# Scanner Improvements - Usage Guide

## Recent Improvements (January 2026)

### 1. Tool Counter Display ✓
**Requirement 61: Show tool progress like "1/36 whatweb", "2/36 nmap"**

The scanner now displays progress during execution:

```
[1/46] assetfinder_basic               ✓ SUCCESS
[2/46] assetfinder_sorted              ✓ SUCCESS
[3/46] dnsrecon_std                    ✓ SUCCESS
[4/46] dnsrecon_axfr                   ✓ SUCCESS
```

**Benefits:**
- See real-time progress
- Know how many tools remain
- Estimate time to completion
- Identify which tool is hanging (if any)

---

### 2. Interactive Tool Installation ✓
**Requirement 62: If tool not found, ask user before failing**

When a tool is missing, you now get a menu:

```
======================================================================
Tool Not Found: gobuster
Required for: gobuster_https_common
======================================================================
Options:
  [1] Skip this tool and continue
  [2] Try to install now
  [3] Exit and install manually

Enter choice (1-3, default=1): 
```

**Options:**
- **[1] Skip** - Continue scan without this tool
- **[2] Install** - Attempt auto-installation (may require sudo password)
- **[3] Exit** - Stop scan and install manually

**Benefits:**
- No more "tool not found" failures mid-scan
- Automatic installation attempts
- User control over what happens

---

### 3. Custom Tool Manager ✓
**Requirement 65: Allow users to add new tools interactively**

Run the interactive tool manager:

```bash
python3 automation_scanner_v2.py --manage-tools
```

This opens a menu:

```
======================================================================
CUSTOM TOOL MANAGER
======================================================================
Options:
  [1] Add new tool
  [2] List custom tools
  [3] Remove tool
  [4] Back to main menu

Enter choice (1-4):
```

#### Adding a Tool

When you select **[1] Add new tool**, you'll be asked:

1. **Tool name** - e.g., `nikto`, `zap`, `burpsuite`
2. **Category** - DNS, Network, SSL/TLS, Web, Directory, Vulnerabilities, Other
3. **Description** - What this tool does
4. **Installation method:**
   - `pip` - Python package manager
   - `apt` - Ubuntu/Debian packages
   - `git` - Clone & build from source
   - `brew` - macOS Homebrew
   - `manual` - Custom/manual setup

5. **Package/URL** - Package name or git repository
6. **Verification command** - How to verify installation (e.g., `nikto --version`)

**Example: Adding Nikto**

```
Enter tool name: nikto
Select category: [3] Web
Enter tool description: Web server scanner
Select method: [2] apt
Enter apt package name: nikto
Enter verification command: nikto -V

[SUCCESS] Tool 'nikto' added successfully!
Install now? (y/n): y
[*] Installing nikto...
[+] nikto verified successfully!
```

The tool is now:
- Saved to `custom_tools.json`
- Added to the scanner's tool database
- Ready to use in scans

#### Listing Custom Tools

Select **[2] List custom tools** to see all added custom tools:

```
======================================================================
CUSTOM TOOLS
======================================================================

✓ nikto
  Category:     Web
  Description:  Web server scanner
  Method:       apt

✓ zap-cli
  Category:     Web
  Description:  OWASP ZAP command-line interface
  Method:       pip
```

#### Removing Tools

Select **[3] Remove tool** and confirm:

```
Enter tool name to remove: nikto
Remove tool 'nikto'? (y/n): y
[SUCCESS] Tool 'nikto' removed
```

---

## How To Use

### Basic Scan (with progress)

```bash
python3 automation_scanner_v2.py google.com -p https
```

**Output preview:**
```
[*] Scanning for installed tools...
✓ assetfinder          (DNS            ) - INSTALLED
✓ dnsrecon             (DNS            ) - INSTALLED
...
[10:35:27] [INFO] Target: google.com
[10:35:27] [INFO] Domain: google.com

Starting DNS Reconnaissance
[1/46] assetfinder_basic               ✓ SUCCESS
[2/46] assetfinder_sorted              ✓ SUCCESS
[3/46] dnsrecon_std                    ✓ SUCCESS
```

### Full Scan with Log

```bash
python3 automation_scanner_v2.py google.com --mode full 2>&1 | tee full_scan.log
```

### Skip Initial Tool Check

```bash
python3 automation_scanner_v2.py google.com --skip-install
```

### Auto-install Missing Tools

```bash
python3 automation_scanner_v2.py google.com --install-all
```

### Manage Tools

```bash
python3 automation_scanner_v2.py --manage-tools
```

---

## Technical Details

### Files Modified/Created

1. **automation_scanner_v2.py** (~1210 lines)
   - Added tool counter tracking
   - Added `_handle_missing_tool()` method
   - Integrated custom tool installer
   - Added `--manage-tools` CLI flag

2. **tool_custom_installer.py** (NEW, 380 lines)
   - `CustomToolInstaller` class - adds/removes/lists tools
   - `custom_tool_menu()` - interactive menu system
   - Supports: pip, apt, git, brew, manual setup
   - Stores custom tools in `custom_tools.json`

### Data Storage

Custom tools are saved in `custom_tools.json`:

```json
{
  "nikto": {
    "apt": "nikto",
    "category": "Web",
    "description": "Web server scanner",
    "custom": true,
    "install_method": "apt",
    "verify_cmd": "nikto -V"
  }
}
```

This JSON is:
- Portable (copy between machines)
- Version-controllable
- Easy to share with teams

---

## Next Steps (Future Improvements)

These are planned for the next phase:

### Phase 1: DNS/Subdomain Optimization (Requirements 6-17)
- Skip DNS entirely for IP targets
- Single A/AAAA lookup for subdomains only
- Max 2 subdomain enumeration tools
- Deduplicate DNS results before use
- Resolve discovered subdomains before scanning

### Phase 2: Tool Gating (Requirements 29-44)
- Run TLS tools only if HTTPS detected
- Run WordPress tools only if WordPress confirmed
- Run XSS tools only after reflection detected
- Run SQL injection tools only if parameters exist
- Run command injection tools only if command-like parameters exist

### Phase 3: Execution Control (Requirements 52-55)
- Decision layer before each phase
- Stop pipeline if earlier phase fails
- Per-tool timeouts
- Global runtime budget

### Phase 4: Output & Reporting (Requirements 56-60)
- Map findings to OWASP categories
- Suppress informational noise by default
- Store raw output separately from findings
- Generate concise human-readable summary

---

## Troubleshooting

### "Tool Not Found" During Scan

If you see:
```
[WARN] Tool Not Found: gobuster
```

Press **[2]** to install, or **[1]** to skip.

### Custom Tool Not Working

1. Verify installation manually:
   ```bash
   which nikto
   nikto -V
   ```

2. Check `custom_tools.json` for correct verify command

3. Re-add the tool with correct command:
   ```bash
   python3 automation_scanner_v2.py --manage-tools
   # Select [3] Remove tool
   # Select [1] Add new tool (with corrected command)
   ```

### Lost Custom Tools

Custom tools are stored in `custom_tools.json` in the same directory.

To backup:
```bash
cp custom_tools.json custom_tools.json.backup
```

To restore:
```bash
cp custom_tools.json.backup custom_tools.json
```

---

## Examples

### Example 1: Add Nikto (Web Scanner)

```bash
$ python3 automation_scanner_v2.py --manage-tools

[1] Add new tool
Enter tool name: nikto
Select category: [3] Web
Enter tool description: Web server vulnerability scanner
Select method: [2] apt
Enter apt package name: nikto
Enter verification command: nikto -V

Install now? (y/n): y
[+] nikto verified successfully!
```

### Example 2: Add Custom Python Tool via Git

```bash
$ python3 automation_scanner_v2.py --manage-tools

[1] Add new tool
Enter tool name: subfinder
Select category: [1] DNS
Enter tool description: Subdomain discovery tool
Select method: [3] git
Enter git repository URL: https://github.com/projectdiscovery/subfinder.git
Enter folder name after clone: subfinder
Enter verification command: subfinder -version

Install now? (y/n): y
[+] subfinder verified successfully!
```

### Example 3: Full Scan with Progress

```bash
$ python3 automation_scanner_v2.py example.com --mode full 2>&1 | tee example_full_scan.log

[*] Scanning for installed tools...
✓ assetfinder          (DNS            ) - INSTALLED
✓ dnsrecon             (DNS            ) - INSTALLED
✓ nmap                 (Network        ) - INSTALLED
...

[10:35:27] [INFO] Target: example.com

Starting DNS Reconnaissance
[1/96] assetfinder_basic               ✓ SUCCESS
[2/96] assetfinder_sorted              ✓ SUCCESS
[3/96] dnsrecon_std                    ✓ SUCCESS
[4/96] dnsrecon_axfr                   ✓ SUCCESS
...
```

---

## Summary

These improvements provide:

✓ **Visibility** - See exact progress (X/N tools)
✓ **Resilience** - Handle missing tools interactively
✓ **Extensibility** - Add custom tools without code changes
✓ **Portability** - Share custom tools via `custom_tools.json`
✓ **User Control** - Choose what to do when issues occur

Next phase will add **intelligence** - tools run conditionally based on what's been discovered so far.
