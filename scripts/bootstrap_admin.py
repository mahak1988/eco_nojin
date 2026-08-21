"""
Bootstrap the first admin (Phase 5 readiness).

Usage:
    python scripts/bootstrap_admin.py you@example.com
    python scripts/bootstrap_admin.py you@example.com --create --password ***
    python scripts/bootstrap_admin.py you@example.com --set-password ***

Idempotent: re-running on the same email is a no-op (still prints state).
``--create`` registers the user when the email does not exist yet
(role=admin, is_active=True) — needed when the account was never
registered through the site.
``--set-password <new>`` resets the password of an EXISTING user
(e.g. change the admin password after bootstrap).
"""
from __future__ import annotations

import argparse
import sys
from typing import Optional

from database import models
from database.config import SessionLocal
from services.api_gateway.auth import hash_password

ADMIN_ROLE = "admin"


def bootstrap_admin(
    email: str,
    create: bool = False,
    password: str = "",
    set_password: str = "",
) -> Optional[str]:
    """Set role=admin for ``email`` (optionally creating it / resetting pwd)."""
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        if user is None:
            if not create:
                return None
            if not password:
                raise ValueError("--password is required with --create")
            user = models.User(
                email=email,
                full_name=email.split("@")[0],
                hashed_password=hash_password(password),
                role=ADMIN_ROLE,
                is_active=True,
            )
            db.add(user)
            db.commit()
            print(f"OK: created {email} with role=admin")
            return user.role
        if set_password:
            if len(set_password) < 6:
                raise ValueError("--set-password must be at least 6 characters")
            user.hashed_password = hash_password(set_password)
            db.commit()
            print(f"OK: password updated for {email}")
        if user.role != ADMIN_ROLE:
            user.role = ADMIN_ROLE
            db.commit()
            print(f"OK: {email} -> role=admin")
        else:
            print(f"OK: {email} is already admin")
        return user.role
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap the first admin user.")
    parser.add_argument("email", help="email of the admin account")
    parser.add_argument("--create", action="store_true", help="create the user if missing")
    parser.add_argument("--password", default="", help="password (required with --create)")
    parser.add_argument("--set-password", default="", help="reset password for an existing user")
    args = parser.parse_args()

    email = args.email.strip().lower()
    if not email or "@" not in email:
        print("error: a valid email is required")
        return 2
    try:
        result = bootstrap_admin(
            email,
            create=args.create,
            password=args.password,
            set_password=args.set_password,
        )
    except ValueError as exc:
        print(f"error: {exc}")
        return 2
    if result is None:
        print(
            f"error: no user found with email '{email}' — "
            "register first via the site, or re-run with --create --password"
        )
        return 1
    print(f"done: role={result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
