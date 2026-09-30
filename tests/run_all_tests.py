"""
Flipkart Sales Intelligence System - Master Test Suite Runner
Executes all automated test suites and outputs a detailed execution report.
"""

import os
import sys
import time
import pytest

def main():
    print("=" * 80)
    print(" FLIPKART SALES INTELLIGENCE SYSTEM - AUTOMATED VERIFICATION SUITE")
    print("=" * 80)
    
    start_time = time.time()
    
    # Run pytest programmatically
    args = [
        "-v",
        "--tb=short",
        "tests"
    ]
    
    exit_code = pytest.main(args)
    elapsed = round(time.time() - start_time, 2)
    
    print("\n" + "=" * 80)
    if exit_code == 0:
        print(f" [PASS] ALL 20 TESTS PASSED SUCCESSFULLY! (Completed in {elapsed}s)")
    else:
        print(f" [FAIL] TEST FAILURES DETECTED. (Exit Code: {exit_code}, Duration: {elapsed}s)")
    print("=" * 80)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
