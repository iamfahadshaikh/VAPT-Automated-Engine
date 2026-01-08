#!/usr/bin/env python3
"""
Startup Guide - Advanced Security Scanner
First-time setup and introduction
"""

import os
import sys

STARTUP_GUIDE = """
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║         🔒 ADVANCED SECURITY RECONNAISSANCE & VULNERABILITY SCANNER 🔒     ║
║                              Version 2.0                                   ║
║                         Enterprise Edition                                 ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝


👋 WELCOME!

You have successfully installed the most comprehensive automated security
scanning tool. This scanner combines 35+ security tools with intelligent
analysis to provide enterprise-grade vulnerability assessment.

Better than Burp Suite and OWASP ZAP with:
  ✓ Automated multi-tool reconnaissance
  ✓ CVSS 3.1 auto-scoring
  ✓ Risk assessment (0-100)
  ✓ Comprehensive remediation guidance
  ✓ Zero configuration needed


🚀 FIRST TIME? START HERE
════════════════════════════════════════════════════════════════════════════

Step 1: View Quick Start Guide
  $ python3 QUICKSTART.py

Step 2: Install Required Package
  $ pip3 install tabulate

Step 3: Run Your First Scan
  $ python3 automation_scanner.py example.com

Step 4: Review Results
  $ cat scan_results_example.com_*/EXECUTIVE_SUMMARY.txt

That's it! Your first security assessment is ready.


📁 FILES IN YOUR PROJECT
════════════════════════════════════════════════════════════════════════════

Essential Files:
  ✓ automation_scanner.py          Main scanning engine
  ✓ tool_manager.py                Tool detection & installation
  ✓ vulnerability_analyzer.py      CVSS scoring & analysis

Documentation:
  ✓ README.md                      Full documentation
  ✓ IMPLEMENTATION_SUMMARY.md      Technical details
  ✓ QUICKSTART.py                  Quick start guide (run it!)
  ✓ TESTING_GUIDE.py               Test verification

Optional:
  ✓ scanner_config.py              Configuration file
  ✓ PROJECT_FILES.txt              Project file listing


🎯 ALL 9 STAGES INCLUDED
════════════════════════════════════════════════════════════════════════════

Stage 1: Tool Detection ✅
  → Automatically detects installed security tools

Stage 2: Tool Installation ✅
  → Installs missing tools with one command

Stage 3: Protocol Selection ✅
  → Choose HTTP, HTTPS, or both

Stage 4: Timestamped Outputs ✅
  → All results saved with timestamps and correlation IDs

Stage 5: Error Resilience ✅
  → Continues even if tools fail

Stage 6: Results Summary ✅
  → Shows which tools succeeded and failed

Stage 7: Vulnerability Analysis ✅
  → Parses outputs for security issues

Stage 8: Risk Scoring ✅
  → Calculates CVSS and overall risk (0-100)

Stage 9: Comprehensive Reports ✅
  → Executive summary, technical details, remediation steps


📖 RECOMMENDED READING ORDER
════════════════════════════════════════════════════════════════════════════

For Quick Start:
  1. Read this file (you're reading it!)
  2. $ python3 QUICKSTART.py
  3. Run first scan
  4. Check results

For Complete Understanding:
  1. This file
  2. README.md
  3. IMPLEMENTATION_SUMMARY.md
  4. TESTING_GUIDE.py
  5. Run and explore


💻 COMMON COMMANDS
════════════════════════════════════════════════════════════════════════════

Scan a domain:
  $ python3 automation_scanner.py example.com

Scan with HTTPS only:
  $ python3 automation_scanner.py example.com --protocol https

Auto-install all tools:
  $ python3 automation_scanner.py example.com --install-all

Custom output directory:
  $ python3 automation_scanner.py example.com -o my_assessment

Get help:
  $ python3 automation_scanner.py -h

View quick start:
  $ python3 QUICKSTART.py

View test guide:
  $ python3 TESTING_GUIDE.py


🔍 WHAT WILL BE SCANNED
════════════════════════════════════════════════════════════════════════════

✓ DNS Configuration & Vulnerabilities
✓ Subdomain Discovery
✓ Open Ports & Services
✓ SSL/TLS Certificates & Configuration
✓ Web Application Vulnerabilities
✓ CORS & Security Headers
✓ Known Exploits
✓ Service Misconfigurations
✓ Path Traversal & LFI
✓ And much more...

Output:
  Complete vulnerability report with CVSS scores and remediation steps


📊 UNDERSTANDING YOUR RESULTS
════════════════════════════════════════════════════════════════════════════

After scanning, you'll get 3 reports:

1. EXECUTIVE_SUMMARY.txt
   📄 Read this first!
   → Risk score (0-100)
   → Severity level (Critical/High/Medium/Low)
   → Top 5 findings
   → Immediate actions needed

2. vulnerability_report.json
   📋 Technical details
   → All vulnerabilities with CVSS scores
   → CVE references
   → Full descriptions
   → Tool that found it

3. remediation_report.json
   🔧 How to fix
   → Step-by-step instructions
   → Immediate actions
   → Short-term remediation
   → Long-term improvements


⚠️  IMPORTANT REMINDERS
════════════════════════════════════════════════════════════════════════════

1. AUTHORIZATION REQUIRED
   → Only scan systems you own
   → Get written permission for others
   → Never scan production without approval

2. ETHICAL USE
   → Use responsibly
   → Respect rate limits
   → Don't damage target systems
   → Follow all applicable laws

3. NETWORK CONSIDERATION
   → Scan during off-peak hours
   → Be aware of IDS/IPS systems
   → Use VPN if appropriate
   → Monitor for alerts


🔐 RISK SCORE EXPLAINED
════════════════════════════════════════════════════════════════════════════

Overall Risk Score (0-100):

  🔴 ≥75   CRITICAL   - Fix immediately!
  🟠 50-74  HIGH       - Urgent remediation needed
  🟡 25-49  MEDIUM     - Plan remediation
  🟢 <25    LOW        - Monitor and plan

Each vulnerability is scored using CVSS 3.1:
  10.0     - Completely compromised
  7.0-9.9  - Easily exploitable
  4.0-6.9  - Could be exploited
  <4.0     - Unlikely exploitation


🚨 IF YOU GET HIGH SCORES
════════════════════════════════════════════════════════════════════════════

If risk score is ≥75:

1. Don't panic! This scanner is comprehensive
2. Read EXECUTIVE_SUMMARY.txt
3. Review vulnerability_report.json
4. Check remediation_report.json
5. Prioritize by CVSS score (highest first)
6. Follow the remediation steps
7. Re-scan after fixes to verify


📈 SCANNING LARGE TARGETS
════════════════════════════════════════════════════════════════════════════

For IP ranges or many domains:

  Create a script:
  #!/bin/bash
  for target in example1.com example2.com example3.com; do
    python3 automation_scanner.py $target -o assessment_$target
  done

  Or use cron for scheduled scanning:
  0 3 * * 0 python3 automation_scanner.py example.com -o weekly_scan


💡 TIPS & TRICKS
════════════════════════════════════════════════════════════════════════════

Tip 1: Run with sudo for network tools
  $ sudo python3 automation_scanner.py example.com

Tip 2: Use custom output directory
  $ python3 automation_scanner.py example.com -o 2024_q1_assessment

Tip 3: Check specific findings
  $ grep -r "CRITICAL" scan_results_*/

Tip 4: Monitor progress
  $ tail -f scan_results_*/EXECUTIVE_SUMMARY.txt

Tip 5: Schedule regular scans
  $ crontab -e  # Add scanning job

Tip 6: Check only recently found issues
  $ find scan_results_*/ -mtime -1  # Files from last day


🆘 GETTING HELP
════════════════════════════════════════════════════════════════════════════

For Different Needs:

Getting Started:
  $ python3 QUICKSTART.py

Verify It Works:
  $ python3 TESTING_GUIDE.py

Full Documentation:
  $ cat README.md

Technical Details:
  $ cat IMPLEMENTATION_SUMMARY.md

Command Options:
  $ python3 automation_scanner.py -h

See All Files:
  $ cat PROJECT_FILES.txt


✅ NEXT STEPS
════════════════════════════════════════════════════════════════════════════

1️⃣  Install tabulate:
    $ pip3 install tabulate

2️⃣  Run quick start guide:
    $ python3 QUICKSTART.py

3️⃣  Pick a target to scan:
    - Your own domain
    - Dev/staging environment
    - Lab environment

4️⃣  Run your first scan:
    $ python3 automation_scanner.py <target>

5️⃣  Review the results:
    $ cat scan_results_<target>_*/EXECUTIVE_SUMMARY.txt

6️⃣  Follow remediation guidance:
    $ cat scan_results_<target>_*/remediation_report.json

7️⃣  Fix vulnerabilities

8️⃣  Re-scan to verify


🎉 YOU'RE READY!
════════════════════════════════════════════════════════════════════════════

Everything is set up and ready to go. The scanner will:

  ✓ Detect all installed security tools
  ✓ Offer to install missing ones
  ✓ Let you choose HTTP/HTTPS
  ✓ Run comprehensive scans
  ✓ Continue if tools fail
  ✓ Analyze all findings
  ✓ Calculate CVSS scores
  ✓ Generate detailed reports
  ✓ Provide remediation steps

All with zero configuration needed!


═════════════════════════════════════════════════════════════════════════════

🚀 Ready to start?

  $ python3 automation_scanner.py example.com

Or read the guide first:

  $ python3 QUICKSTART.py

═════════════════════════════════════════════════════════════════════════════
"""

