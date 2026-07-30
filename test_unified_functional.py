"""Functional smoke test: hit key routes and check status codes."""
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///unified_test.db")
os.environ.pop("PORT", None)

from wsgi import app
import json

client = app.test_client()

tests = [
    # (method, path, expected_min_status, description)
    ("GET", "/", 200, "Legacy home page"),
    ("GET", "/health", 200, "CRM health check"),
    ("GET", "/admin", 200, "Legacy admin"),
    ("GET", "/admin/load-demo", 200, "Legacy load demo"),
    ("GET", "/kanban", 200, "CRM kanban"),
    ("GET", "/contacts", 200, "CRM contacts list"),
    ("GET", "/api/cases", 401, "CRM cases (no JWT → 401)"),
    ("GET", "/status/doesnotexist", 404, "Legacy status (missing token)"),
]

passed = 0
failed = 0
for method, path, expected_min, desc in tests:
    resp = client.open(path, method=method)
    status_ok = resp.status_code >= expected_min
    mark = "✓" if status_ok else "✗"
    if status_ok:
        passed += 1
    else:
        failed += 1
    print(f"  {mark} {method:5s} {path:35s} → {resp.status_code} ({desc})")

print(f"\n{passed}/{passed+failed} tests passed")
