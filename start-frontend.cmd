@echo off
setlocal
cd /d "%~dp0"
set "PROJECT_NODE=%~dp0.runtime\node_modules\node\bin\node.exe"
if not exist "%PROJECT_NODE%" (
  echo Local Node runtime missing. Run from the project root:
  echo npm.cmd install --prefix .runtime --no-save --package-lock=false node@22
  exit /b 1
)
if not exist "frontend\node_modules\vite\bin\vite.js" (
  echo Frontend dependencies missing. Run npm.cmd install from frontend first.
  exit /b 1
)
cd frontend
"%PROJECT_NODE%" node_modules\vite\bin\vite.js --host 127.0.0.1 --port 5173 --strictPort
