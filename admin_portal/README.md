# sms_frwd Admin Portal

Flask + PostgreSQL admin portal that is the backend for the `sms_frwd`
Android app: devices self-register, send heartbeats, and upload matched
bank SMS messages here for you to browse, categorize, and audit.

## Local setup

1. **Start Postgres.** Docker Desktop must be running first:
   ```
   docker compose up -d
   ```
   If you don't want to use Docker, install PostgreSQL natively and create
   a database/user matching `.env`'s `DATABASE_URL` instead.

2. **Install dependencies** (Python 3.11+):
   ```
   python -m pip install -r requirements-dev.txt
   ```

3. **Configure environment**: copy `.env.example` to `.env` and adjust
   `SECRET_KEY`/`DATABASE_URL` as needed. `python-dotenv` loads `.env`
   automatically via `.flaskenv`/Flask's CLI.

4. **Run migrations**:
   ```
   flask db upgrade
   ```

5. **Create your first admin login** (this is the only way to provision
   portal accounts — there's no self-service signup):
   ```
   flask create-admin
   ```

6. **Run the dev server**:
   ```
   flask run --debug
   ```
   Visit `http://localhost:5000/login`.

## Running tests

Tests run against an in-memory SQLite database, no Postgres/Docker
required:
```
python -m pytest tests/ -v
```

## Verifying the API end-to-end (no Android app needed)

With the dev server running:

```bash
# 1. Register a device
curl -X POST localhost:5000/api/v1/register-device \
  -H "Content-Type: application/json" \
  -d '{"device_id":"11111111-1111-1111-1111-111111111111","device_name":"Test Phone"}'
# -> capture "api_token" from the response

TOKEN="<paste api_token here>"

# 2. Heartbeat
curl -X POST localhost:5000/api/v1/heartbeat -H "Authorization: Bearer $TOKEN"

# 3. Upload a message
curl -X POST localhost:5000/api/v1/messages -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"client_message_id":"m1","sender_raw":"AX-HDFCBK-S","sender_matched":"HDFCBK","body":"Rs.500 debited from A/c XX1234","received_at":"2026-07-14T10:00:00Z"}]}'
# -> expect category: "DEBIT"

# 4. Re-post the same client_message_id -> expect duplicates: 1

# 5. Fetch device config
curl localhost:5000/api/v1/device-config -H "Authorization: Bearer $TOKEN"
```

Then log into the portal and confirm: Dashboard totals reflect the above,
Messages page shows the full untruncated body with category DEBIT, Devices
page shows the device Online, Audit Logs shows DEVICE_REGISTER and
MESSAGE_UPLOAD entries.

To confirm device revocation enforces data isolation: revoke the device
from its detail page in the portal, then re-run step 3's curl — expect
`401`.

To confirm the offline sweep: temporarily set `DEVICE_OFFLINE_THRESHOLD_MINUTES=0`
in `.env`, restart the dev server, wait ~60s (the sweep runs every minute)
— the device should flip to Offline on the Devices page and a
`DEVICE_DISCONNECT` audit entry should appear.

## Deployment notes

- Run behind a reverse proxy that terminates TLS (e.g. **Caddy** — it
  handles automatic HTTPS with essentially no config, a good fit for a
  single-server deployment). `ProxyFix` is already wired in so
  `X-Forwarded-Proto`/`X-Forwarded-Host` are trusted.
- Use `FLASK_CONFIG=app.config.ProdConfig` in production (enables
  `SESSION_COOKIE_SECURE`).
- Run via `gunicorn wsgi:app` rather than `flask run`.
- Set a real `SECRET_KEY` (not the dev default) and a real `DATABASE_URL`.
- The in-process APScheduler sweep job (device online/offline detection)
  runs inside the web process itself — if you run multiple gunicorn
  workers, only one process needs `ENABLE_STATUS_SWEEP` on to avoid
  duplicate sweeps; this isn't currently worker-count-aware, so pin to a
  single worker or add that guard before scaling out.

## Known limitations (deliberately out of scope for v1)

- No AdminUser self-service signup/password reset — provision accounts via
  `flask create-admin` only.
- No Celery/task queue — background work (the status sweep) runs
  in-process via APScheduler, appropriate at this project's scale.
- No per-heartbeat history — only the latest `last_seen_at` is tracked.
- `SETTINGS_CHANGE` audit event type exists but has no settings page
  wired to it yet (no settings page exists in v1).
