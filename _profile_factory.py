"""
Factory methods to add to TargetProfile class
"""

from typing import TYPE_CHECKING
import re

if TYPE_CHECKING:
    from target_profile import TargetProfile, TargetType, TargetScope


def from_target(cls, target: str, scheme: str = "https") -> "TargetProfile":
    """
    Factory method to create TargetProfile from a target string.
    Simplified creation for common cases.
    
    Args:
        target: Domain, subdomain, or IP
        scheme: http or https (default: https)
    
    Returns:
        TargetProfile instance
    """
    from target_profile import TargetType, TargetScope
    
    # Strip protocol if present
    clean_target = re.sub(r'^https?://', '', target)
    clean_target = clean_target.split('/')[0]  # Remove path
    clean_target = clean_target.split(':')[0]  # Remove port
    
    # Determine target type
    ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    if re.match(ip_pattern, clean_target):
        target_type = TargetType.IP
        host = clean_target
        base_domain = None
    elif '.' in clean_target:
        parts = clean_target.split('.')
        if len(parts) == 2:
            # Root domain (e.g., example.com)
            target_type = TargetType.ROOT_DOMAIN
            host = clean_target
            base_domain = None
        else:
            # Subdomain (e.g., api.example.com)
            target_type = TargetType.SUBDOMAIN
            host = clean_target
            base_domain = '.'.join(parts[-2:])
    else:
        # Single-word domain (treat as root)
        target_type = TargetType.ROOT_DOMAIN
        host = clean_target
        base_domain = None
    
    # Determine port and flags
    is_https = scheme == "https"
    port = 443 if is_https else 80
    is_web_target = True
    
    return cls(
        original_input=target,
        target_type=target_type,
        host=host,
        scheme=scheme,
        port=port,
        base_domain=base_domain,
        scope=TargetScope.SINGLE_HOST,
        resolved_ips=[host] if target_type == TargetType.IP else [],
        is_resolvable=target_type == TargetType.IP,
        is_web_target=is_web_target,
        is_https=is_https,
    )


def get_type(self) -> "TargetType":
    """Alias for target_type for consistency"""
    return self.target_type


def get_runtime_budget(self) -> int:
    """Get runtime budget in seconds based on target type"""
    from target_profile import TargetType
    
    if self.target_type == TargetType.ROOT_DOMAIN:
        return 1800  # 30 minutes for full reconnaissance
    elif self.target_type == TargetType.SUBDOMAIN:
        return 900   # 15 minutes for subdomain scan
    else:  # IP
        return 600   # 10 minutes for IP scan
