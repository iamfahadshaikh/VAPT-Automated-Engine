#!/usr/bin/env python3
"""
Scanner wrapper with skip functionality
Allows user to press Ctrl+C during tool execution to skip and continue to next tool
"""

import subprocess
import sys
import signal
import time

# Global state
class SkipState:
    skip_current = False
    process = None

def signal_handler(signum, frame):
    """Handle Ctrl+C - skip current tool instead of exiting"""
    if SkipState.process:
        try:
            SkipState.process.terminate()
            time.sleep(0.5)
            if SkipState.process.poll() is None:
                SkipState.process.kill()
        except:
            pass
    print("\n[SKIP] Skipping current tool, moving to next...")
    SkipState.skip_current = True

def run_scanner_with_skip(target, *args):
    """
    Run scanner with skip-on-Ctrl+C support
    
    Usage: python3 scanner_with_skip.py <target> [additional args]
    
    Press Ctrl+C during tool execution to skip and continue to next tool
    """
    
    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Build command
    cmd = [sys.executable, "automation_scanner_v2.py", target] + list(args)
    
    print("="*80)
    print("SECURITY SCANNER WITH SKIP SUPPORT")
    print("="*80)
    print(f"Target: {target}")
    print(f"\nPress Ctrl+C during tool execution to SKIP and continue to next tool")
    print("="*80 + "\n")
    
    try:
        process = subprocess.Popen(cmd)
        SkipState.process = process
        process.wait()
        return process.returncode
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Exiting scanner...")
        if process:
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                process.kill()
        return 1
    except Exception as e:
        print(f"[ERROR] Failed to run scanner: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scanner_with_skip.py <target> [args...]")
        print("\nExamples:")
        print("  python3 scanner_with_skip.py google.com -p https")
        print("  python3 scanner_with_skip.py 192.168.1.1")
        sys.exit(1)
    
    target = sys.argv[1]
    extra_args = sys.argv[2:]
    
    exit_code = run_scanner_with_skip(target, *extra_args)
    sys.exit(exit_code)
