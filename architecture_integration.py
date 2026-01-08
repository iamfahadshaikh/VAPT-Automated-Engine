"""
ARCHITECTURE INTEGRATION LAYER
==============================

This file connects:
- automation_scanner_v2.py (old tool execution)
- target_profile.py (immutable target)
- decision_ledger.py (tool decisions)
- execution_paths.py (root/subdomain/IP flows)
- architecture_guards.py (enforcement)

Non-negotiable rule: Every tool checks ledger before running.
"""

from target_profile import TargetProfile, TargetType, TargetProfileBuilder
from decision_ledger import DecisionLedger, DecisionEngine
from execution_paths import get_executor
from architecture_guards import ArchitectureValidator, ArchitectureViolation


class ArchitectureIntegration:
    """
    Bridges automation_scanner_v2.py to the new architecture.
    
    Old flow (broken):
        parse_input → guess_target_type → run_tools
    
    New flow (correct):
        parse_input → build_profile → build_ledger → get_executor → get_plan → run_tools
    """
    
    @staticmethod
    def create_profile_from_scanner_args(target: str, scheme: str, port: int) -> TargetProfile:
        """
        Convert automation_scanner_v2 args to immutable TargetProfile.
        
        This is the ONLY place that analyzes the raw input.
        After this, no tool may recompute target type or scheme.
        
        Args:
            target: User input (domain, IP, or subdomain)
            scheme: http or https (or None = auto-detect)
            port: Port number (or None = infer from scheme)
        
        Returns:
            Frozen TargetProfile
        """
        # Step 1: Normalize input
        target = target.strip().lower()
        
        # Step 2: Detect target type
        is_ip = _is_ip_address(target)
        is_subdomain = _is_subdomain(target)
        is_root = not (is_ip or is_subdomain)
        
        # Step 3: Normalize scheme and port
        if scheme is None:
            scheme = "https"  # Default
        
        if port is None:
            port = 443 if scheme == "https" else 80
        
        # Step 4: Build profile
        builder = TargetProfileBuilder()
        
        if is_ip:
            builder.with_original_input(target)
            builder.with_target_type(TargetType.IP)
            builder.with_host(target)
            builder.with_resolved_ips([target])
            builder.with_scheme(scheme)
            builder.with_port(port)
        
        elif is_subdomain:
            base_domain = _extract_base_domain(target)
            builder.with_original_input(target)
            builder.with_target_type(TargetType.SUBDOMAIN)
            builder.with_host(target)
            builder.with_base_domain(base_domain)
            builder.with_scheme(scheme)
            builder.with_port(port)
            builder.with_is_web_target(True)  # Assume web
            builder.with_is_https(scheme == "https")
        
        else:  # Root domain
            builder.with_original_input(target)
            builder.with_target_type(TargetType.ROOT_DOMAIN)
            builder.with_host(target)
            builder.with_scheme(scheme)
            builder.with_port(port)
            builder.with_is_web_target(True)  # Assume web
            builder.with_is_https(scheme == "https")
        
        profile = builder.build()
        return profile
    
    @staticmethod
    def build_ledger(profile: TargetProfile) -> DecisionLedger:
        """
        Build decision ledger from profile.
        
        This pre-computes which tools run, based on profile evidence.
        After this, tools check ledger - they don't decide.
        
        Args:
            profile: Immutable TargetProfile
        
        Returns:
            DecisionLedger (read-only, finalized)
        """
        ledger = DecisionEngine.build_ledger(profile)
        return ledger
    
    @staticmethod
    def route_execution(profile: TargetProfile, ledger: DecisionLedger) -> str:
        """
        Determine which execution path to use.
        
        This is the ONLY place that checks target type for routing.
        After this, execution is path-specific.
        
        Args:
            profile: Immutable TargetProfile
            ledger: Finalized DecisionLedger
        
        Returns:
            Path identifier: "root", "subdomain", or "ip"
        """
        if profile.is_root_domain:
            return "root"
        elif profile.is_subdomain:
            return "subdomain"
        elif profile.is_ip:
            return "ip"
        else:
            raise ArchitectureViolation(f"Unknown target type: {profile.target_type}")
    
    @staticmethod
    def validate_architecture(profile: TargetProfile, ledger: DecisionLedger) -> None:
        """
        Validate that profile and ledger are consistent and ready.
        
        Raises ArchitectureViolation if any contract is broken.
        """
        ArchitectureValidator.validate_pre_scan(profile, ledger)
        ArchitectureValidator.validate_execution_plan(profile, ledger)


def _is_ip_address(target: str) -> bool:
    """Check if target is an IP address"""
    import re
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    ipv6_pattern = r'^[\da-f:]+$'
    
    if re.match(ipv4_pattern, target):
        return True
    if re.match(ipv6_pattern, target):
        return True
    
    return False


def _is_subdomain(target: str) -> bool:
    """
    Check if target is a subdomain (not a root domain).
    
    Rules:
    - Must contain exactly 2+ dots (sub.example.com = subdomain)
    - First label must not be 'www' alone
    - Must be resolvable or reasonable
    """
    if target.count('.') < 2:
        return False
    
    # If it's 'example.com' (2 labels), it's root
    # If it's 'sub.example.com' (3+ labels), it's subdomain
    parts = target.split('.')
    
    if len(parts) == 2:
        return False  # Root domain
    else:
        return True   # Subdomain


def _extract_base_domain(subdomain: str) -> str:
    """
    Extract base domain from subdomain.
    
    Examples:
    - api.example.com → example.com
    - app.staging.example.com → staging.example.com (conservative)
    """
    parts = subdomain.split('.')
    
    if len(parts) < 3:
        return subdomain
    
    # Take last 2 parts (domain.tld)
    return '.'.join(parts[-2:])


# Example usage in automation_scanner_v2.py:
#
# OLD (broken):
#     classifier = TargetClassifierBuilder.from_string(target, scheme=protocol)
#     self.context = ScanContext(self.classifier)
#     # Now tools make decisions inline
#
# NEW (correct):
#     profile = ArchitectureIntegration.create_profile_from_scanner_args(
#         target=target,
#         scheme=protocol,
#         port=port
#     )
#     ledger = ArchitectureIntegration.build_ledger(profile)
#     ArchitectureIntegration.validate_architecture(profile, ledger)
#     path = ArchitectureIntegration.route_execution(profile, ledger)
#
#     if path == "root":
#         run_root_domain_scan(profile, ledger)
#     elif path == "subdomain":
#         run_subdomain_scan(profile, ledger)
#     elif path == "ip":
#         run_ip_scan(profile, ledger)
