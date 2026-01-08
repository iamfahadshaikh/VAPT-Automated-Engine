"""
Noise Filter - Suppress informational findings and duplicates
Filters based on severity, finding type, and configuration
"""

from typing import List, Dict, Optional, Tuple


class NoiseFilter:
    """Filter out informational and low-priority findings"""
    
    # Informational finding patterns that should be suppressed
    INFO_PATTERNS = [
        "Server: Apache",
        "Server: nginx",
        "X-Powered-By",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "HTTP version",
        "Connection:",
        "Cache-Control",
    ]
    
    # Severity levels and their noise filtering
    SEVERITY_LEVELS = {
        "CRITICAL": 0,
        "HIGH": 1,
        "MEDIUM": 2,
        "LOW": 3,
        "INFO": 4,
    }
    
    @staticmethod
    def should_filter(finding: Dict, min_severity: str = "LOW") -> bool:
        """
        Determine if finding should be filtered out
        
        Args:
            finding: Finding dict with 'severity', 'type', 'title'
            min_severity: Minimum severity level to keep (CRITICAL, HIGH, MEDIUM, LOW, INFO)
            
        Returns:
            True if finding should be filtered out, False if it should be kept
        """
        severity = finding.get("severity", "INFO").upper()
        
        # Check severity level
        severity_level = NoiseFilter.SEVERITY_LEVELS.get(severity, 4)
        min_level = NoiseFilter.SEVERITY_LEVELS.get(min_severity.upper(), 3)
        
        if severity_level > min_level:
            return True
        
        # Check if it's an informational finding pattern
        title = finding.get("title", "").lower()
        for pattern in NoiseFilter.INFO_PATTERNS:
            if pattern.lower() in title:
                if severity == "INFO":
                    return True
        
        return False
    
    @staticmethod
    def filter_findings(findings: List[Dict], min_severity: str = "LOW") -> Tuple[List[Dict], int]:
        """
        Filter findings by severity
        
        Args:
            findings: List of findings
            min_severity: Minimum severity to keep
            
        Returns:
            (filtered_findings, num_filtered)
        """
        filtered = []
        count = 0
        
        for finding in findings:
            if not NoiseFilter.should_filter(finding, min_severity):
                filtered.append(finding)
            else:
                count += 1
        
        return filtered, count
    
    @staticmethod
    def suppress_duplicates(findings: List[Dict]) -> List[Dict]:
        """
        Suppress duplicate findings across tools
        
        Args:
            findings: List of findings
            
        Returns:
            Deduplicated list
        """
        seen = set()
        deduped = []
        
        for finding in findings:
            # Create unique key
            key = (
                finding.get("type", ""),
                finding.get("target", ""),
                finding.get("title", ""),
            )
            
            if key not in seen:
                seen.add(key)
                deduped.append(finding)
        
        return deduped
    
    @staticmethod
    def apply_noise_filter(findings: List[Dict], min_severity: str = "LOW", remove_duplicates: bool = True) -> Dict:
        """
        Apply comprehensive noise filtering
        
        Args:
            findings: List of findings
            min_severity: Minimum severity to keep
            remove_duplicates: Also deduplicate
            
        Returns:
            {
                'filtered': filtered_findings,
                'removed_count': number removed,
                'kept_count': number kept,
                'filter_rate': percentage filtered
            }
        """
        if remove_duplicates:
            findings = NoiseFilter.suppress_duplicates(findings)
        
        filtered, removed = NoiseFilter.filter_findings(findings, min_severity)
        
        return {
            'filtered': filtered,
            'removed_count': removed,
            'kept_count': len(filtered),
            'total_before': len(findings),
            'filter_rate': f"{(removed / max(len(findings), 1)) * 100:.1f}%"
        }