def show_menu():
    """Show interactive menu"""
    while True:
        print(STARTUP_GUIDE)
        print("\n" + "="*80)
        print("OPTIONS")
        print("="*80)
        print("1. Show Quick Start Guide (QUICKSTART.py)")
        print("2. Show Testing Guide (TESTING_GUIDE.py)")
        print("3. Show Full README (README.md)")
        print("4. Show Implementation Details (IMPLEMENTATION_SUMMARY.md)")
        print("5. Run your first scan")
        print("6. Exit")
        print("="*80)
        
        choice = input("\nSelect option (1-6): ").strip()
        
        if choice == "1":
            os.system("python3 QUICKSTART.py")
            input("\nPress Enter to continue...")
        elif choice == "2":
            os.system("python3 TESTING_GUIDE.py")
            input("\nPress Enter to continue...")
        elif choice == "3":
            os.system("cat README.md | less" if os.name != "nt" else "type README.md")
            input("\nPress Enter to continue...")
        elif choice == "4":
            os.system("cat IMPLEMENTATION_SUMMARY.md | less" if os.name != "nt" else "type IMPLEMENTATION_SUMMARY.md")
            input("\nPress Enter to continue...")
        elif choice == "5":
            target = input("\nEnter target (domain or IP): ").strip()
            if target:
                cmd = f"python3 automation_scanner.py {target}"
                os.system(cmd)
            input("\nPress Enter to continue...")
        elif choice == "6":
            print("\nGoodbye! Happy scanning! 🔒")
            sys.exit(0)
        else:
            print("Invalid option. Try again.")
        
        print("\n" * 2)

if __name__ == "__main__":
    print(STARTUP_GUIDE)
    
    # Check if running with arguments
    if len(sys.argv) > 1:
        # Just show guide and exit
        sys.exit(0)
    
    # Show menu
    try:
        show_menu()
    except KeyboardInterrupt:
        print("\n\nGoodbye! 🔒")
        sys.exit(0)
