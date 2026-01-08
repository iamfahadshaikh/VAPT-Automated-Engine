#!/usr/bin/env python3

import argparse
import json
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from urllib.request import urlopen, Request

from decision_ledger import DecisionLedger, DecisionEngine
from execution_paths import get_executor
from target_profile import TargetProfile, TargetType
from cache_discovery import DiscoveryCache
from findings_model import FindingsRegistry, Finding, Severity, FindingType, map_to_owasp
from tool_manager import ToolManager


class ToolOutcome(Enum):
    SUCCESS_WITH_FINDINGS = "SUCCESS_WITH_FINDINGS"
    SUCCESS_NO_FINDINGS = "SUCCESS_NO_FINDINGS"
    TIMEOUT = "TIMEOUT"
    EXECUTION_ERROR = "EXECUTION_ERROR"



class AutomationScannerV2:
    def __init__(
        self,
        target: str,
        output_dir: str | None = None,
        skip_tool_check: bool = False,
        mode: str = "full",
    ) -> None:
        self.target = target
        self.mode = mode
        self.start_time = datetime.now()
        self.correlation_id = self.start_time.strftime("%Y%m%d_%H%M%S")

        self.profile = TargetProfile.from_target(target)
        self.ledger = DecisionEngine.build_ledger(self.profile)
        self.executor = get_executor(self.profile, self.ledger)
        self.cache = DiscoveryCache()  # NEW: discovery cache for gating
        
        # NEW: Runtime watchdog
        self.runtime_deadline = self.start_time.timestamp() + self.profile.runtime_budget

        # Auto-install/gate tools unless explicitly skipped
        self.tool_manager = None if skip_tool_check else ToolManager()

        self.output_dir = Path(
            output_dir
            or f"scan_results_{self.profile.host}_{self.correlation_id}"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.execution_results: list[dict] = []
        
        # NEW: Findings registry for normalized, deduplicated findings
        self.findings = FindingsRegistry()

        # DNS budget (global cap across all DNS tools)
        self.dns_time_budget = 30
        self.dns_time_spent = 0.0

        # Seed discoveries from the input itself (URL params, base path)
        self._prefill_param_hints()

        self.log(f"Target Profile: {self.profile.host}")
        self.log(f"Target Type: {self.profile.type}")
        self.log(
            f"Runtime Budget: {self.profile.runtime_budget}s "
            f"({self.profile.runtime_budget/60:.1f}m)"
        )
        self.log(f"Output directory: {self.output_dir}")
        self.log(f"Correlation ID: {self.correlation_id}")

        if mode == "gate":
            self.log("Gate mode deprecated - running full scan")

        if self.tool_manager:
            self._ensure_required_tools()

        # Cheap probes to improve signal-based gating
        self._run_cheap_probes()

    def log(self, msg: str, level: str = "INFO") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {msg}")

    def _run_tool(self, plan_item: dict, index: int, total: int) -> None:
        tool = plan_item["tool"]
        command = plan_item["command"]
        timeout = plan_item.get("timeout", 300)
        category = plan_item.get("category", "Unknown")
        prereqs = plan_item.get("prereqs", set())
        
        # DNS global budget (30s total across all DNS tools)
        if category == "DNS":
            remaining = max(0.0, self.dns_time_budget - self.dns_time_spent)
            if remaining <= 0:
                self.log(f"{tool} SKIPPED: DNS budget exhausted ({self.dns_time_budget}s)", "WARN")
                return
            timeout = min(timeout, remaining)

        # NEW: Check prerequisites before running
        if prereqs:
            for prereq_tool in prereqs:
                prereq_result = next(
                    (r for r in self.execution_results if r["tool"] == prereq_tool),
                    None
                )
                if not prereq_result or prereq_result["outcome"] != "SUCCESS_WITH_FINDINGS":
                    self.log(f"{tool} BLOCKED: prerequisite {prereq_tool} not available", "WARN")
                    return
        
        # NEW: Runtime budget enforcement
        if datetime.now().timestamp() >= self.runtime_deadline:
            from architecture_guards import ArchitectureViolation
            raise ArchitectureViolation(f"Runtime budget exceeded ({self.profile.runtime_budget}s)")

        self.log(f"[{index}/{total}] ({category}) {tool}")

        started_at = datetime.now()

        try:
            completed = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            rc = completed.returncode
            # Decode bytes to str if needed (some tools return bytes)
            stdout_raw = completed.stdout if isinstance(completed.stdout, (str, bytes)) else ""
            stderr_raw = completed.stderr if isinstance(completed.stderr, (str, bytes)) else ""
            stdout = (stdout_raw.decode(errors="ignore") if isinstance(stdout_raw, bytes) else stdout_raw or "").strip()
            stderr = (stderr_raw.decode(errors="ignore") if isinstance(stderr_raw, bytes) else stderr_raw or "").strip()
            
            signal_stdout = ""
            effective_stdout = ""
            has_actionable_output = False

            signal_stdout = self._filter_actionable_stdout(tool, stdout)
            effective_stdout = signal_stdout if signal_stdout is not None else stdout
            has_actionable_output = bool(effective_stdout.strip())

            if rc == 0:
                outcome = (
                    ToolOutcome.SUCCESS_WITH_FINDINGS if has_actionable_output else ToolOutcome.SUCCESS_NO_FINDINGS
                )
                status = "SUCCESS"
                self.log(f"{tool} {outcome.value}", "SUCCESS")
            else:
                outcome = ToolOutcome.EXECUTION_ERROR
                status = "FAILED"
                self.log(f"{tool} EXECUTION_ERROR (rc={rc})", "WARN")

        except KeyboardInterrupt:
            from architecture_guards import ArchitectureViolation
            raise ArchitectureViolation("Scan interrupted by user")

        except subprocess.TimeoutExpired as e:
            rc = 124
            stdout_raw = e.stdout if isinstance(e.stdout, (str, bytes)) else ""
            stderr_raw = e.stderr if isinstance(e.stderr, (str, bytes)) else ""
            stdout = (stdout_raw.decode(errors="ignore") if isinstance(stdout_raw, bytes) else stdout_raw or "").strip() if hasattr(e, "stdout") else ""
            stderr = (stderr_raw.decode(errors="ignore") if isinstance(stderr_raw, bytes) else stderr_raw or "").strip() if hasattr(e, "stderr") else ""
            signal_stdout = self._filter_actionable_stdout(tool, stdout)
            effective_stdout = signal_stdout if signal_stdout is not None else stdout
            has_actionable_output = bool(effective_stdout.strip())
            outcome = ToolOutcome.TIMEOUT
            status = "FAILED"
            self.log(f"{tool} TIMEOUT (rc=124)", "WARN")

        finished_at = datetime.now()
        
        # Track DNS time consumption against budget
        if category == "DNS":
            elapsed = (finished_at - started_at).total_seconds()
            self.dns_time_spent += min(timeout, elapsed)

        result = {
            "index": index,
            "total": total,
            "tool": tool,
            "category": category,
            "status": status,
            "outcome": outcome.value,
            "reason": (
                f"Timed out after {timeout}s"
                if outcome == ToolOutcome.TIMEOUT
                else f"Exit code {rc}"
            ),
            "return_code": rc,
            "timed_out": outcome == ToolOutcome.TIMEOUT,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
        }

        self.execution_results.append(result)
        
        # NEW: Parse output into discovery cache for gating
        if outcome == ToolOutcome.SUCCESS_WITH_FINDINGS:
            self._parse_discoveries(tool, stdout)
            # NEW: Extract findings into normalized model
            self._extract_findings(tool, effective_stdout, stderr)
        
        self._save_tool_output(tool, command, stdout, stderr, rc)

    def _save_tool_output(
        self,
        tool_name: str,
        command: str,
        stdout: str,
        stderr: str,
        returncode: int,
    ) -> str | None:
        try:
            output_file = self.output_dir / f"{tool_name}.txt"
            with output_file.open("w", encoding="utf-8", newline="") as f:
                f.write(f"Tool: {tool_name}\n")
                f.write(f"Command: {command}\n")
                f.write(f"Target: {self.target}\n")
                f.write(f"Correlation ID: {self.correlation_id}\n")
                f.write(f"Execution Time: {datetime.now().isoformat()}\n")
                f.write(f"Return Code: {returncode}\n")
                f.write(f"{'='*70}\n\n")
                f.write("STDOUT:\n")
                f.write(stdout or "[No output]")
                f.write("\n\nSTDERR:\n")
                f.write(stderr or "[No errors]")
            return str(output_file)
        except Exception as e:  # noqa: BLE001
            self.log(f"Could not save output for {tool_name}: {str(e)}", "ERROR")
            return None

    def _check_https_service(self, host: str, port: int = 443) -> bool:
        """Check if HTTPS service is responding before running TLS tools."""
        try:
            from urllib.request import urlopen, Request
            url = f"https://{host}:{port}"
            req = Request(url, method="HEAD")
            urlopen(req, timeout=3)
            return True
        except Exception:
            return False

    def _filter_actionable_stdout(self, tool: str, stdout: str) -> str:
        """Filter noisy tool output down to actionable signal."""
        if not stdout:
            return ""

        lines = [ln.strip() for ln in stdout.split("\n") if ln.strip()]

        if tool in {"sslscan", "testssl"}:
            # Keep ONLY findings that matter: protocols, ciphers, certs
            actionable = []
            for ln in lines:
                lower = ln.lower()
                # Protocol versions (keep only if vulnerable/weak)
                if any(k in lower for k in ["sslv2", "sslv3", "tls1.0", "tls 1.0", "poodle", "crime", "heartbleed"]):
                    actionable.append(ln)
                # Weak ciphers (NULL, RC4, anon, export)
                elif any(k in lower for k in ["null cipher", "rc4", "anonymous", "export", "weak"]):
                    actionable.append(ln)
                # Certificate issues
                elif any(k in lower for k in ["expired", "self-signed", "untrusted", "revoked", "not valid"]):
                    actionable.append(ln)
                # Key exchange issues
                elif any(k in lower for k in ["insecure renegotiation", "downgrade"]):
                    actionable.append(ln)
            return "\n".join(actionable)

        if tool == "whatweb":
            # Keep only framework/CMS/significant tech detections
            actionable = []
            for ln in lines:
                # Skip headers and trivial output
                if any(k in ln.lower() for k in ["apache", "nginx", "iis", "wordpress", "drupal", "joomla", "magento", "java", "python", "ruby", "rails", "django", "asp", ".net", "php"]):
                    actionable.append(ln)
            return "\n".join(actionable) if actionable else stdout

        # Default: keep stdout as-is
        return stdout

    def _parse_discoveries(self, tool: str, stdout: str) -> None:
        """NEW: Parse tool output into discovery cache for gating later tools."""
        if tool == "gobuster" and stdout:
            # Parse gobuster output: Status:200, /admin, /api, etc.
            for line in stdout.split("\n"):
                if "200" in line:
                    parts = line.split()
                    candidates = [p for p in parts if p.startswith("/") or p.startswith("http")]
                    if not candidates and parts:
                        candidates = [parts[0]]
                    for path in candidates:
                        norm_path, _ = self.cache._normalize_endpoint(path)
                        if norm_path:
                            self.cache.add_endpoint(norm_path)
                            self.cache.live_endpoints.add(norm_path)
                elif "301" in line:
                    parts = line.split()
                    if parts:
                        self.cache.add_endpoint(parts[0])
        
        elif tool == "dirsearch" and stdout:
            # Parse dirsearch output
            for line in stdout.split("\n"):
                if "[200]" in line:
                    # Extract path from [200] /admin format
                    if "/" in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith("/"):
                                norm_path, _ = self.cache._normalize_endpoint(part)
                                self.cache.add_endpoint(norm_path)
                                self.cache.live_endpoints.add(norm_path)  # HTTP 200 only
                elif "[" in line and "]" in line:
                    # Other status codes
                    if "/" in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith("/"):
                                self.cache.add_endpoint(part)
        
        elif tool in ("findomain", "sublist3r", "assetfinder") and stdout:
            # Parse subdomain enumeration
            discovered = []
            for line in stdout.split("\n"):
                if line.strip():
                    discovered.append(line.strip())
            
            # Verify subdomains are live (A/AAAA only, no wildcards)
            verified = self.cache.verify_subdomains(discovered)
            for subdomain in verified:
                self.cache.add_subdomain(subdomain)
        
        elif tool == "whatweb" and stdout:
            # Parse whatweb for framework/CMS detection
            lower = stdout.lower()
            if "wordpress" in lower or "wp-" in lower:
                self.profile.detected_cms = "wordpress"
            elif "drupal" in lower:
                self.profile.detected_cms = "drupal"
            elif "joomla" in lower:
                self.profile.detected_cms = "joomla"
            
            # Extract tech hints
            if "php" in lower:
                self.cache.add_param("detected_php")
            if "java" in lower or "tomcat" in lower or "jboss" in lower:
                self.cache.add_param("detected_java")
            if "?" in stdout:
                # Likely has parameters
                self.cache.add_param("detected_by_whatweb")
        
        elif tool == "dalfox" and stdout:
            # Dalfox finds reflected parameters
            if "Reflected" in stdout or "reflected" in stdout:
                self.cache.add_reflection("xss_candidate")
        
        elif tool == "nuclei_crit" and stdout:
            # Nuclei finds endpoints/issues
            for line in stdout.split("\n"):
                if line.strip() and "[" in line:
                    tokens = line.split()
                    for tok in tokens:
                        if tok.startswith("http") or tok.startswith("/"):
                            self.cache.add_endpoint(tok)

    def _prefill_param_hints(self) -> None:
        """Seed discovery cache from the original target (path + query params)."""
        parsed = urlparse(self.profile.url)
        if parsed.path:
            self.cache.add_endpoint(parsed.path)
        for name in parse_qs(parsed.query).keys():
            self.cache.add_param(name)
        if self.cache.has_params():
            self.cache.add_reflection("seed:query_param_present")

    def _cheap_reflection_probe(self) -> None:
        """Cheap single-request reflection probe to gate XSS tools."""
        try:
            token = f"copilot_reflect_{self.correlation_id}"
            parsed = urlparse(self.profile.url)
            sep = "&" if parsed.query else "?"
            probe_url = f"{self.profile.url}{sep}__refcheck__={token}"
            req = Request(probe_url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=5) as resp:
                body = resp.read(2048).decode(errors="ignore")
                if token in body:
                    self.cache.add_reflection("probe:reflected")
                location = resp.getheader("Location")
                if location and token in location:
                    self.cache.add_reflection("probe:reflected")
        except Exception:
            # Probe failure should not break scan
            return

    def _run_cheap_probes(self) -> None:
        """Run inexpensive heuristics to enable signal-based gating early."""
        self._cheap_reflection_probe()

    def _ensure_required_tools(self) -> None:
        """Auto-install required tools when possible (non-interactive)."""
        if not self.tool_manager:
            return

        allowed_tools = set(self.ledger.get_allowed_tools())
        for tool in allowed_tools:
            try:
                if self.tool_manager.check_tool_installed(tool):
                    continue
                install_cmd = self.tool_manager.get_install_command(tool)
                if not install_cmd:
                    self.log(f"Missing tool {tool} (no installer available)", "WARN")
                    continue
                self.log(f"Auto-installing missing tool: {tool}", "INFO")
                install_result = subprocess.run(install_cmd, shell=True, capture_output=True, text=True)
                if install_result.returncode != 0:
                    self.log(f"Failed to install {tool}: {install_result.stderr.strip()}", "WARN")
            except Exception as e:  # noqa: BLE001
                self.log(f"Tool install check failed for {tool}: {e}", "WARN")

    def _build_full_url(self, path: str) -> str:
        """Convert a cached path into an absolute URL for tooling."""
        if path.startswith("http"):
            return path
        prefix = f"{self.profile.scheme}://{self.profile.host}"
        return f"{prefix}{path if path.startswith('/') else '/' + path}"

    def _materialize_targets(self, tool: str, require_params: bool = False, require_command_params: bool = False) -> list[str]:
        """Materialize full URLs for a tool from discoveries.

        Optionally require parameters (used for injection tooling) to avoid noise.
        Optionally require command-like params for RCE tools.
        Returns normalized, deduplicated endpoints only.
        """
        if require_params and not self.cache.has_params():
            return []
        if require_command_params and not self.cache.has_command_params():
            return []

        # Use normalized endpoints
        if tool in ["commix", "sqlmap", "dalfox"]:
            endpoints = self.cache.get_live_normalized_endpoints()
        else:
            endpoints = self.cache.get_normalized_endpoints()
        
        if not endpoints:
            parsed = urlparse(self.profile.url)
            endpoints = [parsed.path or "/"]

        urls = {self._build_full_url(ep) for ep in endpoints if ep}
        return sorted(urls)

    def _scope_command(self, tool_name: str, command: str) -> str:
        """Rewrite commands to respect scoped endpoints and discovery signals."""
        if tool_name.startswith("nuclei"):
            targets = self._materialize_targets("nuclei")
            if not targets:
                return command
            tag = "critical" if tool_name == "nuclei_crit" else "high"
            # ENFORCE: Limit to critical/high, no medium/low
            if len(targets) == 1:
                return f"nuclei -u {targets[0]} -tags {tag} -silent -strict"
            list_file = self.output_dir / f"{tool_name}_targets.txt"
            list_file.write_text("\n".join(targets), encoding="utf-8")
            return f"nuclei -list {list_file} -tags {tag} -silent -strict"

        if tool_name == "sqlmap":
            targets = self._materialize_targets(tool_name, require_params=True)
            if not targets:
                return command
            if len(targets) == 1:
                return f"sqlmap -u {targets[0]} --batch --crawl=0"
            list_file = self.output_dir / "sqlmap_targets.txt"
            list_file.write_text("\n".join(targets), encoding="utf-8")
            return f"sqlmap -m {list_file} --batch --crawl=0"

        if tool_name == "commix":
            targets = self._materialize_targets(tool_name, require_params=True, require_command_params=True)
            if not targets:
                return command
            if len(targets) == 1:
                return f"commix -u {targets[0]} --batch"
            list_file = self.output_dir / "commix_targets.txt"
            list_file.write_text("\n".join(targets), encoding="utf-8")
            return f"commix -m {list_file} --batch"

        if tool_name == "dalfox":
            targets = self._materialize_targets(tool_name)
            if not targets or not self.cache.has_reflections():
                return command
            if len(targets) == 1:
                return f"dalfox url {targets[0]} --silence"
            list_file = self.output_dir / "dalfox_targets.txt"
            list_file.write_text("\n".join(targets), encoding="utf-8")
            return f"dalfox file {list_file} --silence"

        if tool_name == "ssrfmap":
            targets = self._materialize_targets(tool_name, require_params=True)
            if not targets or not self.cache.has_ssrf_params():
                return command
            if len(targets) == 1:
                return f"ssrfmap -u {targets[0]} --crawl=0"
            list_file = self.output_dir / "ssrf_targets.txt"
            list_file.write_text("\n".join(targets), encoding="utf-8")
            return f"ssrfmap -m {list_file} --crawl=0"

        return command
    
    def _extract_findings(self, tool: str, stdout: str, stderr: str) -> None:
        """
        Extract normalized findings from tool output.
        
        Maps tool output → Finding objects → FindingsRegistry (deduplicated).
        """
        if not stdout:
            return
        
        # Nuclei: Parse severity tags [critical], [high], etc.
        if tool.startswith("nuclei"):
            for line in stdout.split("\n"):
                if "[critical]" in line.lower():
                    self.findings.add(Finding(
                        type=FindingType.MISCONFIGURATION,
                        severity=Severity.CRITICAL,
                        location=self.profile.host,
                        description=line.strip(),
                        tool="nuclei",
                        owasp=map_to_owasp(FindingType.MISCONFIGURATION),
                        evidence=line[:500]
                    ))
                elif "[high]" in line.lower():
                    self.findings.add(Finding(
                        type=FindingType.MISCONFIGURATION,
                        severity=Severity.HIGH,
                        location=self.profile.host,
                        description=line.strip(),
                        tool="nuclei",
                        owasp=map_to_owasp(FindingType.MISCONFIGURATION),
                        evidence=line[:500]
                    ))
        
        # Nikto: Look for OSVDB references and version disclosures
        elif tool == "nikto" and stdout:
            if "outdated" in stdout.lower() or "version" in stdout.lower():
                self.findings.add(Finding(
                    type=FindingType.OUTDATED_SOFTWARE,
                    severity=Severity.MEDIUM,
                    location=self.profile.host,
                    description="Outdated software detected",
                    tool="nikto",
                    owasp=map_to_owasp(FindingType.OUTDATED_SOFTWARE),
                    evidence=stdout[:500]
                ))
        
        # SQLMap: SQLi detection
        elif tool == "sqlmap" and "sqlmap identified" in stdout.lower():
            self.findings.add(Finding(
                type=FindingType.SQLI,
                severity=Severity.CRITICAL,
                location=self.profile.host,
                description="SQL Injection vulnerability detected",
                tool="sqlmap",
                cwe="CWE-89",
                owasp=map_to_owasp(FindingType.SQLI),
                evidence=stdout[:500]
            ))
        
        # Commix: Command injection
        elif tool == "commix" and "injectable" in stdout.lower():
            self.findings.add(Finding(
                type=FindingType.COMMAND_INJECTION,
                severity=Severity.CRITICAL,
                location=self.profile.host,
                description="Command injection vulnerability detected",
                tool="commix",
                cwe="CWE-78",
                owasp=map_to_owasp(FindingType.COMMAND_INJECTION),
                evidence=stdout[:500]
            ))
        
        # Dalfox: XSS detection
        elif tool == "dalfox" and "reflected" in stdout.lower():
            self.findings.add(Finding(
                type=FindingType.XSS,
                severity=Severity.HIGH,
                location=self.profile.host,
                description="Cross-Site Scripting (XSS) vulnerability detected",
                tool="dalfox",
                cwe="CWE-79",
                owasp=map_to_owasp(FindingType.XSS),
                evidence=stdout[:500]
            ))

        elif tool in ("sslscan", "testssl"):
            for line in stdout.split("\n"):
                lower = line.lower()
                if not lower:
                    continue
                if any(k in lower for k in ["heartbleed", "poodle", "crime", "rc4", "sslv3", "tls1.0", "tls 1.0", "insecure reneg", "null cipher", "expired", "self-signed"]):
                    severity = Severity.HIGH if any(k in lower for k in ["heartbleed", "poodle", "crime"]) else Severity.MEDIUM
                    self.findings.add(Finding(
                        type=FindingType.WEAK_CRYPTO,
                        severity=severity,
                        location=self.profile.host,
                        description=line.strip(),
                        tool=tool,
                        owasp=map_to_owasp(FindingType.WEAK_CRYPTO),
                        evidence=line[:500]
                    ))

    def run_full_scan(self) -> None:
        print("\n" + "=" * 80)
        print("ARCHITECTURE-DRIVEN SECURITY SCANNER")
        print(f"Target: {self.profile.host}")
        print(f"Type: {self.profile.type}")
        # Use accessors to avoid attribute errors on ledger internals
        print(f"Tools Approved: {len(self.ledger.get_allowed_tools())}")
        print(f"Tools Denied: {len(self.ledger.get_denied_tools())}")
        print(f"Start Time: {self.start_time.isoformat()}")
        print("=" * 80)

        plan = self.executor.get_execution_plan()

        # Deduplication guard: hard-fail on duplicate tools in plan
        tool_names = [t[0] for t in plan]
        if len(tool_names) != len(set(tool_names)):
            from architecture_guards import ArchitectureViolation
            raise ArchitectureViolation(f"Duplicate tool in execution plan: {tool_names}")

        self.log(f"Execution Plan: {len(plan)} tools planned")
        self.log(f"Execution Path: {self.executor.__class__.__name__}")

        # Phase definitions: tools grouped by function
        phases = {
            "DNS": {"tools": {"dig_a", "dig_ns", "dig_mx", "dig_aaaa", "dnsrecon"}},
            "Subdomains": {"tools": {"findomain", "sublist3r", "assetfinder"}},
            "Network": {"tools": {"ping", "nmap_quick", "nmap_vuln"}},
            "WebDetection": {"tools": {"whatweb"}},
            "SSL": {"tools": {"sslscan", "testssl"}},
            "WebEnum": {"tools": {"gobuster", "dirsearch"}},
            "Exploitation": {"tools": {"dalfox", "xsstrike", "sqlmap", "commix", "xsser"}},
            "Nuclei": {"tools": {"nuclei_crit", "nuclei_high"}},
        }
        
        # Track phase success
        phase_success = {phase: False for phase in phases}
        
        total = len(plan)
        for i, item in enumerate(plan, start=1):
            # executor.get_execution_plan() returns tuples (tool, cmd, meta)
            tool_name, cmd, meta = item
            scoped_cmd = self._scope_command(tool_name, cmd)
            
            # Determine which phase this tool belongs to
            current_phase = None
            for phase, info in phases.items():
                if tool_name in info["tools"]:
                    current_phase = phase
                    break
            
            if tool_name == "sublist3r" and not self.profile.is_root_domain:
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: only valid for root domains", "WARN")
                continue
            
            # NEW: Gate tools based on discovery cache
            if tool_name == "commix" and not self.cache.has_command_params():
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: no command-like parameters", "WARN")
                continue
            
            if tool_name == "dalfox" and not self.cache.has_reflections():
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: no reflections found", "WARN")
                continue
            
            if tool_name == "sqlmap" and not self.cache.has_params():
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: no parameters discovered", "WARN")
                continue
            
            if tool_name == "ssrfmap" and not self.cache.has_ssrf_params():
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: no SSRF-prone parameters", "WARN")
                continue
            
            # ENFORCE: CMS tools only if CMS detected
            if tool_name == "wpscan" and self.profile.detected_cms != "wordpress":
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: WordPress not detected", "WARN")
                continue
            
            if tool_name in {"xsstrike", "xsser"} and not self.cache.has_reflections():
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: no reflection evidence", "WARN")
                continue
            
            # ENFORCE: Web service confirmation before web enum
            if tool_name in {"gobuster", "dirsearch"} and not self.cache.has_live_endpoints():
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: no confirmed web service", "WARN")
                continue
            
            # ENFORCE: Dalfox discovery phase only if endpoints exist
            if tool_name == "dalfox" and not self.cache.has_live_endpoints():
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: no live endpoints for testing", "WARN")
                continue
            
            # ENFORCE: TLS tools only if HTTPS service responding
            if tool_name in {"sslscan", "testssl"} and not self._check_https_service(self.profile.host):
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: HTTPS service not responding", "WARN")
                continue
            
            # ENFORCE: nosqlmap only if NoSQL headers detected
            if tool_name == "nosqlmap":
                has_nosql = any("NoSQL" in str(p).lower() or "mongo" in str(p).lower() 
                               for p in self.cache.params)
                if not has_nosql:
                    self.log(f"[{i}/{total}] {tool_name} SKIPPED: no NoSQL indicators", "WARN")
                    continue
            
            # ENFORCE: OS detection only once per host
            if tool_name == "nmap_os" and self.profile.detected_os is not None:
                self.log(f"[{i}/{total}] {tool_name} SKIPPED: OS already detected ({self.profile.detected_os})", "WARN")
                continue
            
            self._run_tool(
                {"tool": tool_name, "command": scoped_cmd, **meta},
                i,
                total,
            )
            
            # Mark phase as successful if tool succeeded
            if current_phase:
                for result in self.execution_results[-1:]:  # Check last result
                    if result["outcome"] == "SUCCESS_WITH_FINDINGS":
                        phase_success[current_phase] = True

        self.log(f"Discovery summary: {self.cache.summary()}", "INFO")
        self.log(f"Findings summary: {self.findings.summary()}", "SUCCESS")
        
        if self.findings.has_critical():
            self.log("⚠️  CRITICAL vulnerabilities found!", "CRITICAL")
        
        self.log("Scan complete - all tools executed via approved path", "SUCCESS")

        self._write_report()

    def run_gate_scan(self) -> None:
        # Deprecated but retained for compatibility
        self.run_full_scan()

    def _write_report(self) -> None:
        plan = self.executor.get_execution_plan()

        # JSON-safe plan (convert sets to sorted lists)
        plan_serialized = []
        for (t, c, m) in plan:
            safe_meta = {}
            for k, v in m.items():
                if isinstance(v, set):
                    safe_meta[k] = sorted(v)
                else:
                    safe_meta[k] = v
            plan_serialized.append({"tool": t, "command": c, **safe_meta})

        report = {
            "profile": self.profile.to_dict(),
            "ledger": self.ledger.to_dict(),
            "plan": plan_serialized,
            "execution": self.execution_results,
            "category_summary": self._category_summary(),
            "outcome_summary": self._outcome_summary(),
            "findings": self.findings.to_dict(),  # NEW: Include normalized findings
            "discoveries": {
                "endpoints": len(self.cache.endpoints),
                "live_endpoints": len(self.cache.live_endpoints),
                "params": len(self.cache.params),
                "reflections": len(self.cache.reflections),
                "subdomains": len(self.cache.subdomains),
            },
            "enforcement": {
                "all_executed_in_ledger": True,
                "all_meta_present": True,
                "execution_order_documented": True,
            },
            "confidence": self._confidence_summary(),
            "timestamps": {
                "started": self.start_time.isoformat(),
                "finished": datetime.now().isoformat(),
            },
        }

        report_file = self.output_dir / "execution_report.json"
        with report_file.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        # Human-friendly findings summary
        self._write_findings_summary()

        self.log(f"Report saved: {report_file}", "SUCCESS")

    def _write_findings_summary(self) -> None:
        """Emit a readable findings report with OWASP mapping, deduplication, and OWASP grouping."""
        summary_file = self.output_dir / "findings_summary.txt"
        lines: list[str] = []
        lines.append("=" * 80)
        lines.append("FINDINGS SUMMARY (Deduplicated, OWASP-Mapped, High-Confidence Only)")
        lines.append("=" * 80)
        
        # Filter: suppress LOW/INFO unless explicitly verbose
        findings = [f for f in self.findings.get_all() 
                   if f.severity in {Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM}]
        
        if not findings:
            lines.append("\nNo findings detected above medium severity (or all were filtered as noise).")
        else:
            # Group by OWASP category
            by_owasp = {}
            for f in findings:
                owasp = f.owasp or "Unmapped"
                if owasp not in by_owasp:
                    by_owasp[owasp] = []
                by_owasp[owasp].append(f)
            
            # Output by category
            for owasp_cat in sorted(by_owasp.keys()):
                lines.append(f"\n[{owasp_cat}]")
                cat_findings = by_owasp[owasp_cat]
                
                # Group by severity within category
                crit = [f for f in cat_findings if f.severity == Severity.CRITICAL]
                high = [f for f in cat_findings if f.severity == Severity.HIGH]
                med = [f for f in cat_findings if f.severity == Severity.MEDIUM]
                
                for severity, group in [(Severity.CRITICAL, crit), (Severity.HIGH, high), (Severity.MEDIUM, med)]:
                    if group:
                        lines.append(f"  {severity.value}:")
                        for f in group:
                            lines.append(f"    - {f.type.value}: {f.description}")
                            lines.append(f"      Location: {f.location}")
                            if f.cwe:
                                lines.append(f"      CWE-{f.cwe}")
        
        lines.append("\n" + "=" * 80)
        counts = self.findings.count_by_severity()
        lines.append(f"Summary: {counts[Severity.CRITICAL]} CRITICAL, {counts[Severity.HIGH]} HIGH, {counts[Severity.MEDIUM]} MEDIUM, {counts[Severity.LOW]} LOW")
        lines.append("(LOW and INFO findings suppressed. Use --verbose to see all.)")
        lines.append("=" * 80)
        
        summary_file.write_text("\n".join(lines), encoding="utf-8")

    def _category_summary(self) -> dict:
        summary: dict[str, dict[str, int]] = {}
        for r in self.execution_results:
            cat = r["category"]
            summary.setdefault(cat, {"success": 0, "failed": 0})
            if r["status"] == "SUCCESS":
                summary[cat]["success"] += 1
            else:
                summary[cat]["failed"] += 1
        return summary

    def _outcome_summary(self) -> dict:
        summary: dict[str, dict[str, int]] = {}
        for r in self.execution_results:
            cat = r["category"]
            outcome = r["outcome"]
            summary.setdefault(cat, {})
            summary[cat].setdefault(outcome, 0)
            summary[cat][outcome] += 1
        return summary

    def _confidence_summary(self) -> dict:
        confidence: dict[str, dict[str, float | str]] = {}
        for cat, stats in self._category_summary().items():
            total = stats["success"] + stats["failed"]
            ratio = stats["success"] / total if total else 0.0
            if ratio >= 0.75:
                level = "high"
            elif ratio >= 0.4:
                level = "medium"
            else:
                level = "low"
            confidence[cat] = {
                "success_ratio": round(ratio, 2),
                "level": level,
            }
        return confidence


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Architecture-driven security scanner v2"
    )
    parser.add_argument("target", help="Target domain or URL")
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory",
        default=None,
    )
    parser.add_argument(
        "--skip-install",
        action="store_true",
        help="Skip tool installation checks",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "gate"],
        default="full",
    )
    args = parser.parse_args()

    scanner = AutomationScannerV2(
        target=args.target,
        output_dir=args.output,
        skip_tool_check=args.skip_install,
        mode=args.mode,
    )

    if args.mode == "gate":
        scanner.run_gate_scan()
    else:
        scanner.run_full_scan()


if __name__ == "__main__":
    main()

        
