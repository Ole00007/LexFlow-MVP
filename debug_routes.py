"""Temporary diagnostic endpoint — remove after investigation."""
import sys
from app import app as intake_app

# Quick smoke test: does the app even boot?
try:
    with intake_app.test_client() as c:
        rules = sorted([str(r) for r in intake_app.url_map.iter_rules()])
        print("=== /app.py URL Map ===")
        for r in rules:
            print(r)
        print("\n=== Testing live routes ===")
        for path in ['/', '/admin', '/admin/load-demo', '/status/t', '/uploads/x']:
            resp = c.get(path)
            print(f"{path} -> {resp.status_code} ({len(resp.data)} bytes)")
except Exception as e:
    print(f"FATAL: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n=== Boot OK ===")
