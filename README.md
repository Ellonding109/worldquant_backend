wq-brain-backend

This repository is the backend service for WQ Brain Manager.

Run locally

1. Create virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Set environment variables (example):

```bash
export SECRET_KEY="your-secret"
export DATABASE_PATH="wq_brain.db"
```

3. Run locally:

```bash
python wsgi.py
# or
gunicorn app:app --bind 0.0.0.0:5000
```

Deploy to Render

- Connect this repo to Render as a Web Service.
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Add Render environment variables: `SECRET_KEY`, `DATABASE_PATH`, `ENCRYPTION_KEY` (and any API tokens).