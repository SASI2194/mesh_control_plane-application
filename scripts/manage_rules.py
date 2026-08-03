#!/usr/bin/env python3

"""
===============================================================================

Mesh Control Plane

RULES.md Governance Security & Password Protection Tool

Provides cryptographically salted SHA-256 password protection, file integrity
signature verification, and read-only filesystem locking for RULES.md.

Commands:
    python3 scripts/manage_rules.py set-password --password <pwd>
    python3 scripts/manage_rules.py lock
    python3 scripts/manage_rules.py unlock --password <pwd>
    python3 scripts/manage_rules.py verify

===============================================================================
"""

import argparse
import hashlib
import os
import stat
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES_PATH = os.path.join(PROJECT_ROOT, "RULES.md")
AUTH_PATH = os.path.join(PROJECT_ROOT, ".rules_auth")
SIG_PATH = os.path.join(PROJECT_ROOT, "RULES.md.sig")

DEFAULT_SALT = b"MeshControlPlaneRulesSalt2026"


def hash_password(password: str) -> str:
    """Computes PBKDF2 HMAC SHA-256 password hash."""
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        DEFAULT_SALT,
        100000
    ).hex()


def compute_file_hash(filepath: str) -> str:
    """Computes SHA-256 hash of file contents."""
    if not os.path.exists(filepath):
        return ""
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


def set_password(password: str):
    """Saves master password hash to .rules_auth."""
    hashed = hash_password(password)
    with open(AUTH_PATH, "w") as f:
        f.write(hashed + "\n")
    os.chmod(AUTH_PATH, 0o600)
    print("[SECURITY SUCCESS] Master Password successfully set and saved to .rules_auth!")


def verify_password(password: str) -> bool:
    """Verifies input password against stored hash."""
    if not os.path.exists(AUTH_PATH):
        print("[ERROR] No password initialized. Run: python3 scripts/manage_rules.py set-password --password <pwd>")
        return False
    with open(AUTH_PATH, "r") as f:
        stored_hash = f.read().strip()
    input_hash = hash_password(password)
    return input_hash == stored_hash


def lock_rules():
    """Calculates hash signature and sets RULES.md read-only (chmod 444)."""
    if not os.path.exists(RULES_PATH):
        print(f"[ERROR] {RULES_PATH} does not exist!")
        return False

    file_hash = compute_file_hash(RULES_PATH)
    with open(SIG_PATH, "w") as f:
        f.write(file_hash + "\n")

    # Set read-only permissions (chmod 444)
    os.chmod(RULES_PATH, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    print(f"[LOCKED] {RULES_PATH} is now LOCKED and set to Read-Only (chmod 444).")
    print(f"[SIGNATURE] Cryptographic Hash: {file_hash}")
    return True


def unlock_rules(password: str):
    """Verifies password and unlocks RULES.md (chmod 644) for editing."""
    if not verify_password(password):
        print("[ACCESS DENIED] Incorrect password! Cannot unlock RULES.md.")
        return False

    if os.path.exists(RULES_PATH):
        # Set read-write permissions (chmod 644)
        os.chmod(RULES_PATH, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        print(f"[UNLOCKED SUCCESS] RULES.md is now UNLOCKED for updates (chmod 644).")
        return True
    return False


def verify_rules_integrity():
    """Checks whether RULES.md matches its locked signature."""
    if not os.path.exists(RULES_PATH):
        print("[FAIL] RULES.md is missing!")
        return False
    if not os.path.exists(SIG_PATH):
        print("[WARNING] RULES.md signature file missing! Lock file to generate signature.")
        return False

    current_hash = compute_file_hash(RULES_PATH)
    with open(SIG_PATH, "r") as f:
        expected_hash = f.read().strip()

    if current_hash == expected_hash:
        print(f"[PASS] RULES.md Integrity Verification OK (Hash: {current_hash[:16]}...)")
        return True
    else:
        print(f"[VIOLATION WARNING] RULES.md has been modified without password authorization!")
        print(f"  Expected Hash : {expected_hash}")
        print(f"  Current Hash  : {current_hash}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Mesh Control Plane RULES.md Password Protection Tool")
    parser.add_argument("action", choices=["set-password", "lock", "unlock", "verify"], help="Security action")
    parser.add_argument("--password", help="Password for authentication")

    args = parser.parse_args()

    if args.action == "set-password":
        pwd = args.password or input("Enter new master password: ")
        set_password(pwd)
    elif args.action == "lock":
        lock_rules()
    elif args.action == "unlock":
        pwd = args.password or input("Enter master password: ")
        unlock_rules(pwd)
    elif args.action == "verify":
        verify_rules_integrity()


if __name__ == "__main__":
    main()
