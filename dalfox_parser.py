#!/usr/bin/env python3
"""
Dalfox Output Parser
Extracts XSS findings from dalfox JSON output
"""

import json
import re
from typing import List, Optional
from urllib.parse import urlparse
from finding_schema import Finding, FindingType, Severity, FindingCollection, get_remediation


class DalfoxParser:
    """
    Parse dalfox output into canonical Finding objects.
    
    Dalfox outputs JSON with structure:
    {
        "url": "...",
        "infoList": [
            {
                "type": "reflected-xss" | "stored-xss" | "dom-xss",
                "poc": "...",
                "param": "parameter_name",
                "severity": "high" | "medium" | "low",
                "message": "description"
            }
        ]
    }
    """
    
    def __init__(self, scan_id: Optional[str] = None):
        self.scan_id = scan_id
        self.findings = FindingCollection(scan_id=scan_id)
        self.finding_counter = 0
    
    def parse(self, dalfox_output: str) -> FindingCollection:
        """
        Parse dalfox JSON output and return FindingCollection.
        
        Args:
            dalfox_output: JSON string from dalfox
        
        Returns:
            FindingCollection with extracted findings
        """
        try:
            data = json.loads(dalfox_output)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse dalfox JSON: {e}")
            return self.findings
        
        # Extract base URL
        base_url = data.get('url', '')
        if not base_url:
            print("[WARN] No URL found in dalfox output")
            return self.findings
        
        # Parse target URL to extract components
        parsed_url = urlparse(base_url)
        endpoint = parsed_url.path or "/"
        
        # Extract findings
        info_list = data.get('infoList', [])
        if not info_list:
            print("[INFO] No vulnerabilities found in dalfox output")
            return self.findings
        
        for idx, vuln in enumerate(info_list):
            finding = self._parse_vulnerability(vuln, base_url, endpoint, idx)
            if finding:
                self.findings.add_finding(finding)
        
        return self.findings
    
    def _parse_vulnerability(self, vuln: dict, base_url: str, endpoint: str, idx: int) -> Optional[Finding]:
        """
        Convert a single dalfox vulnerability to a Finding.
        
        Args:
            vuln: Single vulnerability dict from dalfox
            base_url: Base URL being scanned
            endpoint: Endpoint path
            idx: Index for ID generation
        
        Returns:
            Finding object or None if invalid
        """
        try:
            # Extract vulnerability type
            vuln_type = vuln.get('type', 'xss').lower()
            finding_type = self._map_vuln_type(vuln_type)
            
            # Extract severity
            severity = self._map_severity(vuln.get('severity', 'medium').lower())
            
            # Extract parameter
            parameter = vuln.get('param', '')
            
            # Extract payload/POC
            payload = vuln.get('poc', '')
            
            # Extract message
            message = vuln.get('message', '')
            
            # Build endpoint with parameter
            full_endpoint = endpoint
            if parameter:
                full_endpoint = f"{endpoint}?{parameter}=..."
            
            # Generate unique ID
            self.finding_counter += 1
            finding_id = f"XSS-{self.scan_id.split('_')[0] if self.scan_id else 'UNKNOWN'}-{self.finding_counter:03d}"
            
            # Create Finding
            finding = Finding(
                id=finding_id,
                finding_type=finding_type,
                url=base_url,
                endpoint=endpoint,
                parameter=parameter,
                payload=payload,
                evidence=message,
                description=f"{self._describe_vuln_type(vuln_type)}: {message}",
                severity=severity,
                confidence=self._calculate_confidence(vuln_type),
                source_tool="dalfox",
                source_tools=["dalfox"],
                category="Input Validation - XSS",
                exploitability=self._map_exploitability(vuln_type),
                remediation=get_remediation(FindingType.XSS).get('remediation', ''),
                references=get_remediation(FindingType.XSS).get('references', []),
                scan_id=self.scan_id,
            )
            
            return finding
        
        except Exception as e:
            print(f"[ERROR] Failed to parse dalfox vulnerability {idx}: {e}")
            return None
    
    def _map_vuln_type(self, dalfox_type: str) -> FindingType:
        """Map dalfox vulnerability type to FindingType enum"""
        type_map = {
            'reflected-xss': FindingType.XSS,
            'stored-xss': FindingType.XSS,
            'dom-xss': FindingType.XSS,
            'xss': FindingType.XSS,
        }
        return type_map.get(dalfox_type, FindingType.XSS)
    
    def _describe_vuln_type(self, dalfox_type: str) -> str:
        """Get human-readable description of vulnerability type"""
        descriptions = {
            'reflected-xss': 'Reflected Cross-Site Scripting',
            'stored-xss': 'Stored Cross-Site Scripting',
            'dom-xss': 'DOM-based Cross-Site Scripting',
            'xss': 'Cross-Site Scripting',
        }
        return descriptions.get(dalfox_type, 'XSS Vulnerability')
    
    def _map_severity(self, severity_str: str) -> Severity:
        """Map dalfox severity to Severity enum"""
        severity_map = {
            'critical': Severity.CRITICAL,
            'high': Severity.HIGH,
            'medium': Severity.MEDIUM,
            'low': Severity.LOW,
            'info': Severity.INFO,
        }
        return severity_map.get(severity_str.lower(), Severity.MEDIUM)
    
    def _calculate_confidence(self, vuln_type: str) -> float:
        """
        Calculate confidence based on vulnerability type.
        
        Different XSS types have different confirmation levels:
        - Reflected: 0.85 (usually confirmed)
        - Stored: 0.95 (almost always confirmed)
        - DOM: 0.80 (DOM-based are harder to confirm)
        """
        confidence_map = {
            'reflected-xss': 0.85,
            'stored-xss': 0.95,
            'dom-xss': 0.80,
            'xss': 0.80,
        }
        return confidence_map.get(vuln_type.lower(), 0.75)
    
    def _map_exploitability(self, vuln_type: str) -> str:
        """Determine exploitability level"""
        if 'reflected' in vuln_type:
            return 'easy'  # Easy to exploit (just need user click)
        elif 'stored' in vuln_type:
            return 'moderate'  # Depends on where stored
        elif 'dom' in vuln_type:
            return 'moderate'  # Client-side execution needed
        else:
            return 'unknown'
    
    def parse_file(self, filepath: str) -> FindingCollection:
        """
        Parse dalfox output from file.
        
        Args:
            filepath: Path to dalfox JSON output file
        
        Returns:
            FindingCollection
        """
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            return self.parse(content)
        except FileNotFoundError:
            print(f"[ERROR] File not found: {filepath}")
            return self.findings
        except Exception as e:
            print(f"[ERROR] Failed to read file {filepath}: {e}")
            return self.findings


