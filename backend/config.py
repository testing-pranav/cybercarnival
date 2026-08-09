"""
Central configuration. Loaded once at startup. Fails fast (refuses to boot)
if required secrets are missing in production instead of silently falling
back to an insecure default.
"""
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

ENV = os.environ.get("FLASK_ENV", "development")
IS_PRODUCTION = ENV == "production"

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if IS_PRODUCTION:
        raise RuntimeError(
            "SECRET_KEY is not set. Refusing to start in production without it. "
            "Set SECRET_KEY in your .env file."
        )
    # Dev-only fallback so `flask run` works locally without setup.
    # Regenerated every restart on purpose — never persisted, never used in prod.
    SECRET_KEY = secrets.token_hex(32)

DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

REGISTRATIONS_FILE = DATA_DIR / "registrations.json"
EVENTS_FILE = DATA_DIR / "events.json"
ADMINS_FILE = DATA_DIR / "admins.json"
AUDIT_LOG_FILE = DATA_DIR / "audit_log.json"
LOGIN_ATTEMPTS_FILE = DATA_DIR / "login_attempts.json"

ALLOWED_ORIGINS = [
    o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()
]

RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

# Where the built frontend (`npm run build` / `pnpm build` -> static export)
# lives. Defaults to the sibling frontend/out folder in the combined project
# layout (cybercarnival/backend + cybercarnival/frontend). Override with
# FRONTEND_DIST_DIR in .env if you keep a different layout.
FRONTEND_DIST_DIR = Path(
    os.environ.get("FRONTEND_DIST_DIR", str(BASE_DIR.parent / "frontend" / "out"))
).resolve()

# Hard ceiling on request body size (bytes) — blocks oversized-payload DoS attempts.
MAX_CONTENT_LENGTH = 64 * 1024  # 64 KB is generous for a registration form

SESSION_COOKIE_SECURE = IS_PRODUCTION
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
PERMANENT_SESSION_LIFETIME_SECONDS = 60 * 60 * 4  # 4 hours

# Login brute-force protection
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_SECONDS = 15 * 60
