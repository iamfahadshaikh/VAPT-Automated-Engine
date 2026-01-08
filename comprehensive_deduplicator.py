"""
Enhanced Deduplicator - Comprehensive deduplication across all finding types
Handles DNS, subdomains, endpoints, nuclei findings, and cross-tool findings
"""

import hashlib
import json
from typing import List, Dict, Set, Tuple
from collections import defaultdict


class ComprehensiveDeduplicator:
    """Deduplicates findings across all stages of scanning"""
    
    @staticmethod
    def hash_finding(finding: Dict) -> str:
        """Generate consistent hash for finding deduplication"""
        key = (
            finding.get("type", ""),
            finding.get("target", ""),
            finding.get("title", ""),
            str(finding.get("severity", ""))
        )
        return hashlib.md5(str(key).encode()).hexdigest()
    
    # ============ DNS DEDUPLICATION (Req 11) ============
    @staticmethod
    def deduplicate_dns_records(dns_results: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """
        Deduplicate DNS records across multiple DNS tools
        
        Args:
            dns_results: {'dig': [...], 'host': [...], 'nslookup': [...]}
            
        Returns:
            Deduplicated results with single source of truth per record type
        """
        deduped = {}
        
        for record_type, records in dns_results.items():
            unique = set()
            for record in records:
                # Normalize and clean
                clean = record.strip().lower()
                if clean and not clean.startswith(";"):
                    unique.add(clean)
            
            if unique:
                deduped[record_type] = sorted(list(unique))
        
        return deduped
    
    # ============ SUBDOMAIN DEDUPLICATION (Req 13) ============
    @staticmethod
    def deduplicate_subdomains(subdomains: List[str], base_domain: str) -> List[str]:
        """
        Deduplicate subdomains from multiple tools
        
        Args:
            subdomains: List from all subdomain tools
            base_domain: Root domain to validate against
            
        Returns:
            Sorted unique subdomains
        """
        unique = set()
        
        for subdomain in subdomains:
            # Normalize
            clean = subdomain.strip().lower()
            
            # Validate it's part of base domain
            if clean.endswith(base_domain) or clean == base_domain:
                unique.add(clean)
        
        return sorted(list(unique))
    
    # ============ ENDPOINT DEDUPLICATION (Req 36) ============
    @staticmethod
    def deduplicate_endpoints(endpoints: List[Dict]) -> List[Dict]:
        """
        Deduplicate discovered endpoints
        
        Args:
            endpoints: List of discovered endpoints with url, method, params, etc.
            
        Returns:
            Deduplicated endpoint list
        """
        unique_endpoints = {}
        
        for endpoint in endpoints:
            # Use URL + method as key
            key = (endpoint.get("url", "").lower(), endpoint.get("method", "GET"))
            
            if key not in unique_endpoints:
                unique_endpoints[key] = endpoint
            else:
                # Merge parameters if both have them
                existing = unique_endpoints[key]
                if endpoint.get("params") and existing.get("params"):
                    existing["params"] = list(set(
                        existing.get("params", []) + endpoint.get("params", [])
                    ))
        
        return list(unique_endpoints.values())
    
    # ============ NUCLEI FINDING DEDUPLICATION (Req 51) ============
    @staticmethod
    def deduplicate_nuclei_findings(nuclei_findings: List[Dict]) -> List[Dict]:
        """
        Deduplicate Nuclei template matches
        
        Args:
            nuclei_findings: List of template matches
            
        Returns:
            Deduplicated findings keeping highest severity
        """
        unique_findings = {}
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        
        for finding in nuclei_findings:
            # Key: template + target + title
            key = (
                finding.get("template", ""),
                finding.get("target", ""),
                finding.get("title", "")
            )
            
            if key not in unique_findings:
                unique_findings[key] = finding
            else:
                # Keep the one with higher severity
                existing = unique_findings[key]
                existing_sev = severity_order.get(existing.get("severity", "INFO"), 5)
                new_sev = severity_order.get(finding.get("severity", "INFO"), 5)
                
                if new_sev < existing_sev:
                    unique_findings[key] = finding
        
        return list(unique_findings.values())
    
    # ============ CROSS-TOOL FINDING DEDUPLICATION (Req 56) ============
    @staticmethod
    def deduplicate_findings(findings: List[Dict]) -> List[Dict]:
        """
        Master deduplication across all tools
        
        Args:
            findings: List of vulnerability findings from all tools
            
        Returns:
            Deduplicated findings with cross-tool merging
        """
        if not findings:
            return []
        
        # Group by finding type and target
        grouped = defaultdict(list)
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}
        
        for finding in findings:
            # Create grouping key
            key = (
                finding.get("type", "").lower(),
                finding.get("target", "").lower(),
                finding.get("title", "").lower()
            )
            grouped[key].append(finding)
        
        # Deduplicate within each group
        deduped = []
        for key, group in grouped.items():
            if not group:
                continue
            
            # Sort by severity and take the best one
            sorted_group = sorted(
                group,
                key=lambda f: severity_order.get(f.get("severity", "INFO"), 5)
            )
            
            best = sorted_group[0].copy()
            
            # Merge source tools
            sources = set()
            for f in group:
                if f.get("source"):
                    sources.add(f["source"])
            
            if sources:
                best["sources"] = sorted(list(sources))
                best["source_count"] = len(sources)
            
            deduped.append(best)
        
        return deduped
    
    @staticmethod
    def merge_findings_from_tools(findings_by_tool: Dict[str, List[Dict]]) -> Tuple[List[Dict], Dict]:
        """
        Merge findings from multiple tools with deduplication
        
        Args:
            findings_by_tool: {'xsstrike': [...], 'dalfox': [...], ...}
            
        Returns:
            (deduplicated_findings, dedup_stats)
        """
        all_findings = []
        tool_counts = {}
        
        for tool, findings in findings_by_tool.items():
            tool_counts[tool] = len(findings)
            for finding in findings:
                finding["source"] = tool
                all_findings.append(finding)
        
        # Deduplicate
        deduped = ComprehensiveDeduplicator.deduplicate_findings(all_findings)
        
        # Calculate stats
        stats = {
            "total_before": len(all_findings),
            "total_after": len(deduped),
            "duplicates_removed": len(all_findings) - len(deduped),
            "by_tool": tool_counts,
            "dedup_rate": f"{(1 - len(deduped) / max(len(all_findings), 1)) * 100:.1f}%"
        }
        
        return deduped, stats
    
    @staticmethod
    def report_dedup_stats(stats: Dict) -> str:
        """Generate deduplication statistics report"""
        report = "\nDEDUPLICATION STATISTICS\n"
        report += "=" * 50 + "\n"
        report += f"Total findings before: {stats['total_before']}\n"
        report += f"Total findings after:  {stats['total_after']}\n"
        report += f"Duplicates removed:    {stats['duplicates_removed']}\n"
        report += f"Deduplication rate:    {stats['dedup_rate']}\n"
        report += f"\nBy Tool:\n"
        for tool, count in stats.get('by_tool', {}).items():
            report += f"  {tool}: {count}\n"
        report += "\n"
        return report
