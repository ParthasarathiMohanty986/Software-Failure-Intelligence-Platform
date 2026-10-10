@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Project virtual environment missing: .venv\Scripts\python.exe
  exit /b 1
)
".venv\Scripts\python.exe" backend\manage.py runserver 127.0.0.1:8000
