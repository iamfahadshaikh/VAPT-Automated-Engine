#!/usr/bin/env python3
"""
Finding Schema and Data Models
Canonical representation of security findings
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import json


class Severity(Enum):
    """Severity levels based on impact"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class FindingType(Enum):
    """Finding categories"""
    XSS = "xss"
    SQL_INJECTION = "sql_injection"
    SSRF = "ssrf"
    RCE = "rce"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    OPEN_REDIRECT = "open_redirect"
    XXE = "xxe"
    CSRF = "csrf"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INFO_DISCLOSURE = "info_disclosure"
    WEAK_CRYPTO = "weak_crypto"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    DNS_ISSUE = "dns_issue"
    SSL_TLS = "ssl_tls"
    DEFAULT_CREDENTIALS = "default_credentials"
    EXPOSED_PANEL = "exposed_panel"
    MISCONFIGURATION = "misconfiguration"
    OUTDATED_SOFTWARE = "outdated_software"
    OTHER = "other"


@dataclass
class Finding:
    """
    Canonical representation of a single security finding.
    This is the fundamental unit of the scanner's output.
    """
    
    # Identity
    id: str                                 # Unique identifier (e.g., "XSS-20260105-001")
    finding_type: FindingType              # Type of finding (xss, sql_injection, etc.)
    
    # Location
    url: str                                # Target URL where finding was discovered
    endpoint: Optional[str] = None         # Specific endpoint (e.g., "/search")
    parameter: Optional[str] = None        # Parameter name if applicable (e.g., "q")
    header: Optional[str] = None           # Header name if applicable
    
    # Content
    payload: Optional[str] = None          # The actual payload used (for context)
    evidence: str = ""                     # Raw proof from tool (output snippet)
    description: str = ""                  # Human-readable description
    
    # Severity & Confidence
    severity: Severity = Severity.MEDIUM   # Impact severity
    confidence: float = 0.5                # Tool confidence (0.0-1.0)
    
    # Source tracking
    source_tool: str = ""                  # Which tool found this ("dalfox", "xsstrike", etc.)
    source_tools: List[str] = field(default_factory=list)  # Tools that confirmed this
    
    # Additional context
    category: str = ""                     # Finding category for organization
    cvss_score: Optional[float] = None    # CVSS score if available (0-10)
    exploitability: str = "unknown"        # easy, moderate, difficult, unknown
    affected_component: str = ""           # Which component is affected
    
    # Remediation
    remediation: str = ""                  # How to fix this
    references: List[str] = field(default_factory=list)  # CVE, CWE, blog posts, etc.
    
    # Metadata
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    scan_id: Optional[str] = None          # Correlation ID from scan
    
    # Deduplication/Correlation
    duplicate_of: Optional[str] = None     # If merged, ID of master finding
    merged_from: List[str] = field(default_factory=list)  # IDs of merged findings
    
    def __post_init__(self):
        """Validate after initialization"""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        if self.cvss_score and not (0.0 <= self.cvss_score <= 10.0):
            raise ValueError("cvss_score must be between 0.0 and 10.0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['finding_type'] = self.finding_type.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Finding':
        """Create Finding from dictionary"""
        data_copy = data.copy()
        data_copy['severity'] = Severity(data_copy['severity'])
        data_copy['finding_type'] = FindingType(data_copy['finding_type'])
        return cls(**data_copy)
    
    def __hash__(self):
        """Make hashable for deduplication"""
        return hash((self.finding_type, self.url, self.endpoint, self.parameter))
    
    def __eq__(self, other):
        """Equality based on finding type and location"""
        if not isinstance(other, Finding):
            return False
        return (self.finding_type == other.finding_type and
                self.url == other.url and
                self.endpoint == other.endpoint and
                self.parameter == other.parameter)


@dataclass
class FindingCollection:
    """Collection of findings with metadata"""
    findings: List[Finding] = field(default_factory=list)
    total_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    scan_id: Optional[str] = None
    
    def add_finding(self, finding: Finding) -> None:
        """Add a finding and update counts"""
        self.findings.append(finding)
        self.total_count += 1
        
        if finding.severity == Severity.CRITICAL:
            self.critical_count += 1
        elif finding.severity == Severity.HIGH:
            self.high_count += 1
        elif finding.severity == Severity.MEDIUM:
            self.medium_count += 1
        elif finding.severity == Severity.LOW:
            self.low_count += 1
        elif finding.severity == Severity.INFO:
            self.info_count += 1
    
    def get_by_severity(self, severity: Severity) -> List[Finding]:
        """Get all findings of a specific severity"""
        return [f for f in self.findings if f.severity == severity]
    
    def get_by_type(self, finding_type: FindingType) -> List[Finding]:
        """Get all findings of a specific type"""
        return [f for f in self.findings if f.finding_type == finding_type]
    
    def get_by_tool(self, tool_name: str) -> List[Finding]:
        """Get all findings from a specific tool"""
        return [f for f in self.findings if tool_name in [f.source_tool] + f.source_tools]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'findings': [f.to_dict() for f in self.findings],
            'summary': {
                'total': self.total_count,
                'critical': self.critical_count,
                'high': self.high_count,
                'medium': self.medium_count,
                'low': self.low_count,
                'info': self.info_count,
            },
            'timestamp': self.timestamp,
            'scan_id': self.scan_id,
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)


