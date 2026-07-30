"""Smoke-test: boot the unified app and dump all registered routes."""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///unified_test.db")

# Boot unified app
from wsgi import app

print(f"App name: {app.name}")
print(f"Secret key: {bool(app.secret_key)}")
print(f"Templates dirs: {app.template_folder}")

print("\n--- Registered Routes ---")
rules = sorted(app.url_map.iter_rules(), key=lambda r: r.rule)
for rule in rules:
    methods = sorted(rule.methods - {"HEAD", "OPTIONS"})
    print(f"  {methods} {rule.rule} -> {rule.endpoint}")

print(f"\nTotal routes: {len(rules)}")
