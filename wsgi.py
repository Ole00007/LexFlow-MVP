"""WSGI entry point for Railway deployment."""

import os
from crm import create_app

# Force rebuild marker
BUILD_VERSION = "20260720_v2"

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