# Predefined remediation templates
REMEDIATION_TEMPLATES = {
    FindingType.XSS: {
        'description': 'Cross-Site Scripting (XSS) allows attackers to inject malicious scripts',
        'remediation': 'Implement output encoding, use Content Security Policy (CSP), sanitize user input',
        'references': ['CWE-79', 'OWASP-A03']
    },
    FindingType.SQL_INJECTION: {
        'description': 'SQL Injection allows attackers to manipulate database queries',
        'remediation': 'Use parameterized queries, input validation, least privilege DB accounts',
        'references': ['CWE-89', 'OWASP-A03']
    },
    FindingType.SSRF: {
        'description': 'Server-Side Request Forgery allows attackers to make requests from the server',
        'remediation': 'Validate URLs, use allowlists, disable unnecessary protocols, network segmentation',
        'references': ['CWE-918', 'OWASP-A10']
    },
    FindingType.RCE: {
        'description': 'Remote Code Execution allows attackers to run arbitrary code on the server',
        'remediation': 'Update software immediately, disable dangerous functions, implement WAF, network segmentation',
        'references': ['CWE-94', 'OWASP-A01']
    },
    FindingType.COMMAND_INJECTION: {
        'description': 'Command Injection allows attackers to execute system commands',
        'remediation': 'Avoid shell execution, use safe APIs, input validation, least privilege',
        'references': ['CWE-77', 'OWASP-A03']
    },
    FindingType.PATH_TRAVERSAL: {
        'description': 'Path Traversal allows attackers to access files outside intended directory',
        'remediation': 'Validate paths, use allowlists, canonicalize paths, implement chroot',
        'references': ['CWE-22', 'OWASP-A01']
    },
    FindingType.OPEN_REDIRECT: {
        'description': 'Open Redirect allows attackers to redirect users to malicious sites',
        'remediation': 'Validate redirect destinations, use allowlists, avoid user-controlled redirects',
        'references': ['CWE-601', 'OWASP-A04']
    },
    FindingType.DEFAULT_CREDENTIALS: {
        'description': 'Default credentials allow unauthorized access to systems',
        'remediation': 'Change all default credentials immediately, implement strong password policy',
        'references': ['CWE-798', 'OWASP-A07']
    },
    FindingType.WEAK_CRYPTO: {
        'description': 'Weak cryptography can be broken to compromise security',
        'remediation': 'Use AES-256, TLS 1.2+, SHA-256+, disable deprecated algorithms',
        'references': ['CWE-327', 'OWASP-A02']
    },
    FindingType.OUTDATED_SOFTWARE: {
        'description': 'Outdated software has known vulnerabilities',
        'remediation': 'Update to latest patched version immediately, implement patch management',
        'references': ['CWE-1035', 'OWASP-A06']
    },
}


def get_remediation(finding_type: FindingType) -> Dict[str, Any]:
    """Get remediation template for a finding type"""
    return REMEDIATION_TEMPLATES.get(finding_type, {
        'description': 'Security finding detected',
        'remediation': 'Review and address the identified issue',
        'references': []
    })
