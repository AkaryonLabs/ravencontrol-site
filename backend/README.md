# Raven Control Backend

Python backend for the Raven Control MVP.

## Render Settings

Create a new **Web Service** on Render from the GitHub repo.

- Runtime: `Python 3`
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `python app.py`
- Health Check Path: `/api/health`

Environment variables:

- `ANTHROPIC_API_KEY`: your Claude API key
- `RAVEN_CLAUDE_MODEL`: `claude-haiku-4-5`
- `RESEND_API_KEY`: your Resend API key
- `RAVEN_NOTIFY_EMAIL`: where internal intake alerts go, for example `akeemandrew@ravencontrol.com`
- `RAVEN_FROM_EMAIL`: sender, for example `Raven Control <alerts@send.ravencontrol.com>`
- `RAVEN_REPLY_TO`: reply address, for example `verify@ravencontrol.com`
- `RAVEN_CONSOLE_URL`: Render console URL, for example `https://ravencontrol-site.onrender.com`

Optional:

- `OPENAI_API_KEY`
- `RAVEN_OPENAI_MODEL`

## Endpoints

- `GET /api/health`
- `GET /api/state`
- `POST /api/public-intake`
- `POST /api/review`
- `POST /api/cases/<case_id>/review`

## Important

The current backend saves cases to local JSON. That is fine for testing, but
Render instances can lose local files across deploys/restarts unless you add a
persistent disk or move data to Supabase/Postgres.
