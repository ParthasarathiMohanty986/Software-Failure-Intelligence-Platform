# AI Software Failure Intelligence

AI Software Failure Intelligence (SFI) is a local incident-analysis workspace for ingesting application logs, grouping recurring errors into incidents, reviewing pipeline activity, and searching indexed runbooks. It consists of a Django REST API and a React dashboard.

## Stack

- Backend: Python 3.12+, Django, Django REST Framework
- Frontend: React, TypeScript, Vite, React Router
- Storage: SQLite by default; a `DATABASE_URL` can be used for PostgreSQL
- AI: optional Gemini integration; local fallback behavior is configured by default for embeddings

## Requirements

- Python 3.12 or newer
- Node.js 20.19+ or 22.12+
- npm

## Run Locally (Windows PowerShell)

From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
python backend\manage.py migrate
python backend\manage.py runserver
```

In a second terminal, start the frontend:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Open <http://localhost:5173>. The API runs at <http://localhost:8000/api/>. Create an account with the dashboard's Register control before using authenticated workspace endpoints.

For other operating systems, create and activate a Python virtual environment with the platform's normal commands, then run the same `pip`, migration, and Django commands from the repository root.

## Configuration

Copy `backend/.env.example` to `backend/.env` and adjust values as needed. The defaults use SQLite and the local embedding fallback, so external services are not required for basic local use. To enable Gemini features, provide a valid `GOOGLE_API_KEY` and configure `AI_PROVIDER`, `AI_MODEL`, and `EMBEDDING_MODEL` as appropriate.

Do not commit `backend/.env` or put API keys in source control. The development settings are not production-ready: set a secure `DJANGO_SECRET_KEY`, disable `DJANGO_DEBUG`, restrict `ALLOWED_HOSTS` and CORS, and configure production-grade storage and deployment settings before exposing the service.

## Workspace Areas

- **Dashboard**: log and incident summaries, error trends, and service metrics
- **Logs**: upload CSV or JSON logs and review ingested entries
- **Incidents**: inspect grouped errors and update incident status
- **AI investigations**: review saved investigation results
- **Knowledge base**: index text or Markdown runbooks and search retrieved content
- **Pipeline**: inspect log ingestion runs

The main API route groups are `/api/auth/`, `/api/logs/`, `/api/incidents/`, `/api/investigations/`, `/api/knowledge/`, and `/api/analytics/`. Django admin is available at `/admin/` after creating a superuser with `python backend/manage.py createsuperuser`.

## Checks

Run Django's configuration check and tests from the repository root:

```powershell
python backend\manage.py check
python backend\manage.py test
```

Build the frontend:

```powershell
Set-Location frontend
npm run build
```
