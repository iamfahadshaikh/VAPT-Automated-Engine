#!/usr/bin/env python3
"""
Deduplicator
Merges identical findings from multiple tools and increases confidence with agreement.
"""

from typing import List, Dict, Tuple
from finding_schema import Finding, FindingCollection, Severity
import hashlib


class FindingDeduplicator:
    """
    Deduplicates findings across multiple tools.
    
    When multiple tools find the same vulnerability:
    - Merge into single finding
    - Track all tools that found it
    - Increase confidence based on tool agreement
    - Keep original tool evidence
    """
    
    def __init__(self):
        self.merged_findings: Dict[str, Finding] = {}  # key: hash, value: merged Finding
    
    def deduplicate(self, collection: FindingCollection) -> FindingCollection:
        """
        Deduplicate findings in a collection.
        
        Args:
            collection: FindingCollection with potential duplicates
        
        Returns:
            New FindingCollection with deduplicated findings
        """
        self.merged_findings = {}
        
        # Group findings by similarity
        for finding in collection.findings:
            key = self._generate_key(finding)
            
            if key in self.merged_findings:
                # Merge with existing
                self._merge_findings(self.merged_findings[key], finding)
            else:
                # First time seeing this finding
                self.merged_findings[key] = finding
        
        # Create new collection with deduplicated findings
        result = FindingCollection(scan_id=collection.scan_id)
        for finding in self.merged_findings.values():
            result.add_finding(finding)
        
        return result
    
    def deduplicate_multiple(self, collections: List[FindingCollection]) -> FindingCollection:
        """
        Deduplicate findings across multiple FindingCollections (from different tools/parsers).
        
        Args:
            collections: List of FindingCollections
        
        Returns:
            Merged FindingCollection
        """
        # Combine all findings
        combined = FindingCollection(scan_id=collections[0].scan_id if collections else None)
        for collection in collections:
            for finding in collection.findings:
                combined.add_finding(finding)
        
        # Deduplicate
        return self.deduplicate(combined)
    
    def _generate_key(self, finding: Finding) -> str:
        """
        Generate unique key for finding deduplication.
        
        Two findings are the same if they have:
        - Same type
        - Same URL
        - Same endpoint
        - Same parameter
        
        Args:
            finding: Finding to generate key for
        
        Returns:
            Hash key as string
        """
        # Normalize values
        finding_type = finding.finding_type.value
        url = finding.url.strip().lower()
        endpoint = (finding.endpoint or "").strip().lower()
        parameter = (finding.parameter or "").strip().lower()
        
        # Create unique key
        key_str = f"{finding_type}|{url}|{endpoint}|{parameter}"
        
        # Return hash
        return hashlib.sha256(key_str.encode()).hexdigest()[:16]
    
    def _merge_findings(self, master: Finding, duplicate: Finding) -> None:
        """
        Merge a duplicate finding into master.
        
        Updates:
        - source_tools list
        - confidence (based on tool agreement)
        - evidence (append)
        - severity (keep highest)
        
        Args:
            master: Master finding to merge into
            duplicate: Duplicate finding to merge
        """
        # Add tool to list if not already there
        if duplicate.source_tool and duplicate.source_tool not in master.source_tools:
            master.source_tools.append(duplicate.source_tool)
        
        # Track merge
        if duplicate.id not in master.merged_from:
            master.merged_from.append(duplicate.id)
        
        # Update confidence based on tool agreement
        # Formula: average confidence increased by number of tools
        old_confidence = master.confidence
        agreement_bonus = min(len(master.source_tools) * 0.05, 0.15)  # Max +0.15 for agreement
        master.confidence = min(
            (old_confidence + duplicate.confidence) / 2 + agreement_bonus,
            0.99  # Cap at 0.99
        )
        
        # Keep highest severity
        if self._severity_value(duplicate.severity) > self._severity_value(master.severity):
            master.severity = duplicate.severity
        
        # Append evidence
        if duplicate.evidence and duplicate.evidence not in master.evidence:
            master.evidence = f"{master.evidence}\n---\n[{duplicate.source_tool}]: {duplicate.evidence}"
        
        # Keep highest exploitability
        if self._exploitability_value(duplicate.exploitability) > self._exploitability_value(master.exploitability):
            master.exploitability = duplicate.exploitability
        
        # Track all payloads
        if duplicate.payload and duplicate.payload != master.payload:
            if not master.payload:
                master.payload = duplicate.payload
            else:
                # Store multiple payloads in evidence
                if duplicate.payload not in master.evidence:
                    master.evidence = f"{master.evidence}\n[Payload from {duplicate.source_tool}]: {duplicate.payload}"
    
    def _severity_value(self, severity: Severity) -> int:
        """Convert severity to numeric value for comparison"""
        severity_map = {
            Severity.CRITICAL: 5,
            Severity.HIGH: 4,
            Severity.MEDIUM: 3,
            Severity.LOW: 2,
            Severity.INFO: 1,
        }
        return severity_map.get(severity, 0)
    
    def _exploitability_value(self, exploitability: str) -> int:
        """Convert exploitability to numeric value for comparison"""
        exploitability_map = {
            'easy': 3,
            'moderate': 2,
            'difficult': 1,
            'unknown': 0,
        }
        return exploitability_map.get(exploitability.lower(), 0)


