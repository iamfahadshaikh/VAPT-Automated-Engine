"""
Execution Paths - Completely separate flows for root domain vs subdomain

RULE: Root domain and subdomain never share execution logic.
Not even utilities that might "just skip a few tools".

This prevents the leakage we saw before.
"""

from typing import List, Tuple, Dict
from target_profile import TargetProfile, TargetType
from decision_ledger import DecisionLedger


class RootDomainExecutor:
    """
    Execution path for ROOT DOMAIN targets.
    
    Complete reconnaissance:
    - DNS recon (full)
    - Subdomain enumeration
    - Network scanning
    - Web enumeration
    - Vulnerability scanning
    """
    
    def __init__(self, profile: TargetProfile, ledger: DecisionLedger):
        if profile.target_type != TargetType.ROOT_DOMAIN:
            raise ValueError("RootDomainExecutor only handles ROOT_DOMAIN targets")
        
        self.profile = profile
        self.ledger = ledger
    
    def get_execution_plan(self) -> List[Tuple[str, str, Dict]]:
        """
        Get the execution plan for root domain.
        
        Returns list of (tool_name, command, metadata)
        Only includes tools approved by ledger.
        """
        plan = []
        
        # ============ PHASE 1: DNS RECONNAISSANCE ============
        dns_tools = [
            ("dig_a", f"dig A {self.profile.host} +short", {"timeout": 30, "category": "DNS", "prereqs": set(), "blocking": True}),
            ("dig_ns", f"dig NS {self.profile.host} +short", {"timeout": 30, "category": "DNS", "prereqs": set(), "blocking": True}),
            ("dig_mx", f"dig MX {self.profile.host} +short", {"timeout": 30, "category": "DNS", "prereqs": set(), "blocking": True}),
            ("dnsrecon", f"dnsrecon -d {self.profile.host}", {"timeout": 30, "category": "DNS", "prereqs": set(), "blocking": True}),
        ]
        
        for tool_name, cmd, meta in dns_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 2: SUBDOMAIN ENUMERATION ============
        subdomain_tools = [
            ("findomain", f"findomain -t {self.profile.host} -q", {"timeout": 60, "category": "Subdomains", "prereqs": set(), "blocking": True}),
            ("sublist3r", f"sublist3r -d {self.profile.host} -o /dev/null", {"timeout": 120, "category": "Subdomains", "prereqs": set(), "blocking": True}),
            ("assetfinder", f"assetfinder {self.profile.host}", {"timeout": 60, "category": "Subdomains", "prereqs": set(), "blocking": True}),
        ]
        
        for tool_name, cmd, meta in subdomain_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 3: NETWORK SCANNING ============
        network_tools = [
            ("ping", f"ping -c 1 {self.profile.host}", {"timeout": 10, "category": "Network", "prereqs": set(), "blocking": True}),
            ("nmap_quick", f"nmap -F {self.profile.host}", {"timeout": 300, "category": "Network", "prereqs": set(), "blocking": True}),
            ("nmap_vuln", f"nmap -sV --script vuln {self.profile.host}", {"timeout": 300, "category": "Network", "prereqs": set(), "blocking": True}),
        ]
        
        for tool_name, cmd, meta in network_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 4: WEB DETECTION ============
        web_detection = [
            ("whatweb", f"whatweb {self.profile.url} -a 3", {"timeout": 60, "category": "Web", "prereqs": set(), "blocking": True}),
            ("nikto", f"nikto -h {self.profile.url}", {"timeout": 120, "category": "Web", "prereqs": set(), "blocking": True}),
        ]
        
        for tool_name, cmd, meta in web_detection:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 5: SSL/TLS ============
        tls_tools = [
            ("sslscan", f"sslscan {self.profile.host}", {"timeout": 120, "category": "SSL", "prereqs": set(), "blocking": True}),
            ("testssl", f"testssl.sh {self.profile.url}", {"timeout": 300, "category": "SSL", "prereqs": set(), "blocking": True}),
        ]
        
        for tool_name, cmd, meta in tls_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 6: WEB ENUMERATION ============
        web_enum = [
            ("gobuster", f"gobuster dir -u {self.profile.url} -w /usr/share/wordlists/dirb/common.txt --status-codes-blacklist 403", 
             {"timeout": 9999, "category": "Web", "prereqs": {"whatweb"}, "blocking": False}),
            ("dirsearch", f"dirsearch -u {self.profile.url} -w /usr/share/wordlists/dirb/common.txt", 
             {"timeout": 120, "category": "Web", "prereqs": {"whatweb"}, "blocking": True}),
        ]
        
        for tool_name, cmd, meta in web_enum:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 7: VULNERABILITY SCANNING ============
        vuln_tools = [
            ("dalfox", f"dalfox url {self.profile.url} --silence", 
             {"timeout": 300, "category": "XSS", "prereqs": {"gobuster", "dirsearch"}, "blocking": True}),
            ("xsstrike", f"xsstrike -u {self.profile.url} --crawl", 
             {"timeout": 300, "category": "XSS", "prereqs": {"gobuster"}, "blocking": True}),
            ("sqlmap", f"sqlmap -u {self.profile.url} --batch --crawl=2", 
             {"timeout": 300, "category": "SQLi", "prereqs": {"gobuster"}, "blocking": True}),
            ("xsser", f"xsser -u {self.profile.url}", 
             {"timeout": 300, "category": "XSS", "prereqs": {"gobuster"}, "blocking": True}),
            ("commix", f"commix -u {self.profile.url}", 
             {"timeout": 9999, "category": "Injection", "prereqs": {"gobuster"}, "blocking": False}),
        ]
        
        for tool_name, cmd, meta in vuln_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 8: NUCLEI SCANNING (FORCED ON ALL) ============
        nuclei_tools = [
            ("nuclei_crit", f"nuclei -u {self.profile.url} -tags critical -silent", 
             {"timeout": 9999, "category": "Nuclei", "prereqs": {"whatweb"}, "blocking": False}),
            ("nuclei_high", f"nuclei -u {self.profile.url} -tags high -silent", 
             {"timeout": 9999, "category": "Nuclei", "prereqs": {"whatweb"}, "blocking": False}),
        ]
        
        for tool_name, cmd, meta in nuclei_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        return plan


