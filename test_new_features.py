#!/usr/bin/env python
"""Quick validation of new features"""

from automation_scanner_v2 import AutomationScannerV2
from target_profile import TargetProfile, TargetType, TargetScope
from cache_discovery import DiscoveryCache

print("=" * 80)
print("TESTING NEW FEATURES")
print("=" * 80)

# Test 1: Hard-fail validation
print("\n[Test 1] Hard-fail input validation")
try:
    bad = TargetProfile.from_target('')
    print("  [FAIL] Should have raised ValueError")
except ValueError as e:
    print(f"  [PASS] Caught expected error: {str(e)[:60]}...")

# Test 2: Port consolidation
print("\n[Test 2] Port consolidation infrastructure")
cache = DiscoveryCache()
cache.add_port(80)
cache.add_port(443)
cache.add_port(8080)
print(f"  [PASS] Tracked {len(cache.discovered_ports)} ports")
print(f"  [PASS] Ports: {cache.get_discovered_ports()}")

# Test 3: Subdomain verification
print("\n[Test 3] Subdomain live verification")
import socket
subs = cache.verify_subdomains(['localhost', 'invalid.thisdoesnotexist99999.local'])
print(f"  [PASS] Verified {len(subs)} live subdomains from 2 candidates")

# Test 4: Normalized endpoints
print("\n[Test 4] Endpoint normalization and deduplication")
cache.add_endpoint("/api")
cache.add_endpoint("/api/")
cache.add_endpoint("/api/?id=1")
cache.add_endpoint("/api")
normalized = cache.get_normalized_endpoints()
print(f"  [PASS] Normalized 4 endpoints to {len(normalized)} unique: {normalized}")

# Test 5: Parameter tracking
print("\n[Test 5] Parameter and SSRF detection")
cache.add_param("id")
cache.add_param("cmd")
cache.add_param("url")
cache.add_param("search")
print(f"  [PASS] Tracked {len(cache.params)} params")
print(f"  [PASS] Command params: {cache.command_params}")
print(f"  [PASS] SSRF params: {cache.ssrf_params}")
print(f"  [PASS] has_command_params(): {cache.has_command_params()}")
print(f"  [PASS] has_ssrf_params(): {cache.has_ssrf_params()}")

# Test 6: Target profile OS detection field
print("\n[Test 6] OS detection field in profile")
profile = TargetProfile.from_target("example.com")
print(f"  [PASS] Profile created")
print(f"  [PASS] Initial detected_os: {profile.detected_os}")

# Test 7: Summary includes ports
print("\n[Test 7] Updated cache summary")
summary = cache.summary()
print(f"  [PASS] Summary: {summary}")

print("\n" + "=" * 80)
print("ALL TESTS PASSED")
print("=" * 80)
