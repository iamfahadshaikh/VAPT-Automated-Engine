#!/usr/bin/env python3
"""
Risk Engine
Calculates security risk from findings and makes deployment decisions.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from finding_schema import Finding, FindingCollection, Severity, FindingType
import json


@dataclass
class RiskScore:
    """Represents overall risk assessment"""
    overall_score: float           # 0-100 overall risk
    critical_risk: float           # Contribution from critical findings
    high_risk: float               # Contribution from high findings
    medium_risk: float             # Contribution from medium findings
    low_risk: float                # Contribution from low findings
    decision: str                  # PASS or FAIL
    threshold: float               # Threshold used for decision
    reason: str                    # Human-readable reason
    top_findings: List[Finding]    # Top 5 most critical findings
    
    def to_dict(self) -> dict:
        return {
            'overall_score': round(self.overall_score, 2),
            'critical_risk': round(self.critical_risk, 2),
            'high_risk': round(self.high_risk, 2),
            'medium_risk': round(self.medium_risk, 2),
            'low_risk': round(self.low_risk, 2),
            'decision': self.decision,
            'threshold': self.threshold,
            'reason': self.reason,
            'top_findings_count': len(self.top_findings),
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def print_summary(self):
        """Print human-readable risk summary"""
        print("\n" + "="*70)
        print("RISK ASSESSMENT")
        print("="*70)
        print(f"Overall Risk Score: {self.overall_score:.1f}/100")
        print(f"Decision: {self.decision}")
        print(f"Threshold: {self.threshold}/100")
        if self.decision == "FAIL":
            print(f"Status: ⛔ DEPLOYMENT BLOCKED")
        else:
            print(f"Status: ✅ DEPLOYMENT ALLOWED")
        print()
        print("Risk Breakdown:")
        print(f"  Critical findings: {self.critical_risk:.1f} points")
        print(f"  High findings: {self.high_risk:.1f} points")
        print(f"  Medium findings: {self.medium_risk:.1f} points")
        print(f"  Low findings: {self.low_risk:.1f} points")
        print()
        print(f"Reason: {self.reason}")
        print()
        if self.top_findings:
            print("Top Critical Findings:")
            for i, finding in enumerate(self.top_findings[:5], 1):
                print(f"  {i}. [{finding.severity.value}] {finding.finding_type.value.upper()}")
                print(f"     URL: {finding.url}")
                if finding.parameter:
                    print(f"     Parameter: {finding.parameter}")
                print(f"     Confidence: {finding.confidence:.0%}")
                print(f"     Tools: {', '.join(finding.source_tools)}")
        print("="*70 + "\n")


class RiskEngine:
    """
    Calculate security risk from findings and make deployment decisions.
    
    Risk scoring incorporates:
    - Severity of findings
    - Confidence of each tool
    - Number of tools that confirmed finding
    - Type of vulnerability
    - Exploitability
    """
    
    # Risk weights by severity
    SEVERITY_WEIGHTS = {
        Severity.CRITICAL: 25.0,
        Severity.HIGH: 15.0,
        Severity.MEDIUM: 8.0,
        Severity.LOW: 3.0,
        Severity.INFO: 1.0,
    }
    
    # Risk multipliers by finding type
    TYPE_MULTIPLIERS = {
        FindingType.RCE: 2.0,                           # Most critical
        FindingType.SQL_INJECTION: 1.8,
        FindingType.COMMAND_INJECTION: 1.8,
        FindingType.XXE: 1.6,
        FindingType.SSRF: 1.4,
        FindingType.PATH_TRAVERSAL: 1.3,
        FindingType.XSS: 1.2,                           # Common but less critical
        FindingType.CSRF: 1.1,
        FindingType.OPEN_REDIRECT: 1.0,
        FindingType.WEAK_CRYPTO: 1.3,
        FindingType.DEFAULT_CREDENTIALS: 1.5,
        FindingType.EXPOSED_PANEL: 1.4,
        FindingType.MISCONFIGURATION: 1.2,
        FindingType.OUTDATED_SOFTWARE: 1.4,
    }
    
    # Exploitability multipliers
    EXPLOITABILITY_MULTIPLIERS = {
        'easy': 1.5,
        'moderate': 1.0,
        'difficult': 0.7,
        'unknown': 0.5,
    }
    
    def __init__(self, threshold: float = 50.0):
        """
        Initialize risk engine.
        
        Args:
            threshold: Risk score threshold for FAIL decision (0-100, default 50)
        """
        if not 0 <= threshold <= 100:
            raise ValueError("threshold must be between 0 and 100")
        self.threshold = threshold
    
    def calculate(self, collection: FindingCollection) -> RiskScore:
        """
        Calculate overall risk from findings.
        
        Args:
            collection: FindingCollection to score
        
        Returns:
            RiskScore with decision
        """
        if not collection.findings:
            return RiskScore(
                overall_score=0.0,
                critical_risk=0.0,
                high_risk=0.0,
                medium_risk=0.0,
                low_risk=0.0,
                decision="PASS",
                threshold=self.threshold,
                reason="No vulnerabilities found",
                top_findings=[]
            )
        
        # Calculate risk from each severity level
        critical_risk = self._calculate_severity_risk(collection, Severity.CRITICAL)
        high_risk = self._calculate_severity_risk(collection, Severity.HIGH)
        medium_risk = self._calculate_severity_risk(collection, Severity.MEDIUM)
        low_risk = self._calculate_severity_risk(collection, Severity.LOW)
        
        # Total risk (capped at 100)
        overall_score = min(critical_risk + high_risk + medium_risk + low_risk, 100.0)
        
        # Get top findings
        top_findings = self._get_top_findings(collection, 5)
        
        # Make decision
        decision = "FAIL" if overall_score >= self.threshold else "PASS"
        
        # Build reason
        reason = self._build_reason(overall_score, decision, collection)
        
        return RiskScore(
            overall_score=overall_score,
            critical_risk=critical_risk,
            high_risk=high_risk,
            medium_risk=medium_risk,
            low_risk=low_risk,
            decision=decision,
            threshold=self.threshold,
            reason=reason,
            top_findings=top_findings,
        )
    
    def _calculate_severity_risk(self, collection: FindingCollection, severity: Severity) -> float:
        """
        Calculate risk from findings of a specific severity.
        
        Formula:
        risk = Σ (severity_weight × confidence × type_multiplier × exploitability_multiplier)
        """
        findings = collection.get_by_severity(severity)
        if not findings:
            return 0.0
        
        total_risk = 0.0
        for finding in findings:
            # Base weight for severity
            base_weight = self.SEVERITY_WEIGHTS.get(severity, 0.0)
            
            # Type multiplier
            type_multiplier = self.TYPE_MULTIPLIERS.get(finding.finding_type, 1.0)
            
            # Exploitability multiplier
            exploitability_multiplier = self.EXPLOITABILITY_MULTIPLIERS.get(
                finding.exploitability.lower(), 0.5
            )
            
            # Tool agreement bonus (more tools = more confidence)
            tool_agreement_bonus = min(len(finding.source_tools) * 0.1, 0.3)
            
            # Calculate individual finding risk
            finding_risk = (
                base_weight *
                finding.confidence *
                type_multiplier *
                exploitability_multiplier *
                (1.0 + tool_agreement_bonus)
            )
            
            total_risk += finding_risk
        
        return min(total_risk, 50.0)  # Cap individual severity contribution
    
    def _get_top_findings(self, collection: FindingCollection, limit: int = 5) -> List[Finding]:
        """Get top N findings sorted by risk"""
        findings_with_score = []
        
        for finding in collection.findings:
            score = self._calculate_finding_risk(finding)
            findings_with_score.append((score, finding))
        
        # Sort by score descending
        findings_with_score.sort(key=lambda x: x[0], reverse=True)
        
        # Return top N findings
        return [finding for _, finding in findings_with_score[:limit]]
    
    def _calculate_finding_risk(self, finding: Finding) -> float:
        """Calculate individual finding risk score"""
        base_weight = self.SEVERITY_WEIGHTS.get(finding.severity, 0.0)
        type_multiplier = self.TYPE_MULTIPLIERS.get(finding.finding_type, 1.0)
        exploitability_multiplier = self.EXPLOITABILITY_MULTIPLIERS.get(
            finding.exploitability.lower(), 0.5
        )
        tool_agreement_bonus = min(len(finding.source_tools) * 0.1, 0.3)
        
        return (
            base_weight *
            finding.confidence *
            type_multiplier *
            exploitability_multiplier *
            (1.0 + tool_agreement_bonus)
        )
    
    def _build_reason(self, score: float, decision: str, collection: FindingCollection) -> str:
        """Build human-readable decision reason"""
        reasons = []
        
        if collection.critical_count > 0:
            reasons.append(f"{collection.critical_count} CRITICAL finding{'s' if collection.critical_count > 1 else ''}")
        if collection.high_count > 0:
            reasons.append(f"{collection.high_count} HIGH finding{'s' if collection.high_count > 1 else ''}")
        if collection.medium_count > 0:
            reasons.append(f"{collection.medium_count} MEDIUM finding{'s' if collection.medium_count > 1 else ''}")
        
        if not reasons:
            return "No critical vulnerabilities detected"
        
        reason_str = ", ".join(reasons)
        
        if decision == "FAIL":
            return f"Risk score {score:.0f} exceeds threshold {self.threshold}. Found: {reason_str}"
        else:
            return f"Risk score {score:.0f} is below threshold {self.threshold}. Found: {reason_str}" if reasons else "No critical vulnerabilities"


# Example usage and testing
if __name__ == "__main__":
    from finding_schema import Finding, FindingType, Severity
    
    # Create test findings
    collection = FindingCollection(scan_id="20260106_100000")
    
    # Critical RCE finding (from 2 tools)
    rce = Finding(
        id="RCE-001",
        finding_type=FindingType.RCE,
        url="https://example.com/admin",
        endpoint="/admin",
        severity=Severity.CRITICAL,
        confidence=0.95,
        source_tool="nuclei",
        source_tools=["nuclei", "metasploit"],
        exploitability="easy",
        evidence="Remote code execution confirmed",
        scan_id="20260106_100000",
    )
    
    # High SQL injection
    sqli = Finding(
        id="SQLI-001",
        finding_type=FindingType.SQL_INJECTION,
        url="https://example.com/users?id=1",
        endpoint="/users",
        parameter="id",
        severity=Severity.HIGH,
        confidence=0.85,
        source_tool="sqlmap",
        source_tools=["sqlmap"],
        exploitability="moderate",
        evidence="SQL injection in id parameter",
        scan_id="20260106_100000",
    )
    
    # Medium XSS (from 3 tools)
    xss = Finding(
        id="XSS-001",
        finding_type=FindingType.XSS,
        url="https://example.com/search",
        endpoint="/search",
        parameter="q",
        severity=Severity.MEDIUM,
        confidence=0.90,
        source_tool="dalfox",
        source_tools=["dalfox", "xsstrike", "xsser"],
        exploitability="easy",
        evidence="Reflected XSS in search parameter",
        scan_id="20260106_100000",
    )
    
    collection.add_finding(rce)
    collection.add_finding(sqli)
    collection.add_finding(xss)
    
    # Calculate risk
    engine = RiskEngine(threshold=50.0)
    risk = engine.calculate(collection)
    
    # Print results
    risk.print_summary()
    
    print(f"JSON output:\n{risk.to_json()}")
