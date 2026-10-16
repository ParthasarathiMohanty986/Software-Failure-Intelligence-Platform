# Incident Intelligence Platform

## Start locally on Windows

Open two terminals in this project folder.

Backend:

```powershell
.\start-backend.cmd
```

Frontend:

```powershell
.\start-frontend.cmd
```

Open http://localhost:5173 for the application. Django admin is at
http://localhost:8000/admin/. The backend root `/` has no route, so a 404
there is expected. Stop each server with Ctrl+C in its terminal.

The backend launcher uses `.venv\Scripts\python.exe` explicitly because the
system `python` may point to Anaconda without Django. It starts from the project
root so the existing relative SQLite database path stays consistent.

The frontend launcher uses a project-local Node.js 22 runtime. System Node.js
20.17.0 is below the version required by the installed Vite. To restore the
local runtime if missing, run from the project root:

```powershell
npm.cmd install --prefix .runtime --no-save --package-lock=false node@22
```

The launchers use the existing Python environment, frontend dependencies, and
`backend/.env`. They do not install dependencies automatically.


## End-to-end incident demo

1. Upload `demo-files/payment-runbook.md` on Knowledge.
2. Upload `demo-files/payment-logs.json` on Logs. Uploads now run incident grouping.
3. On Incidents, click Detect incidents to also process previously uploaded logs.
4. Click Investigate. The report contains generated analysis and expandable supporting evidence.
5. Existing reports are accessible from AI investigation history. Mark resolved only after verifying recovery.

Configure `GOOGLE_API_KEY` locally in `backend/.env`, and set `AI_MODEL=gemini-2.5-flash` (or an available model for your account). Restart the backend after changes. No key means evidence collection still runs but AI analysis is explicitly marked failed; no simulated diagnosis is generated. Model requests send the selected logs and retrieved runbook excerpts to Google.

Retrieval reports `semantic` when compatible Google embeddings exist, otherwise `keyword`. Legacy placeholder vectors are not treated as semantic embeddings. Re-upload runbooks after configuring working embeddings to index them again. Investigations currently execute synchronously with a model request timeout, rather than through a background queue.

Validation: `.\.venv\Scripts\python.exe backend/manage.py test logs investigations --noinput`
Tests use an isolated database and mock the provider to verify successful integration and failure behavior; live Gemini verification requires a configured API key.