class SubdomainExecutor:
    """
    Execution path for SUBDOMAIN targets.
    
    Minimal, targeted reconnaissance:
    - DNS A/AAAA only (inherit NS from base)
    - No subdomain enumeration
    - Network scanning (minimal)
    - Web enumeration (if web target)
    - Vulnerability scanning (if evidence)
    
    Never runs full recon like root domain.
    """
    
    def __init__(self, profile: TargetProfile, ledger: DecisionLedger):
        if profile.target_type != TargetType.SUBDOMAIN:
            raise ValueError("SubdomainExecutor only handles SUBDOMAIN targets")
        
        self.profile = profile
        self.ledger = ledger
    
    def get_execution_plan(self) -> List[Tuple[str, str, Dict]]:
        """
        Get the execution plan for subdomain.
        
        Returns list of (tool_name, command, metadata)
        Only includes tools approved by ledger.
        """
        plan = []
        
        # ============ PHASE 1: MINIMAL DNS ============
        dns_tools = [
            ("dig_a", f"dig A {self.profile.host} +short", {"timeout": 30, "category": "DNS", "prereqs": set(), "blocking": True}),
            ("dig_aaaa", f"dig AAAA {self.profile.host} +short", {"timeout": 30, "category": "DNS", "prereqs": set(), "blocking": True}),
        ]
        
        # ENFORCE: Subdomains get ONLY A/AAAA, no NS/MX/full recon
        # This is intentional - subdomains inherit NS from base_domain
        for tool_name, cmd, meta in dns_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        # NO SUBDOMAIN ENUMERATION - inherited from base_domain
        
        # ============ PHASE 2: NETWORK SCANNING (MINIMAL) ============
        network_tools = [
            ("ping", f"ping -c 1 {self.profile.host}", {"timeout": 10, "category": "Network", "prereqs": set(), "blocking": True}),
            ("nmap_quick", f"nmap -F {self.profile.host}", {"timeout": 300, "category": "Network", "prereqs": set(), "blocking": True}),
        ]
        
        for tool_name, cmd, meta in network_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 3: WEB DETECTION ============
        if self.profile.is_web_target:
            web_detection = [
                ("whatweb", f"whatweb {self.profile.url} -a 3", {"timeout": 60, "category": "Web", "prereqs": set(), "blocking": True}),
                ("nikto", f"nikto -h {self.profile.url}", {"timeout": 120, "category": "Web", "prereqs": set(), "blocking": True}),
            ]
            
            for tool_name, cmd, meta in web_detection:
                if self.ledger.allows(tool_name):
                    plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 4: SSL/TLS (IF HTTPS) ============
        if self.profile.is_https:
            tls_tools = [
                ("sslscan", f"sslscan {self.profile.host}", {"timeout": 120, "category": "SSL", "prereqs": set(), "blocking": True}),
            ]
            
            for tool_name, cmd, meta in tls_tools:
                if self.ledger.allows(tool_name):
                    plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 5: WEB ENUMERATION (IF WEB TARGET) ============
        if self.profile.is_web_target:
            web_enum = [
                ("gobuster", f"gobuster dir -u {self.profile.url} -w /usr/share/wordlists/dirb/common.txt --status-codes-blacklist 403", 
                 {"timeout": 9999, "category": "Web", "prereqs": {"whatweb"}, "blocking": False}),
            ]
            
            for tool_name, cmd, meta in web_enum:
                if self.ledger.allows(tool_name):
                    plan.append((tool_name, cmd, meta))
        
        # ============ VULNERABILITY SCANNING (SUBDOMAIN ONLY) ============
        vuln_tools = [
            ("nuclei_crit", f"nuclei -u {self.profile.url} -tags critical -silent", 
             {"timeout": 9999, "category": "Nuclei", "prereqs": {"whatweb"}, "blocking": False}),
            ("nuclei_high", f"nuclei -u {self.profile.url} -tags high -silent", 
             {"timeout": 9999, "category": "Nuclei", "prereqs": {"whatweb"}, "blocking": False}),
        ]
        
        for tool_name, cmd, meta in vuln_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        return plan