class DalfoxOutputProcessor:
    """
    Process raw dalfox output (may contain STDERR, warnings, etc.)
    Extract JSON section if present.
    """
    
    @staticmethod
    def extract_json(raw_output: str) -> Optional[str]:
        """
        Extract JSON from raw dalfox output.
        Dalfox mixes colored output with JSON, this extracts just the JSON.
        
        Args:
            raw_output: Raw stdout/stderr from dalfox
        
        Returns:
            JSON string or None
        """
        # Remove ANSI color codes
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        clean_output = ansi_escape.sub('', raw_output)
        
        # Try to find JSON object
        # Look for lines that start with { and end with }
        lines = clean_output.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip().startswith('{'):
                # Found potential JSON start
                # Try to parse from here
                potential_json = '\n'.join(lines[i:])
                
                # Find the closing brace
                brace_count = 0
                end_idx = 0
                for j, char in enumerate(potential_json):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = j + 1
                            break
                
                if end_idx > 0:
                    json_str = potential_json[:end_idx]
                    try:
                        json.loads(json_str)
                        return json_str
                    except json.JSONDecodeError:
                        continue
        
        # If no JSON object found, try the entire output
        try:
            json.loads(clean_output)
            return clean_output
        except json.JSONDecodeError:
            return None


# Example usage and testing
if __name__ == "__main__":
    # Test with example dalfox output
    example_output = """
    {
        "url": "https://example.com/search?q=test",
        "infoList": [
            {
                "type": "reflected-xss",
                "param": "q",
                "poc": "<script>alert('xss')</script>",
                "severity": "high",
                "message": "XSS found in query parameter 'q'"
            },
            {
                "type": "stored-xss",
                "param": "comment",
                "poc": "\\\"><script>alert('stored')</script>",
                "severity": "critical",
                "message": "Stored XSS in comment field"
            }
        ]
    }
    """
    
    parser = DalfoxParser(scan_id="20260105_143022")
    findings = parser.parse(example_output)
    
    print(f"\n[+] Found {findings.total_count} vulnerabilities:")
    print(f"    Critical: {findings.critical_count}")
    print(f"    High: {findings.high_count}")
    print(f"    Medium: {findings.medium_count}")
    print(f"    Low: {findings.low_count}")
    
    print("\n[+] Findings:")
    for finding in findings.findings:
        print(f"\n  ID: {finding.id}")
        print(f"  Type: {finding.finding_type.value}")
        print(f"  URL: {finding.url}")
        print(f"  Parameter: {finding.parameter}")
        print(f"  Severity: {finding.severity.value}")
        print(f"  Confidence: {finding.confidence}")
        print(f"  Evidence: {finding.evidence}")