class DeduplicationReport:
    """Report on deduplication results"""
    
    def __init__(self, original: FindingCollection, deduplicated: FindingCollection):
        self.original = original
        self.deduplicated = deduplicated
    
    @property
    def duplicates_found(self) -> int:
        """Number of duplicate findings removed"""
        return self.original.total_count - self.deduplicated.total_count
    
    @property
    def reduction_percentage(self) -> float:
        """Percentage reduction in findings"""
        if self.original.total_count == 0:
            return 0.0
        return (self.duplicates_found / self.original.total_count) * 100
    
    @property
    def confidence_improvement(self) -> float:
        """Average confidence improvement from merging"""
        if not self.deduplicated.findings:
            return 0.0
        
        avg_confidence = sum(f.confidence for f in self.deduplicated.findings) / len(self.deduplicated.findings)
        return avg_confidence
    
    def print_summary(self):
        """Print human-readable deduplication report"""
        print("\n" + "="*70)
        print("DEDUPLICATION REPORT")
        print("="*70)
        print(f"Original findings: {self.original.total_count}")
        print(f"After deduplication: {self.deduplicated.total_count}")
        print(f"Duplicates removed: {self.duplicates_found}")
        print(f"Reduction: {self.reduction_percentage:.1f}%")
        print(f"Average confidence improvement: {self.confidence_improvement:.2f}")
        print("\nSummary by severity:")
        print(f"  Critical: {self.deduplicated.critical_count}")
        print(f"  High: {self.deduplicated.high_count}")
        print(f"  Medium: {self.deduplicated.medium_count}")
        print(f"  Low: {self.deduplicated.low_count}")
        print(f"  Info: {self.deduplicated.info_count}")
        print("="*70 + "\n")
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'original_count': self.original.total_count,
            'deduplicated_count': self.deduplicated.total_count,
            'duplicates_removed': self.duplicates_found,
            'reduction_percentage': self.reduction_percentage,
            'average_confidence': self.confidence_improvement,
            'severity_breakdown': {
                'critical': self.deduplicated.critical_count,
                'high': self.deduplicated.high_count,
                'medium': self.deduplicated.medium_count,
                'low': self.deduplicated.low_count,
                'info': self.deduplicated.info_count,
            }
        }


# Example usage and testing
if __name__ == "__main__":
    from finding_schema import Finding, FindingType, Severity
    
    # Create test findings
    collection = FindingCollection(scan_id="20260106_100000")
    
    # Same XSS from xsstrike (confidence 0.80)
    f1 = Finding(
        id="XSS-001",
        finding_type=FindingType.XSS,
        url="https://example.com/search?q=test",
        endpoint="/search",
        parameter="q",
        payload="<script>alert(1)</script>",
        evidence="Reflected XSS in parameter q",
        severity=Severity.HIGH,
        confidence=0.80,
        source_tool="xsstrike",
        source_tools=["xsstrike"],
        scan_id="20260106_100000",
    )
    
    # Same XSS from dalfox (confidence 0.85)
    f2 = Finding(
        id="XSS-002",
        finding_type=FindingType.XSS,
        url="https://example.com/search?q=test",
        endpoint="/search",
        parameter="q",
        payload="<img src=x onerror=alert(1)>",
        evidence="Reflected XSS detected by dalfox",
        severity=Severity.HIGH,
        confidence=0.85,
        source_tool="dalfox",
        source_tools=["dalfox"],
        scan_id="20260106_100000",
    )
    
    # Same XSS from xsser (confidence 0.75)
    f3 = Finding(
        id="XSS-003",
        finding_type=FindingType.XSS,
        url="https://example.com/search?q=test",
        endpoint="/search",
        parameter="q",
        payload="';alert(String.fromCharCode(88,83,83))//",
        evidence="XSS vulnerability confirmed by xsser",
        severity=Severity.HIGH,
        confidence=0.75,
        source_tool="xsser",
        source_tools=["xsser"],
        scan_id="20260106_100000",
    )
    
    # Different finding (SQL injection)
    f4 = Finding(
        id="SQLI-001",
        finding_type=FindingType.SQL_INJECTION,
        url="https://example.com/users?id=1",
        endpoint="/users",
        parameter="id",
        payload="1' OR '1'='1",
        evidence="SQL injection vulnerability",
        severity=Severity.CRITICAL,
        confidence=0.90,
        source_tool="sqlmap",
        source_tools=["sqlmap"],
        scan_id="20260106_100000",
    )
    
    # Add all findings
    collection.add_finding(f1)
    collection.add_finding(f2)
    collection.add_finding(f3)
    collection.add_finding(f4)
    
    print("[+] Original findings:")
    for f in collection.findings:
        print(f"  - {f.finding_type.value} on {f.url} (tool: {f.source_tool}, confidence: {f.confidence})")
    
    # Deduplicate
    deduplicator = FindingDeduplicator()
    deduplicated = deduplicator.deduplicate(collection)
    
    print("\n[+] After deduplication:")
    for f in deduplicated.findings:
        print(f"  - {f.finding_type.value} on {f.url} (tools: {f.source_tools}, confidence: {f.confidence:.2f})")
    
    # Report
    report = DeduplicationReport(collection, deduplicated)
    report.print_summary()
