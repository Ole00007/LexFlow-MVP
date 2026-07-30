"""Seed an initial admin user for the CRM.

Usage:
    python scripts/seed_admin.py

Environment variables (optional):
    SEED_EMAIL    — admin email (default: admin@lexflow.local)
    SEED_PASSWORD — admin password (default: ChangeMe123!)
"""
import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crm import create_app
from crm.extensions import db
from crm.models.user import User

EMAIL = os.environ.get("SEED_EMAIL", "admin@lexflow.local")
PASSWORD = os.environ.get("SEED_PASSWORD", "ChangeMe123!")


def main():
    app = create_app()
    with app.app_context():
        existing = User.query.filter_by(email=EMAIL).first()
        if existing:
            print(f"User {EMAIL} already exists (id={existing.id}). Skip.")
            sys.exit(0)

        user = User(email=EMAIL)
        user.set_password(PASSWORD)
        db.session.add(user)
        db.session.commit()
        print(f"Created admin user: {EMAIL} / {PASSWORD}")
        print(f"  id={user.id}, role={user.role}")


if __name__ == "__main__":
    main()
