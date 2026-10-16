FROM node:22-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build -- --base=/static/

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements-render.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend /build/frontend/dist/ ./frontend/dist/
RUN python backend/manage.py collectstatic --noinput
RUN useradd --create-home app && chown -R app:app /app
USER app
WORKDIR /app/backend
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-10000} --workers 1 --threads 4 --timeout 180 --access-logfile - --error-logfile -"]
