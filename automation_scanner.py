#!/usr/bin/env python3
"""
Advanced Automated Security Reconnaissance & Vulnerability Scanner
With tool detection, installation, CVSS scoring, and comprehensive analysis
"""

import subprocess
import sys
import os
from datetime import datetime
import json
import argparse
from pathlib import Path
import time
from typing import Dict, List, Tuple

try:
    from tabulate import tabulate
except ImportError:
    def tabulate(data, headers, tablefmt):
        # Fallback if tabulate not installed
        return str(data)

from tool_manager import ToolManager
from vulnerability_analyzer import VulnerabilityAnalyzer

class AdvancedScanner:
    def __init__(self, target, protocol='both', output_dir=None, skip_tool_check=False):
        self.target = target
        self.protocol = protocol
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = datetime.now()
        self.correlation_id = self.timestamp
        self.output_dir = output_dir or f"scan_results_{self.target}_{self.timestamp}"
        
        # Tool management
        self.tool_manager = ToolManager()
        if not skip_tool_check:
            self.tool_manager.scan_all_tools()
        
        # Results tracking
        self.tool_results = {}
        self.errors = []
        self.vulnerabilities = []
        self.analyzer = VulnerabilityAnalyzer()
        
        # Create output directory
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        self.tools_by_category = self.tool_manager.get_installed_tools_by_category()
        
        self.log(f"Output directory: {self.output_dir}", "INFO")
        self.log(f"Correlation ID: {self.correlation_id}", "INFO")
        self.log(f"Protocol: {self.protocol}", "INFO")
    
    def log(self, message, level="INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def ask_for_protocol(self):
        """Ask user for protocol preference"""
        print("\n" + "="*60)
        print("PROTOCOL SELECTION")
        print("="*60)
        print("1. HTTP only (insecure)")
        print("2. HTTPS only (secure)")
        print("3. Both HTTP and HTTPS")
        print("4. Auto-detect")
        
        choice = input("\nSelect protocol (1-4): ").strip()
        
        protocol_map = {
            '1': 'http',
            '2': 'https',
            '3': 'both',
            '4': 'auto'
        }
        
        self.protocol = protocol_map.get(choice, 'both')
        self.log(f"Protocol set to: {self.protocol}", "INFO")
    
    def get_urls(self):
        """Get URLs based on protocol preference"""
        if self.protocol == 'http':
            return [f"http://{self.target}"]
        elif self.protocol == 'https':
            return [f"https://{self.target}"]
        elif self.protocol == 'both':
            return [f"http://{self.target}", f"https://{self.target}"]
        else:  # auto
            return [f"https://{self.target}", f"http://{self.target}"]
    
    def run_command(self, tool_name: str, command: str) -> Tuple[str, str, int]:
        """Execute command with error handling"""
        try:
            self.log(f"Running {tool_name}...", "RUN")
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            self.log(f"Error running {tool_name}: {str(e)}", "ERROR")
            return "", str(e), -1
    
    def save_output(self, tool_name: str, stdout: str, stderr: str, returncode: int) -> str:
        """Save output with timestamp"""
        output_file = os.path.join(self.output_dir, f"{tool_name.replace(' ', '_')}.txt")
        try:
            with open(output_file, 'w') as f:
                f.write(f"{'='*70}\n")
                f.write(f"Tool: {tool_name}\n")
                f.write(f"Target: {self.target}\n")
                f.write(f"Correlation ID: {self.correlation_id}\n")
                f.write(f"Execution Time: {datetime.now().isoformat()}\n")
                f.write(f"Return Code: {returncode}\n")
                f.write(f"{'='*70}\n\n")
                f.write("STDOUT:\n")
                f.write(stdout or "[No output]")
                f.write("\n\nSTDERR:\n")
                f.write(stderr or "[No errors]")
            return output_file
        except Exception as e:
            self.log(f"Could not save output for {tool_name}: {str(e)}", "ERROR")
            return None
    
    def run_dns_tools(self):
        """Run DNS enumeration tools"""
        if 'DNS' not in self.tools_by_category:
            self.log("No DNS tools installed", "SKIP")
            return
        
        self.log("=" * 60, "SECTION")
        self.log("Starting DNS Reconnaissance", "SECTION")
        self.log("=" * 60, "SECTION")
        
        commands = []
        # Only add assetfinder-related commands if assetfinder is available
        try:
            if self.tool_manager.check_tool_installed("assetfinder"):
                commands.append(("assetfinder", f"assetfinder {self.target}"))
                commands.append(("assetfinder_unique", f"assetfinder {self.target} | sort -u"))
        except Exception:
            pass

        commands.extend([
            ("dnsrecon_std", f"dnsrecon -d {self.target} -t std"),
            ("dnsrecon_srv", f"dnsrecon -d {self.target} -t srv"),
            ("dnsrecon_dnssec", f"dnsrecon -d {self.target} -t dnssec"),
            ("host_records", f"host -a {self.target}"),
            ("dig_all", f"dig {self.target} ANY"),
            ("dig_trace", f"dig +trace {self.target}"),
            ("nslookup_any", f"nslookup -type=ANY {self.target}"),
            ("dnsenum", f"dnsenum {self.target}"),
        ])
        
        self._execute_tools(commands)
    
    def run_subdomain_tools(self):
        """Run subdomain enumeration tools"""
        if 'Subdomains' not in self.tools_by_category:
            self.log("No subdomain tools installed", "SKIP")
            return
        
        self.log("=" * 60, "SECTION")
        self.log("Starting Subdomain Enumeration", "SECTION")
        self.log("=" * 60, "SECTION")
        
        commands = [
            ("findomain", f"findomain -t {self.target} --all"),
            ("findomain_with_ips", f"findomain -t {self.target} --ip"),
            # Use the correct binary name for Sublist3r
            ("sublister", f"sublist3r -d {self.target}"),
            ("sublister_bruteforce", f"sublist3r -d {self.target} --bruteforce"),
            ("theharvester_google", f"theHarvester -d {self.target} -b google -l 100"),
            ("theharvester_crtsh", f"theHarvester -d {self.target} -b crtsh -l 100"),
        ]
        
        self._execute_tools(commands)
    
    def run_network_tools(self):
        """Run network reconnaissance tools"""
        if 'Network' not in self.tools_by_category:
            self.log("No network tools installed", "SKIP")
            return
        
        self.log("=" * 60, "SECTION")
        self.log("Starting Network Reconnaissance", "SECTION")
        self.log("=" * 60, "SECTION")
        
        commands = [
            ("ping", f"ping -c 4 {self.target}"),
            ("traceroute", f"traceroute -n {self.target}"),
            ("whois", f"whois {self.target}"),
            ("nmap_fast", f"nmap -F {self.target}"),
            ("nmap_service_version", f"nmap -sV {self.target}"),
            ("nmap_scripts", f"nmap --script vuln {self.target}"),
        ]
        
        self._execute_tools(commands)
    
    def run_ssl_tls_tools(self):
        """Run SSL/TLS analysis tools"""
        if 'SSL/TLS' not in self.tools_by_category:
            self.log("No SSL/TLS tools installed", "SKIP")
            return
        
        self.log("=" * 60, "SECTION")
        self.log("Starting SSL/TLS Analysis", "SECTION")
        self.log("=" * 60, "SECTION")
        
        commands = [
            ("testssl_full", f"testssl --full https://{self.target}"),
            ("sslyze", f"sslyze {self.target}:443 --regular --certinfo=basic"),
            ("sslscan", f"sslscan {self.target}:443"),
            ("openssl_cert", f"openssl s_client -connect {self.target}:443 -showcerts"),
        ]
        
        self._execute_tools(commands)
    
    def run_web_scanning_tools(self):
        """Run web application scanning tools"""
        if 'Web' not in self.tools_by_category:
            self.log("No web scanning tools installed", "SKIP")
            return
        
        self.log("=" * 60, "SECTION")
        self.log("Starting Web Application Scanning", "SECTION")
        self.log("=" * 60, "SECTION")
        
        urls = self.get_urls()
        commands = []
        
        for url in urls:
            protocol = "https" if "https" in url else "http"
            commands.extend([
                (f"whatweb_{protocol}", f"whatweb {url}"),
                (f"whatweb_verbose_{protocol}", f"whatweb -v {url}"),
                (f"corsy_{protocol}", f"corsy -u {url}"),
            ])
        
        self._execute_tools(commands)
    
    def run_vulnerability_scanners(self):
        """Run vulnerability detection tools"""
        if 'Vulnerabilities' not in self.tools_by_category:
            self.log("No vulnerability scanners installed", "SKIP")
            return
        
        self.log("=" * 60, "SECTION")
        self.log("Starting Vulnerability Assessment", "SECTION")
        self.log("=" * 60, "SECTION")
        
        urls = self.get_urls()
        commands = []
        
        for url in urls:
            protocol = "https" if "https" in url else "http"
            commands.extend([
                (f"xsstrike_{protocol}", f"xsstrike -u {url} --crawl"),
                (f"dalfox_{protocol}", f"dalfox scan --url {url}"),
            ])
        
        self._execute_tools(commands)
    
    def _execute_tools(self, commands: List[Tuple[str, str]]):
        """Execute list of tools"""
        for tool_name, command in commands:
            execution_time = datetime.now().isoformat()
            stdout, stderr, returncode = self.run_command(tool_name, command)
            
            # Treat pure empty output (no stdout and no stderr) as failure to avoid confusing 'success with 0 bytes'
            if returncode == 0 and ((stdout and stdout.strip()) or (stderr and stderr.strip())):
                output_file = self.save_output(tool_name, stdout, stderr, returncode)
                self.tool_results[tool_name] = {
                    'status': 'SUCCESS',
                    'output_file': output_file,
                    'return_code': returncode,
                    'execution_time': execution_time,
                    'stdout_length': len(stdout or ""),
                    'has_error': returncode != 0
                }
                self.log(f"{tool_name} completed successfully", "SUCCESS")
                
                # Analyze output
                self._analyze_tool_output(tool_name, stdout)
            else:
                self.tool_results[tool_name] = {
                    'status': 'FAILED',
                    'output_file': None,
                    'return_code': returncode,
                    'execution_time': execution_time,
                    'error': stderr or 'No output'
                }
                self.errors.append({
                    'tool': tool_name,
                    'error': stderr or 'No output',
                    'return_code': returncode
                })
                self.log(f"{tool_name} failed or tool not installed", "WARN")
            
            time.sleep(0.5)
    
    def _analyze_tool_output(self, tool_name: str, output: str):
        """Analyze tool output for vulnerabilities"""
        if not output:
            return
        
        if 'ssl' in tool_name.lower() or 'testssl' in tool_name.lower() or 'sslscan' in tool_name.lower():
            vulns = self.analyzer.analyze_ssl_scan(output, tool_name)
        elif 'nmap' in tool_name.lower():
            vulns = self.analyzer.analyze_nmap_output(output, tool_name)
        elif any(x in tool_name.lower() for x in ['whatweb', 'corsy', 'xsstrike', 'dalfox']):
            vulns = self.analyzer.analyze_web_scan(output, tool_name)
        elif any(x in tool_name.lower() for x in ['dns', 'dig', 'nslookup', 'dnsrecon']):
            vulns = self.analyzer.analyze_dns_output(output, tool_name)
        else:
            vulns = []
        
        self.vulnerabilities.extend(vulns)
        self.analyzer.vulnerabilities.extend(vulns)
    
    def generate_results_table(self):
        """Generate summary table of tool execution"""
        table_data = []
        success_count = 0
        failed_count = 0
        
        for tool_name, result in sorted(self.tool_results.items()):
            status = result['status']
            if status == 'SUCCESS':
                success_count += 1
                status_icon = "✓"
            else:
                failed_count += 1
                status_icon = "✗"
            
            exec_time = result.get('execution_time', 'N/A')
            if isinstance(exec_time, str) and 'T' in exec_time:
                exec_time = exec_time.split('T')[1][:8]
            
            table_data.append([
                tool_name,
                status_icon + " " + status,
                exec_time,
                result.get('stdout_length', 0) if result['status'] == 'SUCCESS' else 'Error'
            ])
        
        print("\n" + "="*80)
        print("TOOL EXECUTION RESULTS SUMMARY")
        print("="*80)
        
        headers = ["Tool Name", "Status", "Execution Time", "Output Size (bytes)"]
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        print(f"\nTotal Tools Run: {len(self.tool_results)}")
        print(f"Successful: {success_count}")
        print(f"Failed: {failed_count}")
        
        return success_count, failed_count
    
    def generate_vulnerability_report(self):
        """Generate comprehensive vulnerability report"""
        report = {
            'scan_info': {
                'target': self.target,
                'timestamp': self.timestamp,
                'correlation_id': self.correlation_id,
                'protocol': self.protocol,
                'scan_duration_seconds': (datetime.now() - self.start_time).total_seconds(),
            },
            'tools_summary': {
                'total': len(self.tool_results),
                'successful': len([r for r in self.tool_results.values() if r['status'] == 'SUCCESS']),
                'failed': len([r for r in self.tool_results.values() if r['status'] == 'FAILED']),
            },
            'vulnerabilities': {
                'total': len(self.vulnerabilities),
                'critical': len([v for v in self.vulnerabilities if v['severity'] == 'CRITICAL']),
                'high': len([v for v in self.vulnerabilities if v['severity'] == 'HIGH']),
                'medium': len([v for v in self.vulnerabilities if v['severity'] == 'MEDIUM']),
                'low': len([v for v in self.vulnerabilities if v['severity'] == 'LOW']),
            },
        }
        
        # Calculate scores
        overall_score, severity = self.analyzer.calculate_overall_risk_score()
        report['risk_assessment'] = {
            'overall_risk_score': overall_score,
            'severity_level': severity,
            'individual_vulnerabilities': self.vulnerabilities,
        }
        
        return report
    
    def generate_remediation_report(self):
        """Generate detailed remediation guidance"""
        report = self.analyzer.generate_remediation_report()
        
        print("\n" + "="*80)
        print("REMEDIATION GUIDANCE REPORT")
        print("="*80)
        
        if report['critical_count'] > 0:
            print(f"\n⚠️  CRITICAL SEVERITY - {report['critical_count']} issues found")
            print("Immediate action required!")
            for vuln in report['vulnerabilities_by_severity']['CRITICAL']:
                print(f"\n  • {vuln['type']}")
                print(f"    CVSS Score: {vuln['cvss_score']}")
                print(f"    Description: {vuln['description']}")
                print(f"    Remediation: {vuln['remediation']}")
                if vuln.get('cve'):
                    print(f"    CVE: {vuln['cve']}")
        
        return report
    
    def run_full_scan(self):
        """Run complete security assessment"""
        print("\n" + "="*80)
        print(f"STARTING COMPREHENSIVE SECURITY SCAN")
        print(f"Target: {self.target}")
        print(f"Start Time: {self.start_time.isoformat()}")
        print("="*80)
        
        try:
            self.run_dns_tools()
            self.run_subdomain_tools()
            self.run_network_tools()
            self.run_ssl_tls_tools()
            self.run_web_scanning_tools()
            self.run_vulnerability_scanners()
            
            success, failed = self.generate_results_table()
            
            vuln_report = self.generate_vulnerability_report()
            self._save_json_report(vuln_report, "vulnerability_report.json")
            
            remediation_report = self.generate_remediation_report()
            self._save_json_report(remediation_report, "remediation_report.json")
            
            self._generate_executive_summary(vuln_report)
            
        except KeyboardInterrupt:
            self.log("Scan interrupted by user", "WARN")
        except Exception as e:
            self.log(f"Fatal error: {str(e)}", "ERROR")
        finally:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.log(f"Scan completed in {elapsed:.2f} seconds", "INFO")
            self.log(f"Results saved to: {self.output_dir}", "INFO")
    
    def _save_json_report(self, report: Dict, filename: str):
        """Save JSON report"""
        report_file = os.path.join(self.output_dir, filename)
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            self.log(f"Report saved: {report_file}", "SUCCESS")
        except Exception as e:
            self.log(f"Error saving report: {str(e)}", "ERROR")
    
    def _generate_executive_summary(self, report: Dict):
        """Generate executive summary"""
        risk = report['risk_assessment']
        score = risk['overall_risk_score']
        severity = risk['severity_level']
        
        summary_file = os.path.join(self.output_dir, "EXECUTIVE_SUMMARY.txt")
        
        with open(summary_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("EXECUTIVE SUMMARY - SECURITY ASSESSMENT REPORT\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Target: {self.target}\n")
            f.write(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Correlation ID: {self.correlation_id}\n\n")
            
            f.write("RISK ASSESSMENT\n")
            f.write("-" * 80 + "\n")
            f.write(f"Overall Risk Score: {score}/100\n")
            f.write(f"Severity Level: {severity}\n\n")
            
            if score >= 75:
                f.write("⚠️  WARNING: This system has CRITICAL security vulnerabilities!\n")
                f.write("IMMEDIATE ACTION IS REQUIRED TO REDUCE SECURITY RISK\n\n")
            
            f.write("VULNERABILITY SUMMARY\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Vulnerabilities: {report['vulnerabilities']['total']}\n")
            f.write(f"  - Critical: {report['vulnerabilities']['critical']}\n")
            f.write(f"  - High: {report['vulnerabilities']['high']}\n")
            f.write(f"  - Medium: {report['vulnerabilities']['medium']}\n")
            f.write(f"  - Low: {report['vulnerabilities']['low']}\n\n")
            
            f.write("TOP FINDINGS\n")
            f.write("-" * 80 + "\n")
            
            sorted_vulns = sorted(risk['individual_vulnerabilities'], 
                                 key=lambda x: x['cvss_score'], reverse=True)
            
            for i, vuln in enumerate(sorted_vulns[:5], 1):
                f.write(f"\n{i}. {vuln['type']}\n")
                f.write(f"   CVSS Score: {vuln['cvss_score']}\n")
                f.write(f"   Severity: {vuln['severity']}\n")
                f.write(f"   Description: {vuln['description']}\n")
                f.write(f"   Remediation: {vuln['remediation']}\n")
                if vuln.get('cve'):
                    f.write(f"   CVE: {vuln['cve']}\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("For detailed analysis, see vulnerability_report.json\n")
            f.write("For remediation steps, see remediation_report.json\n")

def main():
    parser = argparse.ArgumentParser(
        description='Advanced Security Reconnaissance & Vulnerability Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s example.com
  %(prog)s 192.168.1.1 --protocol https
  %(prog)s example.com -o my_scan -p both
        '''
    )
    
    parser.add_argument('target', help='Target domain or IP address')
    parser.add_argument('-p', '--protocol', choices=['http', 'https', 'both', 'auto'],
                       default='both', help='Protocol to scan (default: both)')
    parser.add_argument('-o', '--output', help='Output directory name', default=None)
    parser.add_argument('--skip-install', action='store_true', help='Skip tool installation prompts')
    parser.add_argument('--install-all', action='store_true', help='Auto-install all missing tools')
    
    args = parser.parse_args()
    
    # Tool management
    tool_manager = ToolManager()
    tool_manager.scan_all_tools()
    
    if tool_manager.missing_tools and not args.skip_install:
        if args.install_all:
            print("\n[*] Auto-installing missing tools...")
            # Iterate over a snapshot to avoid dict size change during iteration
            for tool in list(tool_manager.missing_tools.keys()):
                tool_manager.install_tool(tool)
        else:
            tool_manager.install_missing_tools_interactive()
    
    # Create scanner and run scan
    # Do not skip tool checks in WSL/Kali so installed tools are used
    scanner = AdvancedScanner(args.target, args.protocol, args.output, skip_tool_check=False)
    
    if args.protocol == 'auto':
        scanner.ask_for_protocol()
    
    scanner.run_full_scan()

if __name__ == '__main__':
    main()
