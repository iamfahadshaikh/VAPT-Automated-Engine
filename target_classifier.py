#!/usr/bin/env python3
"""
Target Classifier - The Single Source of Truth for Target Info

Everything downstream depends on this being correct and immutable.
If this gets it wrong, the entire scan is compromised.
"""

import re
import ipaddress
from dataclasses import dataclass
from typing import Optional, List, Literal
from enum import Enum


class TargetType(Enum):
    """Valid target types"""
    IP_ADDRESS = "ip_address"
    ROOT_DOMAIN = "root_domain"
    SUBDOMAIN = "subdomain"
    MULTI_LEVEL_SUBDOMAIN = "multi_level_subdomain"


class TargetScope(Enum):
    """What scope of scanning is appropriate"""
    SINGLE_HOST = "single_host"  # IP or specific subdomain
    DOMAIN_TREE = "domain_tree"  # Root domain + all subdomains


@dataclass(frozen=True)
class TargetClassifier:
    """
    Immutable classification of the target.
    
    Once created, cannot be modified.
    This is the single source of truth for target info.
    
    Examples:
        IP: "1.1.1.1" → type=IP_ADDRESS, scope=SINGLE_HOST
        Root: "google.com" → type=ROOT_DOMAIN, scope=DOMAIN_TREE
        Sub: "mail.google.com" → type=SUBDOMAIN, scope=SINGLE_HOST
        Multi: "api.v2.google.com" → type=MULTI_LEVEL_SUBDOMAIN, scope=SINGLE_HOST
    """
    
    # Normalized input
    original_input: str
    scheme: str  # http | https
    host: str    # normalized (lowercase)
    port: int    # 80, 443, 8080, etc
    
    # Classification
    target_type: TargetType
    scope: TargetScope
    
    # Derived (computed once)
    base_domain: Optional[str]        # "google.com" for subdomains
    root_domain: Optional[str]        # Same as base_domain for root, None for IP
    is_ip: bool
    ip_obj: Optional[ipaddress.ip_address]  # Parsed IP if is_ip=True
    
    # Subdomain tracking
    subdomain_levels: int              # 1 = root, 2 = sub.root, 3 = api.v2.root
    parent_domain: Optional[str]       # Domain to use for inherited scans
    
    def __str__(self) -> str:
        """Human-readable representation"""
        if self.is_ip:
            return f"{self.scheme}://{self.host}:{self.port} [IP]"
        elif self.target_type == TargetType.ROOT_DOMAIN:
            return f"{self.scheme}://{self.host}:{self.port} [ROOT_DOMAIN]"
        else:
            return f"{self.scheme}://{self.host}:{self.port} [SUBDOMAIN] (base={self.base_domain})"
    
    def __repr__(self) -> str:
        return f"TargetClassifier({self})"


class TargetClassifierBuilder:
    """
    Build and validate a TargetClassifier.
    
    Raises ValueError if input is invalid.
    """
    
    @staticmethod
    def from_string(input_str: str, scheme: str = "https", port: Optional[int] = None) -> TargetClassifier:
        """
        Parse a target string and classify it.
        
        Args:
            input_str: "google.com", "1.1.1.1", "mail.google.com", "api.v2.google.com"
            scheme: "http" or "https" (default: https)
            port: Override port (default: 80 for http, 443 for https)
        
        Returns:
            TargetClassifier: Immutable classification
        
        Raises:
            ValueError: If input is invalid or missing
        """
        
        # Validate input
        if not input_str or not isinstance(input_str, str):
            raise ValueError(f"Target must be non-empty string, got: {repr(input_str)}")
        
        input_str = input_str.strip()
        
        if not input_str:
            raise ValueError("Target cannot be empty after stripping")
        
        # Normalize scheme
        if scheme not in ["http", "https", "both"]:
            raise ValueError(f"Invalid scheme: {scheme}. Must be 'http' or 'https'")
        
        if scheme == "both":
            scheme = "https"  # Default to https for "both"
        
        # Determine default port
        if port is None:
            port = 443 if scheme == "https" else 80
        elif not (1 <= port <= 65535):
            raise ValueError(f"Port must be 1-65535, got: {port}")
        
        # Normalize host (lowercase, strip whitespace)
        host = input_str.lower().strip()
        
        # Check if it's an IP address
        is_ip = TargetClassifierBuilder._is_ip(host)
        ip_obj = None
        
        if is_ip:
            try:
                ip_obj = ipaddress.ip_address(host)
            except ValueError:
                raise ValueError(f"Invalid IP address: {host}")
            
            return TargetClassifier(
                original_input=input_str,
                scheme=scheme,
                host=host,
                port=port,
                target_type=TargetType.IP_ADDRESS,
                scope=TargetScope.SINGLE_HOST,
                base_domain=None,
                root_domain=None,
                is_ip=True,
                ip_obj=ip_obj,
                subdomain_levels=0,
                parent_domain=None
            )
        
        # It's a domain - parse it
        if not TargetClassifierBuilder._is_valid_domain(host):
            raise ValueError(f"Invalid domain: {host}")
        
        # Count parts
        parts = host.split('.')
        
        if len(parts) < 2:
            raise ValueError(f"Domain must have at least 2 parts (e.g., google.com), got: {host}")
        
        # Classify
        if len(parts) == 2:
            # Root domain (e.g., google.com)
            return TargetClassifier(
                original_input=input_str,
                scheme=scheme,
                host=host,
                port=port,
                target_type=TargetType.ROOT_DOMAIN,
                scope=TargetScope.DOMAIN_TREE,  # Can enumerate subdomains
                base_domain=host,
                root_domain=host,
                is_ip=False,
                ip_obj=None,
                subdomain_levels=2,
                parent_domain=None
            )
        
        elif len(parts) == 3:
            # Subdomain (e.g., mail.google.com)
            base_domain = '.'.join(parts[-2:])
            return TargetClassifier(
                original_input=input_str,
                scheme=scheme,
                host=host,
                port=port,
                target_type=TargetType.SUBDOMAIN,
                scope=TargetScope.SINGLE_HOST,  # Single host only, no subdomain enum
                base_domain=base_domain,
                root_domain=base_domain,
                is_ip=False,
                ip_obj=None,
                subdomain_levels=3,
                parent_domain=base_domain
            )
        
        else:
            # Multi-level subdomain (e.g., api.v2.google.com)
            base_domain = '.'.join(parts[-2:])
            return TargetClassifier(
                original_input=input_str,
                scheme=scheme,
                host=host,
                port=port,
                target_type=TargetType.MULTI_LEVEL_SUBDOMAIN,
                scope=TargetScope.SINGLE_HOST,
                base_domain=base_domain,
                root_domain=base_domain,
                is_ip=False,
                ip_obj=None,
                subdomain_levels=len(parts),
                parent_domain=base_domain
            )
    
    @staticmethod
    def _is_ip(value: str) -> bool:
        """Check if value is an IP address"""
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def _is_valid_domain(value: str) -> bool:
        """
        Check if value is a valid domain.
        
        Regex matches:
        - Lowercase letters, numbers, hyphens
        - Dots as separators
        - No leading/trailing dots
        - Each label 1-63 characters
        """
        if not value or value.startswith('.') or value.endswith('.'):
            return False
        
        # Pattern: labels separated by dots, each label valid
        pattern = r'^(?!-)[a-z0-9.-]{1,253}(?<!-)$'
        
        if not re.match(pattern, value):
            return False
        
        # Check each label
        labels = value.split('.')
        for label in labels:
            if not label or len(label) > 63:
                return False
            if label.startswith('-') or label.endswith('-'):
                return False
        
        return True


