# Procfile — used by Heroku, Railway, Render, and similar PaaS platforms.
# Backend code lives in the backend/ subdirectory.
web: cd backend && gunicorn wsgi:app --workers 4 --bind 0.0.0.0:$PORT --timeout 120 --log-level info
