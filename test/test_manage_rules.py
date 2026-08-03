#!/usr/bin/env python3

"""
===============================================================================
Mesh Control Plane

Test Script: RULES.md Security & Password Protection Tool
===============================================================================
"""

import os
import sys
import stat

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.manage_rules import (
    set_password,
    verify_password,
    lock_rules,
    unlock_rules,
    verify_rules_integrity,
    RULES_PATH
)


def main():
    print("==========================================================")
    print("Testing RULES.md Security & Password Protection Tool")
    print("==========================================================")

    test_pwd = "MeshSecurityPassword2026!"

    # 1. Test set-password and verify-password
    print("\n[Test 1: Setting Master Password]")
    set_password(test_pwd)
    assert verify_password(test_pwd) is True
    assert verify_password("WrongPassword123") is False
    print("Password hashing & verification PASSED!")

    # 2. Test Lock Rules
    print("\n[Test 2: Locking RULES.md]")
    locked = lock_rules()
    assert locked is True
    
    # Check permissions (should be read-only)
    mode = os.stat(RULES_PATH).st_mode
    is_readonly = not bool(mode & stat.S_IWUSR)
    print(f"RULES.md is Read-Only: {is_readonly}")
    assert is_readonly is True

    # 3. Test Verify Integrity
    print("\n[Test 3: Signature Integrity Verification]")
    verified = verify_rules_integrity()
    assert verified is True
    print("Signature Verification PASSED!")

    # 4. Test Unlock Rules with Wrong Password
    print("\n[Test 4: Unlock with Wrong Password (Should Fail)]")
    failed_unlock = unlock_rules("WrongPassword123")
    assert failed_unlock is False

    # 5. Test Unlock Rules with Correct Password
    print("\n[Test 5: Unlock with Correct Password]")
    success_unlock = unlock_rules(test_pwd)
    assert success_unlock is True

    # Re-lock RULES.md after test completion
    lock_rules()

    print("\n[SUCCESS] RULES.md Password Protection & Integrity Tests PASSED!")


if __name__ == "__main__":
    main()
