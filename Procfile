# Procfile — used by Heroku, Railway, Render, and similar PaaS platforms.
# Micro-agents are NOT listed here; they must be managed separately via
# supervisord, Docker Compose, or a multi-dyno setup.
web: gunicorn wsgi:app --workers 4 --bind 0.0.0.0:$PORT --timeout 120 --log-level info
