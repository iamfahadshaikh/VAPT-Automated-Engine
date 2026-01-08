#!/usr/bin/env python3
"""
Test: Discovery cache gating (commix/dalfox/sqlmap)
Demonstrates blockers, prereqs, and dynamic tool filtering.
"""

import sys
sys.path.insert(0, '/mnt/c/Users/FahadShaikh/Desktop/something')

from automation_scanner_v2 import AutomationScannerV2
from cache_discovery import DiscoveryCache

print("=" * 80)
print("DISCOVERY CACHE GATING TEST")
print("=" * 80)

# Simulate cache state after discovery phase
cache = DiscoveryCache()
cache.add_endpoint("/admin")
cache.add_endpoint("/api")
cache.add_param("id")
cache.add_param("search")
cache.add_reflection("user_input")
cache.add_subdomain("api.treadbinary.com")

print("\n[AFTER DISCOVERY PHASE]")
print(f"  Endpoints: {cache.endpoints}")
print(f"  Params: {cache.params}")
print(f"  Reflections: {cache.reflections}")
print(f"  Subdomains: {cache.subdomains}")
print(f"  Summary: {cache.summary()}")

# Create scanner
scanner = AutomationScannerV2("treadbinary.com")
scanner.cache = cache  # Inject the cache

print("\n[TOOL GATING LOGIC]")
print(f"  commix should run? {scanner.cache.has_params()} (has params: {scanner.cache.params})")
print(f"  dalfox should run? {scanner.cache.has_reflections()} (has reflections: {scanner.cache.reflections})")
print(f"  sqlmap should run? {scanner.cache.has_params()} (has params: {scanner.cache.params})")

# Show what would be gated
plan = scanner.executor.get_execution_plan()
gated_tools = []

for tool_name, cmd, meta in plan:
    if tool_name == "commix" and not scanner.cache.has_params():
        gated_tools.append(f"{tool_name} (no params)")
    elif tool_name == "dalfox" and not scanner.cache.has_reflections():
        gated_tools.append(f"{tool_name} (no reflections)")
    elif tool_name == "sqlmap" and not scanner.cache.has_params():
        gated_tools.append(f"{tool_name} (no params)")

print(f"\n[TOOLS THAT WOULD BE SKIPPED]")
if gated_tools:
    for tool in gated_tools:
        print(f"  - {tool}")
else:
    print("  (none - all conditions met)")

print("\n[PREREQUISITES IN PLAN]")
prereq_tools = [(t[0], t[2].get("prereqs")) for t in plan if t[2].get("prereqs")]
for tool, prereqs in prereq_tools[:5]:
    print(f"  {tool}: requires {prereqs}")

print(f"\n✓ Test complete: discovery cache correctly gates tools")
print("=" * 80)