class ScanContext:
    """
    Immutable context for a scan session.
    
    Carries:
    - Target classification (IMMUTABLE)
    - Detection results (mutable, added as tools run)
    - Scan state (what was actually scanned)
    - Decision results (what tools should run)
    """
    
    def __init__(self, classifier: TargetClassifier):
        self.classifier: TargetClassifier = classifier
        self.detection_results: dict = {}  # whatweb, nmap results, etc
        self.scanned_phases: set = set()   # {"DNS", "PORT_SCAN", "TECH_DETECT"}
        self.decisions: dict = {}          # {"run_wordpress": False, "run_xss": True}
    
    def __str__(self) -> str:
        return f"ScanContext({self.classifier})"
    
    def should_run_dns(self) -> bool:
        """Should DNS recon run?"""
        if self.classifier.is_ip:
            return False  # IP → skip DNS
        if self.classifier.target_type == TargetType.SUBDOMAIN:
            return False  # Subdomain → skip DNS recon (just A/AAAA)
        if self.classifier.target_type == TargetType.MULTI_LEVEL_SUBDOMAIN:
            return False  # Deep subdomain → skip
        return True  # Root domain → yes
    
    def should_run_subdomain_enum(self) -> bool:
        """Should subdomain enumeration run?"""
        if self.classifier.is_ip:
            return False
        if self.classifier.target_type == TargetType.ROOT_DOMAIN:
            return True  # Root domain → yes
        return False  # Subdomain/Multi → no
    
    def should_run_port_scan(self) -> bool:
        """Should port scanning run?"""
        return not self.classifier.is_ip or True  # Run for everything initially
    
    def should_run_tls_check(self) -> bool:
        """Should TLS/SSL tests run?"""
        return self.classifier.scheme == "https" or self.classifier.port in [443, 8443]
    
    def should_run_wordpress_tools(self) -> bool:
        """Should WordPress-specific tools run?"""
        tech_stack = self.detection_results.get('tech_stack', {})
        return 'wordpress' in str(tech_stack).lower()
    
    def should_run_xss_tools(self) -> bool:
        """Should XSS testing run?"""
        # Only if we detected reflection or GET parameters
        reflection_detected = self.detection_results.get('has_reflection', False)
        has_params = self.detection_results.get('has_parameters', False)
        return reflection_detected or has_params
    
    def should_run_sqlmap(self) -> bool:
        """Should SQLMap run?"""
        # Only if parameters detected
        return self.detection_results.get('has_parameters', False)


# Example usage / testing
if __name__ == '__main__':
    test_cases = [
        "google.com",
        "mail.google.com",
        "api.v2.google.com",
        "1.1.1.1",
        "127.0.0.1",
        "invalid..domain",  # Should fail
        "sub.domain.co.uk",  # Multi-level
    ]
    
    print("="*70)
    print("TARGET CLASSIFIER - TEST CASES")
    print("="*70)
    
    for test in test_cases:
        try:
            classifier = TargetClassifierBuilder.from_string(test)
            context = ScanContext(classifier)
            
            print(f"\n✓ {test}")
            print(f"  Type: {classifier.target_type.value}")
            print(f"  Scope: {classifier.scope.value}")
            print(f"  Base domain: {classifier.base_domain}")
            print(f"  Run DNS? {context.should_run_dns()}")
            print(f"  Run subdomain enum? {context.should_run_subdomain_enum()}")
            print(f"  Run TLS? {context.should_run_tls_check()}")
        
        except ValueError as e:
            print(f"\n✗ {test}")
            print(f"  Error: {e}")
    
    print("\n" + "="*70)
