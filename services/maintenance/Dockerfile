FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
COPY libs ./libs
COPY services/maintenance ./services/maintenance
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["gunicorn", "--chdir", "/app/services/maintenance", "maintenance_service.wsgi:application", "--bind", "0.0.0.0:8000"]
