# Phase 4 gateway cutover runbook

Phase 4 switches each API domain independently from the monolith to its
service. The gateway reads the `*_UPSTREAM` values when its container starts;
recreate the gateway after changing a value so nginx's template is rendered
again.

## Order

Cut over domains in this order:

1. assets
2. spareparts
3. maintenance
4. workorders
5. inspections
6. reports

Assets go first because the other services cache asset events. Reports go last
because its read side needs every producer to be live.

## Per-domain procedure

For each domain, replace `<domain>` and `<svc>` with the values in the table
below.

| Domain | Service |
| --- | --- |
| assets | assets |
| spareparts | spareparts |
| maintenance | maintenance |
| workorders | workorders |
| inspections | inspections |
| reports | reports |

1. Bring up the service, its database, and its consumer when applicable:

   ```bash
   docker compose up -d <svc> <svc>-db [<svc>-consumer]
   ```

2. Freeze writes for this domain, then import existing data while
   `SOURCE_DATABASE_URL` points to the monolith database:

   ```bash
   SOURCE_DATABASE_URL="$MONOLITH_DATABASE_URL" \
     docker compose exec <svc> \
     python services/<svc>/manage.py import_from_monolith
   ```

   The write freeze is important: writes made to the monolith after import
   are not replayed into the extracted service.

3. Verify the service health endpoint:

   ```bash
   curl http://<svc>:8000/health/
   ```

4. Set `<DOMAIN>_UPSTREAM=<svc>:8000` in `.env` and recreate the gateway.
   Recreating, rather than only reloading nginx, is required because the
   official image renders templates at container startup:

   ```bash
   docker compose up -d gateway
   ```

   `docker compose exec gateway nginx -s reload` is insufficient: it reloads
   the existing configuration but does not re-render the templates.

5. Smoke-check the domain through the gateway:

   ```bash
   curl -H "Authorization: Bearer $TOKEN" \
     http://localhost/api/<domain>/
   ```

6. Roll back by unsetting the domain variable (which restores `web:8000`) and
   recreating the gateway:

   ```bash
   unset <DOMAIN>_UPSTREAM
   docker compose up -d gateway
   ```

## Retiring the monolith

After all six upstream variables are set and `/api/auth/` is served by
identity, the `web`, `celery-worker`, `celery-beat`, and `db` services can be
removed. Until the later retirement step, these routes still point to the
monolith:

- `/`
- `/static/`
- `/admin/`
- `/health/`

The static SPA needs a new hosting home before the monolith can be removed.
That hosting migration is Phase 4 step 10 and is outside this cutover change.
