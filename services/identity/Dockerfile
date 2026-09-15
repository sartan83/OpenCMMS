FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
COPY libs ./libs
COPY users ./users
COPY services/identity ./services/identity
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["gunicorn", "--chdir", "/app/services/identity", "identity_service.wsgi:application", "--bind", "0.0.0.0:8000"]
