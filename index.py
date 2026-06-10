# Legacy entrypoint — Vercel uses app.py directly via zero-config detection.
from app import app as application

app = application