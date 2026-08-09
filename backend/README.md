# CyberCarnival Backend + Admin Panel

Flask API + secure admin dashboard for CyberCarnival. Storage is plain
JSON files under `data/` (no database, per project requirement) — every
write is atomic and file-locked so concurrent requests can't corrupt data.

The frontend (`cyber-carnival-2026`) is untouched. This backend is
designed to be called from it later; nothing here modifies that project.

## What's in here

- **Public API** — `GET /api/health`, `GET /api/events`, `POST /api/registrations`
- **Admin panel** — `/admin/login`, `/admin/` dashboard (Overview, Registrations,
  Events, Audit Log), backed by `/admin/api/*` JSON endpoints
- **Storage** — `data/events.json`, `data/registrations.json`, `data/admins.json`,
  `data/audit_log.json`, `data/login_attempts.json` — created automatically

## 1. Setup

```bash
cd cybercarnival-backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Edit `.env`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"   # paste into SECRET_KEY
```

Set `ALLOWED_ORIGINS` to wherever the frontend is served from
(e.g. `http://localhost:3000` in dev, your real domain in prod).

## 2. Seed data

```bash
python3 seed_events.py   # loads the 11 events (already run once — data/events.json ships pre-seeded)

# Create your first admin account (password hashed on write, never stored in plaintext):
python3 seed_admin.py
```
It'll prompt for a username and password interactively (min 12 characters).
You can add more admins later the same way, or extend `admin_service.create_admin`
into an "invite" flow if you need self-service admin creation.

## 3. Run (development)

```bash
python3 app.py
# or
flask --app app run
```
Visit `http://127.0.0.1:5000/admin/login`.

## 4. Run (production)

Never use the Flask dev server in production. Run behind gunicorn, and put
gunicorn behind a reverse proxy (nginx/Caddy) that terminates TLS:

```bash
export FLASK_ENV=production   # in .env — enables Secure cookies + HSTS, fails fast without SECRET_KEY
gunicorn -w 4 -b 127.0.0.1:8000 app:app
```

nginx (sketch):

```nginx
server {
    listen 443 ssl;
    server_name your-domain.example;
    # ssl_certificate / ssl_certificate_key ...

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
    }
}
```

Run gunicorn under systemd (or similar) so it restarts on crash/reboot.

If you run more than one gunicorn worker, set `RATELIMIT_STORAGE_URI` in
`.env` to a shared store (e.g. `redis://localhost:6379`) — the default
`memory://` limiter state is per-process and won't be shared across workers.

## 4b. Deploying backend on Render + frontend on Vercel

This works, but it's a **cross-origin split** (two different domains), not
the merged same-origin setup described above — different config applies.

**⚠️ Read this before deploying — JSON storage + Render's disk:**
Render's filesystem is ephemeral on every plan except when you explicitly
attach a **Persistent Disk**. Without one, every redeploy, restart, or scale
event **wipes `data/*.json` completely** — all registrations, admins, and
events gone, silently, no warning. This is not a theoretical risk, it will
happen the first time Render restarts your instance.

Fix: in the Render dashboard, add a **Persistent Disk**, mount it (e.g. at
`/var/data`), and set `DATA_DIR` — actually this project derives `DATA_DIR`
from `BASE_DIR` in `config.py`, so instead set the disk's mount path and
point storage there by exporting `FRONTEND_DIST_DIR`-style override, or
simpler: mount the disk directly at `<repo>/data` in Render's disk config
so the existing `data/` folder IS the persistent volume. Confirm this in
Render's dashboard before trusting any data you put in it.

**Render setup:**
1. New Web Service → connect this repo, root directory `backend/`
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`
4. Environment variables (Render dashboard, not `.env` — Render doesn't read that file):
   - `SECRET_KEY` — generate one, paste it in
   - `FLASK_ENV=production`
   - `ALLOWED_ORIGINS=https://your-frontend.vercel.app`
   - `RATELIMIT_STORAGE_URI=memory://` (fine for `-w 1`; use Redis if you scale workers)
5. Attach a Persistent Disk, mounted so it covers `backend/data/`
6. After first deploy, SSH/shell into the instance (Render supports this) and run `python3 seed_admin.py` once to create your admin login — or set `BOOTSTRAP_ADMIN_USERNAME`/`BOOTSTRAP_ADMIN_PASSWORD` as env vars temporarily and run it, then remove them.

**Vercel setup (frontend):**
1. Import this repo, root directory `frontend/`
2. Framework preset: Next.js (auto-detected)
3. Project Settings → Environment Variables → add `NEXT_PUBLIC_API_URL` = your Render backend URL (e.g. `https://cybercarnival-backend.onrender.com`)
4. Deploy — Vercel runs `next build` natively, no static export needed for this split setup (the `output: 'export'` merged-serving mode was only for running both from one Flask process; not used here)

