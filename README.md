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
