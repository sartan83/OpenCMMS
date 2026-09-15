# Microservices Migration

## Phase 0: Foundations

Run the application stack locally with Docker Compose:

```bash
cp .env.example .env
# Set SECRET_KEY in .env before starting
docker compose up --build
```

The gateway is available at http://localhost/ and exposes the web application,
API, admin, static files, and health endpoint.

## Phase 1: Service boundaries

## Phase 2: Shared contracts and data ownership

## Phase 3: Service extraction

## Phase 4: Gateway cutover
