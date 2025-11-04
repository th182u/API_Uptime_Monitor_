# API Uptime Monitor

Small Python script to periodically check a list of endpoints and send alerts via Telegram or Slack when an endpoint is down.

## Quick start

1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your credentials. Do not commit `.env` to GitHub.

4. Run the monitor:

```powershell
python API_Uptime_Monitor.py
```

## Security & publishing checklist

- Never commit your `.env` (credentials). Add it to `.gitignore`.
- Use `.env.example` to document required env vars without secrets.
- Pin dependency versions in `requirements.txt` before publishing.
- Run a dependency audit before publishing (see below).
- Consider removing or redacting any hard-coded sensitive data from source files.

## Dependency vulnerability scanning (recommended)

Use one of these tools locally before publishing:

```powershell
python -m pip install pip-audit
python -m pip_audit

# or
python -m pip install safety
safety check -r requirements.txt
```

## Improvements to consider

- Validate and escape alert content before sending (avoid HTML injection in Telegram).
- Check for non-200 success codes using `res.ok` or configurable expected status codes.
- Add retries/backoff and rate limiting to avoid spamming alerts.
- Add unit tests and CI checks (linting, tests, dependency audits).

