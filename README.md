# CyberCarnival — Full Project

```
cybercarnival/
├── frontend/    Next.js site (landing page + /events)
└── backend/     Flask API + admin panel (JSON file storage)
```

## Steady-state: one command

Once built, the backend serves the frontend itself — `python app.py` alone
runs the whole site (frontend pages + API + admin), same origin, no CORS,
no second process.

**First-time setup (run these once, or after any frontend change):**

```
cd cybercarnival/frontend
pnpm install          # or: npm install
pnpm build             # or: npm run build   → outputs frontend/out/
```

**Then, every time you want to run the site:**

```
cd cybercarnival/backend
python3 -m venv venv && venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env
python3 seed_admin.py        # first time only — creates your admin login
python3 app.py
```

→ http://127.0.0.1:5000 — the landing page, `/events`, everything.
→ http://127.0.0.1:5000/admin/login — admin panel.

`backend/data/events.json` ships pre-seeded with the 11 events. No database —
plain JSON files, atomic writes, as requested.

## Editing the frontend

Edit files under `frontend/`, then re-run `pnpm build` (or `npm run build`)
before your next `python app.py` — Flask serves whatever's currently in
`frontend/out/`, it doesn't watch for changes.

For live-reload while actively developing frontend UI, run the two apps
separately instead:
```
# terminal 1
cd cybercarnival/backend && python3 app.py          → :5000 (API + admin)
# terminal 2
cd cybercarnival/frontend && pnpm dev                 → :3000 (hot reload)
```
In this mode the frontend calls the backend at `http://localhost:5000`
(set in `frontend/.env.development`, dev-only, not used by `pnpm build`).

## Deploying (Render + Vercel)

The one-command setup above is for local use. For hosting on Render
(backend) + Vercel (frontend) — two separate domains, cross-origin — see
`backend/README.md` → "Deploying backend on Render + frontend on Vercel".
Read the persistent-disk warning in there before you deploy — Render wipes
the JSON data files on every restart unless you attach a persistent disk.

## What's connected now

- `/events` — Technical / Non-Technical toggle, posters, per-event register button
- Register button → modal → `POST /api/registrations` on the backend
- Event IDs are fetched live from the backend (`GET /api/events`) and matched
  by name to the poster/description data in `frontend/lib/events-data.ts`
- Sponsors: intentionally untouched — waiting on your assets/list for that section