**What changes vs. the merged single-process setup:**
- CORS is now required and active — `ALLOWED_ORIGINS` on the backend must exactly match your Vercel domain (`https://...vercel.app`, with `https://`, no trailing slash)
- Admin panel is only reachable directly on the Render URL (`https://your-backend.onrender.com/admin/login`) — there's no admin UI on the Vercel-hosted frontend, by design
- Render's free tier spins down on inactivity — first request after idle can take 30–60s to wake up; registrations submitted during that window will just be slow, not lost

## 4c. Deploying both on Railway (short-term / few-days hosting)

Same cross-origin split as Render+Vercel above, just both services on one
platform. Push this repo to GitHub first, then in Railway:

1. **New Project → Deploy from GitHub repo**, pick your repo.
2. Railway will create one service from the repo root — add a **second
   service** from the same repo (⋮ menu → "New Service" → same repo) so you
   end up with two services total, one per app.
3. **Backend service** → Settings → set root directory to `backend`.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn -w 2 -b 0.0.0.0:$PORT app:app`
   - Variables tab: `SECRET_KEY` (generate one), `FLASK_ENV=production`,
     `ALLOWED_ORIGINS=https://<your-frontend-service>.up.railway.app`,
     `RATELIMIT_STORAGE_URI=memory://`
   - **Attach a Volume** (Settings → Volumes), mounted at `/app/data` —
     Railway's filesystem is ephemeral exactly like Render's; without a
     volume, `data/*.json` resets on every redeploy/restart, same warning
     as above. For a few-days test this might be acceptable risk, but know
     that's the tradeoff if you skip it.
   - After first deploy, use Railway's shell (or a one-off run) to execute
     `python3 seed_admin.py` once to create your admin login.
4. **Frontend service** → Settings → set root directory to `frontend`.
   - Railway auto-detects Next.js (Nixpacks) — default build (`npm run
     build`) and start (`npm start`) commands work as-is, no static export
     needed here either.
   - Variables tab: `NEXT_PUBLIC_API_URL=https://<your-backend-service>.up.railway.app`
5. Both services get a free `*.up.railway.app` HTTPS domain automatically —
   grab the actual URLs Railway assigns and go back to steps 3/4 to fill in
   the real values (there's a brief chicken-and-egg step since each needs
   the other's URL — deploy once, copy the URLs, update the env vars, redeploy).


## 5. Registering the frontend against this API

The frontend currently has placeholder `#register` links and no real form.
Once you're ready to wire it up:

```js
// GET events for a picker
fetch('https://api.your-domain.example/api/events')

// Submit a registration
fetch('https://api.your-domain.example/api/registrations', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ name, email, phone, event_id, college, team_members }),
})
```
No credentials/cookies needed for these — they're public, rate-limited,
CORS-restricted to `ALLOWED_ORIGINS`.

## Security measures (what's actually enforced, not just claimed)

| Area | Measure |
|---|---|
| Passwords | scrypt hashing (werkzeug), never stored/logged in plaintext |
| Admin sessions | HttpOnly, SameSite=Lax cookies, Secure in production, 4h expiry |
| CSRF | Flask-WTF, enforced on every admin state-change; public JSON API is exempt (no cookies to forge) |
| Brute force | Per-username+IP lockout after 5 failed logins (15 min), rate limiting on login and registration endpoints |
| User enumeration | Login always takes the same code path/timing whether the username exists or not; error message never reveals which field was wrong |
| Input validation | Allow-list regex validation on every public field; nothing free-text reaches storage or templates unsanitized |
| XSS | Jinja2 autoescaping in all admin templates; admin JS also escapes before injecting into the DOM |
| Injection | No SQL (no DB); JSON writes are structured, never string-concatenated |
| CORS | Public API locked to explicit `ALLOWED_ORIGINS`; admin routes are same-origin only, not exposed via CORS at all |
| Headers | CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff, Referrer-Policy, HSTS (prod) |
| Secrets | `.env`-only, `.gitignore`d; app refuses to boot in production without `SECRET_KEY` |
| DoS | 64KB request body cap; rate limits on the two write-heavy public/auth endpoints |
| Data integrity | Every JSON write is atomic (`tempfile` + `os.replace`) and file-locked — no torn writes under concurrent requests |
| Audit trail | Every admin login, failed login, edit, delete, and export is logged with actor, IP, timestamp in `data/audit_log.json`, viewable in the Audit Log tab |

### Known trade-offs, worth knowing about

- **JSON storage, not a DB**: fine for this event's scale, but `read_all()` loads
  the whole file into memory — if registrations grow into the tens of thousands,
  move to a real DB (the `storage/json_store.py` interface was kept narrow
  specifically so swapping it out later doesn't require touching route/service code).
- **Single-process rate limiting**: `memory://` limiter storage doesn't share
  state across multiple gunicorn workers. Fine for `-w 1`; use Redis for `-w 4+`.
- **No email verification**: registrations aren't confirmed via email link;
  add that if you want to stop fake/typo emails from occupying slots.
