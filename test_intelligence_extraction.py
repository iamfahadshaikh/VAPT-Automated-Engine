"""
Integration test: Findings extraction + OWASP mapping + deduplication.
"""

from findings_model import (
    Finding,
    FindingType,
    FindingsRegistry,
    Severity,
    map_to_owasp,
)


def test_findings_deduplication():
    """Verify findings deduplication by (type, location, cwe)"""
    registry = FindingsRegistry()
    
    # Same finding from two tools (should dedupe)
    finding1 = Finding(
        type=FindingType.SQLI,
        severity=Severity.CRITICAL,
        location="https://example.com/login",
        description="SQL injection found",
        cwe="CWE-89",
        tool="sqlmap",
    )
    finding2 = Finding(
        type=FindingType.SQLI,
        severity=Severity.CRITICAL,
        location="https://example.com/login",
        description="Different description but same vuln",
        cwe="CWE-89",
        tool="manual_test",
    )
    
    assert registry.add(finding1) is True, "First finding should be new"
    assert registry.add(finding2) is False, "Second finding should be duplicate"
    assert len(registry.get_all()) == 1, "Should only have 1 finding"
    
    print("✓ Deduplication working")


def test_owasp_mapping():
    """Verify OWASP Top 10 2021 mapping"""
    mappings = {
        FindingType.XSS: "A03:2021 - Injection",
        FindingType.SQLI: "A03:2021 - Injection",
        FindingType.COMMAND_INJECTION: "A03:2021 - Injection",
        FindingType.AUTH_BYPASS: "A07:2021 - Identification and Authentication Failures",
        FindingType.OUTDATED_SOFTWARE: "A06:2021 - Vulnerable and Outdated Components",
        FindingType.SSRF: "A10:2021 - Server-Side Request Forgery",
        FindingType.MISCONFIGURATION: "A05:2021 - Security Misconfiguration",
    }
    
    for finding_type, expected_owasp in mappings.items():
        assert map_to_owasp(finding_type) == expected_owasp, \
            f"Mapping failed for {finding_type}"
    
    print("✓ OWASP mapping correct")


def test_severity_sorting():
    """Verify findings sorted by severity"""
    registry = FindingsRegistry()
    
    # Add findings in random order
    registry.add(Finding(
        type=FindingType.INFO_DISCLOSURE,
        severity=Severity.LOW,
        location="https://example.com/info",
        description="Info leak",
        tool="nikto",
    ))
    registry.add(Finding(
        type=FindingType.SQLI,
        severity=Severity.CRITICAL,
        location="https://example.com/login",
        description="SQLi",
        cwe="CWE-89",
        tool="sqlmap",
    ))
    registry.add(Finding(
        type=FindingType.XSS,
        severity=Severity.HIGH,
        location="https://example.com/search",
        description="XSS",
        cwe="CWE-79",
        tool="dalfox",
    ))
    registry.add(Finding(
        type=FindingType.MISCONFIGURATION,
        severity=Severity.MEDIUM,
        location="https://example.com/config",
        description="Misconfig",
        tool="nuclei",
    ))
    
    all_findings = registry.get_all()
    severities = [f.severity for f in all_findings]
    
    # Should be: CRITICAL, HIGH, MEDIUM, LOW
    expected_order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW]
    assert severities == expected_order, f"Wrong order: {severities}"
    
    print("✓ Severity sorting works")


def test_findings_summary():
    """Verify summary and counts"""
    registry = FindingsRegistry()
    
    # Add multiple findings
    registry.add(Finding(
        type=FindingType.SQLI,
        severity=Severity.CRITICAL,
        location="https://example.com/1",
        description="SQLi 1",
        cwe="CWE-89",
        tool="sqlmap",
    ))
    registry.add(Finding(
        type=FindingType.COMMAND_INJECTION,
        severity=Severity.CRITICAL,
        location="https://example.com/2",
        description="Cmd injection",
        cwe="CWE-78",
        tool="commix",
    ))
    registry.add(Finding(
        type=FindingType.XSS,
        severity=Severity.HIGH,
        location="https://example.com/3",
        description="XSS",
        cwe="CWE-79",
        tool="dalfox",
    ))
    
    counts = registry.count_by_severity()
    assert counts[Severity.CRITICAL] == 2, "Should have 2 critical"
    assert counts[Severity.HIGH] == 1, "Should have 1 high"
    assert counts[Severity.MEDIUM] == 0, "Should have 0 medium"
    
    assert registry.has_critical() is True, "Should detect critical findings"
    
    summary = registry.summary()
    assert "Critical: 2" in summary, f"Summary wrong: {summary}"
    assert "High: 1" in summary, f"Summary wrong: {summary}"
    
    print("✓ Summary and counts correct")


def test_findings_export():
    """Verify JSON export"""
    registry = FindingsRegistry()
    
    registry.add(Finding(
        type=FindingType.SQLI,
        severity=Severity.CRITICAL,
        location="https://example.com/login",
        description="SQL injection vulnerability",
        cwe="CWE-89",
        owasp="A03:2021 - Injection",
        tool="sqlmap",
        evidence="SELECT * FROM users WHERE id=1 OR 1=1",
        remediation="Use parameterized queries",
    ))
    
    export = registry.to_dict()
    
    assert export["total"] == 1, "Total count wrong"
    assert export["by_severity"]["CRITICAL"] == 1, "Severity count wrong"
    assert len(export["findings"]) == 1, "Findings list wrong"
    
    finding_dict = export["findings"][0]
    assert finding_dict["type"] == "SQLi", "Type wrong"
    assert finding_dict["severity"] == "CRITICAL", "Severity wrong"
    assert finding_dict["cwe"] == "CWE-89", "CWE wrong"
    assert finding_dict["owasp"] == "A03:2021 - Injection", "OWASP wrong"
    
    print("✓ Export format correct")


if __name__ == "__main__":
    test_findings_deduplication()
    test_owasp_mapping()
    test_severity_sorting()
    test_findings_summary()
    test_findings_export()
    
    print("\n=== ALL INTELLIGENCE EXTRACTION TESTS PASSED ===")
    print("✓ Findings model working")
    print("✓ Deduplication working")
    print("✓ OWASP mapping correct")
    print("✓ Severity sorting correct")
    print("✓ Export format valid")
