FROM python:3.12-slim

WORKDIR /app
COPY services/reports/requirements.txt ./services/reports/requirements.txt
COPY libs ./libs
COPY services/reports ./services/reports
WORKDIR /app/services/reports
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["gunicorn", "--chdir", "/app/services/reports", "reports_service.wsgi:application", "--bind", "0.0.0.0:8000"]
