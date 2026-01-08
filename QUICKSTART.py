#!/usr/bin/env python3
"""
Quick Start Guide - Advanced Security Scanner
"""

QUICK_START = """
╔════════════════════════════════════════════════════════════════════════════╗
║         ADVANCED SECURITY RECONNAISSANCE & VULNERABILITY SCANNER           ║
║                              QUICK START GUIDE                             ║
╚════════════════════════════════════════════════════════════════════════════╝

INSTALLATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Install Python packages:
   $ pip3 install tabulate

2. The scanner will auto-detect installed tools and offer to install missing ones:
   $ python3 automation_scanner.py example.com

3. Or auto-install all tools at once:
   $ python3 automation_scanner.py example.com --install-all


BASIC USAGE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scan a target (both HTTP and HTTPS):
  $ python3 automation_scanner.py example.com

Scan HTTPS only:
  $ python3 automation_scanner.py example.com --protocol https

Scan HTTP only:
  $ python3 automation_scanner.py example.com --protocol http

Custom output directory:
  $ python3 automation_scanner.py example.com -o my_assessment


WHAT HAPPENS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STAGE 1: Tool Detection
  ✓ Scans for all security tools on your system
  ✓ Shows which are installed and which are missing

STAGE 2: Tool Installation (Optional)
  ✓ Offers to install missing tools
  ✓ Supports apt, pip, brew, and Go installers

STAGE 3: Protocol Selection
  ✓ Asks if you want HTTP, HTTPS, or both
  ✓ Configures scan URLs accordingly

STAGE 4: Comprehensive Scanning
  ✓ DNS Enumeration (assetfinder, dnsrecon, dig, nslookup, dnsenum)
  ✓ Subdomain Discovery (findomain, sublister, theharvester)
  ✓ Network Scanning (nmap, ping, traceroute, whois)
  ✓ SSL/TLS Analysis (testssl, sslyze, sslscan)
  ✓ Web Scanning (whatweb, wpscan, corsy)
  ✓ Vulnerability Detection (xsstrike, dalfox, commix)

STAGE 5: Error Resilience
  ✓ If one tool fails, others continue running
  ✓ All errors are logged and tracked

STAGE 6: Results Summary
  ✓ Displays table showing all tools and their status
  ✓ Shows how many passed and how many failed

STAGE 7: Vulnerability Analysis
  ✓ Parses all tool outputs
  ✓ Calculates CVSS scores automatically
  ✓ Identifies security issues

STAGE 8: Risk Scoring
  ✓ Calculates Overall Risk Score (0-100)
  ✓ Displays Severity Level:
    - ≥75: 🔴 CRITICAL - Fix immediately
    - 50-74: 🟠 HIGH - Urgent action needed
    - 25-49: 🟡 MEDIUM - Plan remediation
    - <25: 🟢 LOW - Monitor
  ✓ Warns if score ≥75

STAGE 9: Comprehensive Reports
  ✓ EXECUTIVE_SUMMARY.txt - Top findings and actions
  ✓ vulnerability_report.json - Detailed technical findings
  ✓ remediation_report.json - Step-by-step fix instructions


OUTPUT FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

All results saved to: scan_results_<target>_<timestamp>/

Key files:
  📄 EXECUTIVE_SUMMARY.txt
     └─ Read this first! Summary with top findings and risk score

  📊 vulnerability_report.json
     └─ Detailed findings with CVSS scores

  🔧 remediation_report.json
     └─ How to fix each vulnerability

  📋 Individual tool outputs
     └─ Raw output from each scanning tool


UNDERSTANDING THE REPORTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RISK SCORE (0-100):
  Calculated from:
  - Number and severity of vulnerabilities
  - CVSS scores of findings
  - Types of issues discovered

SEVERITY LEVELS:
  CRITICAL (9.0-10.0): Immediate exploitation risk
  HIGH (7.0-8.9):      Likely exploitation path
  MEDIUM (4.0-6.9):    Possible exploitation
  LOW (0.1-3.9):       Unlikely exploitation

CVSS SCORES:
  Automatically calculated based on:
  - Attack Vector (Network, Adjacent, Local, Physical)
  - Privileges Required (None, Low, High)
  - User Interaction (None, Required)
  - Scope (Unchanged, Changed)
  - Confidentiality/Integrity/Availability impact


REMEDIATION GUIDANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Each vulnerability includes:
  ✓ Description of the issue
  ✓ Why it's a problem
  ✓ Exact steps to fix it
  ✓ CVE reference (if applicable)
  ✓ CVSS score and severity
  ✓ Immediate/short-term/long-term actions


EXAMPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scan example.com and auto-install missing tools:
  $ python3 automation_scanner.py example.com --install-all

Scan 192.168.1.1 on HTTPS only with custom output:
  $ python3 automation_scanner.py 192.168.1.1 -p https -o network_audit

Scan api.company.com without any prompts:
  $ python3 automation_scanner.py api.company.com --skip-install


COMPARING TO OTHER TOOLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Feature                    This Tool    Burp Suite    OWASP ZAP
────────────────────────────────────────────────────────────────
Automated DNS Scan         ✓ Yes        ✗ No          ✗ No
Subdomain Enumeration      ✓ Yes        ✗ No          ✗ No
Multi-Tool Integration     ✓ Yes        ✗ No          ✗ No
Auto CVSS Scoring          ✓ Yes        ⚠ Manual      ⚠ Manual
Risk Score (0-100)         ✓ Yes        ✗ No          ✗ No
Remediation Guidance       ✓ Yes        ⚠ Basic       ⚠ Basic
Cost                       ✓ Free       ✗ Expensive   ✓ Free
Continuous Monitoring      ✓ Yes        ✗ No          ✗ No


TIPS & TRICKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✓ Run with highest privileges for network tools:
  $ sudo python3 automation_scanner.py example.com

✓ Check results quickly:
  $ cat scan_results_*/EXECUTIVE_SUMMARY.txt

✓ Extract specific findings:
  $ grep -r "CRITICAL" scan_results_*/*.json

✓ Monitor progress in real-time:
  $ tail -f scan_results_*/EXECUTIVE_SUMMARY.txt

✓ Schedule regular scans:
  $ crontab -e
  # Add: 0 3 * * 0 python3 /path/to/automation_scanner.py example.com -o weekly_scan


IMPORTANT REMINDERS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️  ONLY SCAN SYSTEMS YOU OWN OR HAVE PERMISSION TO TEST

  - Get written authorization before scanning
  - Use responsibly and ethically
  - Never scan production systems without permission
  - Respect rate limits
  - Follow applicable laws


GETTING HELP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View full documentation:
  $ cat README.md

Get help on command-line options:
  $ python3 automation_scanner.py -h

Check tool installation status:
  The scanner shows this automatically at startup

Troubleshoot missing tools:
  Run with --install-all to auto-install everything


NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Run your first scan:
   $ python3 automation_scanner.py example.com --install-all

2. Wait for completion (usually 5-10 minutes)

3. Review EXECUTIVE_SUMMARY.txt in output directory

4. Follow remediation guidance in remediation_report.json

5. Fix identified vulnerabilities

6. Run scan again to verify fixes


═════════════════════════════════════════════════════════════════════════════
Ready to scan? Run: python3 automation_scanner.py <target>
═════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(QUICK_START)