class IPExecutor:
    """
    Execution path for IP targets.
    
    Minimal reconnaissance (no DNS, no domain recon):
    - Network scanning
    - Web enumeration (if web port open)
    - SSL/TLS (if HTTPS port open)
    - Vulnerability scanning (if evidence)
    """
    
    def __init__(self, profile: TargetProfile, ledger: DecisionLedger):
        if profile.target_type != TargetType.IP:
            raise ValueError("IPExecutor only handles IP targets")
        
        self.profile = profile
        self.ledger = ledger
    
    def get_execution_plan(self) -> List[Tuple[str, str, Dict]]:
        """
        Get the execution plan for IP.
        
        Returns list of (tool_name, command, metadata)
        Only includes tools approved by ledger.
        """
        plan = []
        
        # NO DNS - IP is already resolved
        
        # ============ PHASE 1: NETWORK SCANNING ============
        network_tools = [
            ("ping", f"ping -c 1 {self.profile.host}", {"timeout": 10, "category": "Network", "prereqs": set(), "blocking": True}),
            ("nmap_quick", f"nmap -F {self.profile.host}", {"timeout": 300, "category": "Network", "prereqs": set(), "blocking": True}),
        ]
        
        for tool_name, cmd, meta in network_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 2: WEB DETECTION (IF WEB) ============
        if self.profile.is_web_target:
            web_detection = [
                ("whatweb", f"whatweb {self.profile.url} -a 3", {"timeout": 60, "category": "Web", "prereqs": set(), "blocking": True}),
            ]
            
            for tool_name, cmd, meta in web_detection:
                if self.ledger.allows(tool_name):
                    plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 3: SSL/TLS (IF HTTPS) ============
        if self.profile.is_https:
            tls_tools = [
                ("sslscan", f"sslscan {self.profile.host}:{self.profile.port}", 
                 {"timeout": 120, "category": "SSL", "prereqs": set(), "blocking": True}),
            ]
            
            for tool_name, cmd, meta in tls_tools:
                if self.ledger.allows(tool_name):
                    plan.append((tool_name, cmd, meta))
        
        # ============ PHASE 4: WEB ENUMERATION ============
        if self.profile.is_web_target:
            web_enum = [
                ("gobuster", f"gobuster dir -u {self.profile.url} -w /usr/share/wordlists/dirb/common.txt --status-codes-blacklist 403", 
                 {"timeout": 9999, "category": "Web", "prereqs": {"whatweb"}, "blocking": False}),
            ]
            
            for tool_name, cmd, meta in web_enum:
                if self.ledger.allows(tool_name):
                    plan.append((tool_name, cmd, meta))
        
        # ============ VULNERABILITY SCANNING (IP ONLY) ============
        vuln_tools = [
            ("nuclei_crit", f"nuclei -u {self.profile.url} -tags critical -silent", 
             {"timeout": 9999, "category": "Nuclei", "prereqs": {"whatweb"}, "blocking": False}),
            ("nuclei_high", f"nuclei -u {self.profile.url} -tags high -silent", 
             {"timeout": 9999, "category": "Nuclei", "prereqs": {"whatweb"}, "blocking": False}),
        ]
        
        for tool_name, cmd, meta in vuln_tools:
            if self.ledger.allows(tool_name):
                plan.append((tool_name, cmd, meta))
        
        return plan


def get_executor(profile: TargetProfile, ledger: DecisionLedger):
    """
    Get the appropriate executor for target type.
    
    This is the ONLY place target type is checked.
    Execution never splits on target type after this point.
    """
    if profile.is_root_domain:
        return RootDomainExecutor(profile, ledger)
    elif profile.is_subdomain:
        return SubdomainExecutor(profile, ledger)
    elif profile.is_ip:
        return IPExecutor(profile, ledger)
    else:
        raise ValueError(f"Unknown target type: {profile.target_type}")
