# Deploy on Render

This configuration serves the React build and Django API from one HTTPS origin.
It uses PostgreSQL, WhiteNoise for assets, and Gunicorn for the web process.
The Docker runtime includes only the verified Groq analysis path; retrieval uses
keyword matching without Google's optional embedding integration.

## Deployment

1. Push this repository, including `Dockerfile` and `render.yaml`, to GitHub.
2. Sign in to Render. Choose **New > Blueprint**, connect this repository,
   and select the branch containing these files.
3. Review the proposed free web service and free PostgreSQL database.
4. Enter `GROQ_API_KEY` as a secret in Render's environment configuration.
   Do not commit it or enter it in a build command. Render generates the Django
   secret and supplies the database connection automatically.
5. Deploy and wait for the service to become healthy. Open its HTTPS URL.
6. Register a new account, upload the files from `demo-files`, and investigate.

Local users, logs, and reports are not copied to Render. The hosted database is
new. Browser calls use `/api`; Vite proxies that path to port 8000 locally.
Deep links such as `/incidents` are served by Django in production.

## Validation

- `/health/` returns `{"status":"ok"}`.
- `/` and `/incidents` load the React app and its assets.
- Registration and login work with session cookies and CSRF protection.
- Logs upload, incidents are detected, and reports are persisted.
- Reloading a report retains it in PostgreSQL.

The container applies migrations before starting Gunicorn. Keep one service
instance for this demo; use a dedicated migration phase before scaling.
The model call is synchronous, with an application timeout and a longer web
worker timeout. Larger deployments should move investigations to a job queue.

## Free plan limits

Render's free web service sleeps after 15 minutes of inactivity. Its free
PostgreSQL database expires after 30 days and does not include backups. Export
important data or upgrade before expiry. Existing free-database usage may
prevent creating another database in the same workspace. Do not substitute
SQLite on the ephemeral web-service filesystem.

Reference: https://render.com/docs/free

## Optional Google support

The main development requirements include LangChain's Google integration.
To use it in this container, add `langchain-google-genai` to the production
requirements, configure a working Google key and model, and rebuild. The
embedding service currently hardcodes its model; update and validate that
integration before describing production retrieval as semantic search.
