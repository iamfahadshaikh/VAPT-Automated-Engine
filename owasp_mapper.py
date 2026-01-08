"""
OWASP Category Mapper
Maps security findings to OWASP Top 10 and OWASP API Top 10 categories
"""

import re
from typing import List, Dict, Optional

class OWASPMapper:
    """Map findings to OWASP categories based on vulnerability type"""
    
    # OWASP Top 10 2021 Categories
    OWASP_TOP_10 = {
        "A01": "Broken Access Control",
        "A02": "Cryptographic Failures",
        "A03": "Injection",
        "A04": "Insecure Design",
        "A05": "Security Misconfiguration",
        "A06": "Vulnerable and Outdated Components",
        "A07": "Identification and Authentication Failures",
        "A08": "Software and Data Integrity Failures",
        "A09": "Logging and Monitoring Failures",
        "A10": "Server-Side Request Forgery (SSRF)"
    }
    
    # OWASP API Top 10 2023 Categories
    OWASP_API_TOP_10 = {
        "API1": "Broken Object Level Authorization",
        "API2": "Broken Authentication",
        "API3": "Broken Object Property Level Authorization",
        "API4": "Unrestricted Resource Consumption",
        "API5": "Broken Function Level Authorization",
        "API6": "Unrestricted Access to Sensitive Business Flows",
        "API7": "Server-Side Request Forgery",
        "API8": "Security Misconfiguration",
        "API9": "Improper Inventory Management",
        "API10": "Unsafe Consumption of APIs"
    }
    
    # Keyword mappings to OWASP categories
    KEYWORD_MAP = {
        # XSS related
        "xss|cross.site.scripting|reflected|stored|dom": "A03",
        # SQLi related
        "sql.injection|sqlmap|sql": "A03",
        # SSRF related
        "ssrf|server.side.request": "A10",
        # Command Injection
        "command.injection|os.injection|commix": "A03",
        # Auth issues
        "authentication|auth|login|session|token|jwt": "A07",
        # Crypto issues
        "ssl|tls|certificate|encryption|crypto|weak.cipher|self.signed": "A02",
        # Access Control
        "authorization|access.control|privilege|permission|idor": "A01",
        # Outdated Components
        "outdated|deprecated|vulnerable.version|cve": "A06",
        # Security Config
        "misconfiguration|configuration|config|default": "A05",
        # Design issues
        "insecure.design|design.flaw": "A04",
        # Logging/Monitoring
        "logging|monitoring|audit": "A09",
        # CORS, CSP, Security Headers
        "cors|csp|headers|security.header": "A05",
        # NoSQL Injection
        "nosql": "A03",
    }
    
    @staticmethod
    def map_finding(finding_dict: Dict) -> Dict:
        """
        Map a finding to OWASP category
        
        Args:
            finding_dict: Finding with 'type', 'title', 'description', 'severity'
            
        Returns:
            Finding dict with added 'owasp_category' and 'owasp_code' fields
        """
        finding = finding_dict.copy()
        
        # Combine text fields for keyword matching
        search_text = " ".join([
            finding.get("type", ""),
            finding.get("title", ""),
            finding.get("description", ""),
        ]).lower()
        
        owasp_code = None
        
        # Match against keywords
        for pattern, code in OWASPMapper.KEYWORD_MAP.items():
            if re.search(pattern, search_text):
                owasp_code = code
                break
        
        # Default to misconfiguration if no match
        if not owasp_code:
            owasp_code = "A05"
        
        # Add OWASP info
        finding["owasp_code"] = owasp_code
        finding["owasp_category"] = OWASPMapper.OWASP_TOP_10.get(owasp_code, "Unknown")
        
        return finding
    
    @staticmethod
    def map_findings(findings: List[Dict]) -> List[Dict]:
        """Map a list of findings to OWASP categories"""
        return [OWASPMapper.map_finding(f) for f in findings]
    
    @staticmethod
    def group_by_owasp(findings: List[Dict]) -> Dict:
        """
        Group findings by OWASP category
        
        Returns:
            Dict with OWASP codes as keys and list of findings as values
        """
        grouped = {}
        for finding in findings:
            code = finding.get("owasp_code", "A05")
            if code not in grouped:
                grouped[code] = []
            grouped[code].append(finding)
        
        # Sort by severity within each category
        for code in grouped:
            severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
            grouped[code].sort(
                key=lambda f: severity_order.get(f.get("severity", "INFO"), 5)
            )
        
        return grouped
    
    @staticmethod
    def format_owasp_report(findings: List[Dict]) -> str:
        """Generate OWASP-grouped report"""
        mapped = OWASPMapper.map_findings(findings)
        grouped = OWASPMapper.group_by_owasp(mapped)
        
        report = "OWASP TOP 10 FINDINGS SUMMARY\n"
        report += "=" * 70 + "\n\n"
        
        for code in sorted(grouped.keys()):
            category = OWASPMapper.OWASP_TOP_10.get(code, "Unknown")
            findings_list = grouped[code]
            
            report += f"{code}: {category}\n"
            report += f"  Total: {len(findings_list)} findings\n"
            
            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
                count = len([f for f in findings_list if f.get("severity") == severity])
                if count > 0:
                    report += f"    {severity}: {count}\n"
            
            report += "\n"
        
        return report
