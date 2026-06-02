"""
wsgi.py
-------
Production WSGI entrypoint for govManage.

Run with Gunicorn (Linux/macOS):
    gunicorn wsgi:app --workers 4 --bind 0.0.0.0:5000 --timeout 120

Run with Waitress (Windows — no Gunicorn support):
    waitress-serve --port=5000 wsgi:app
"""

from app import app  # noqa: F401  — re-exported for WSGI servers

if __name__ == "__main__":
    # Fallback: run with Flask dev server (NOT for production)
    import os
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
