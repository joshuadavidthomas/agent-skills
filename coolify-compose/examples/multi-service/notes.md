# Multi-Service Conversion: Plausible Analytics

## Changes Made

| Original | Coolify | Why |
|----------|---------|-----|
| External config file | Inline `content:` | Self-contained, no extra files needed |
| Hardcoded secrets | `SERVICE_BASE64_64_*`, `SERVICE_REALBASE64_*` | Cryptographically secure generation |
| Simple `depends_on` | `condition: service_healthy` | Proper startup ordering |
| No healthchecks | All services have healthchecks | Deployment verification |
| Added `sleep 10` | Command modification | Gives databases time to fully initialize |

## Key Patterns

### Different Secret Types

```yaml
# 64-char random string (for general secrets)
- SECRET_KEY_BASE=$SERVICE_BASE64_64_PLAUSIBLE

# Actual base64-encoded string (required by TOTP libraries)
- TOTP_VAULT_KEY=$SERVICE_REALBASE64_32_TOTP
```

Use `REALBASE64` when the application expects actual base64 encoding (common for encryption keys, TOTP secrets).

### Inline Configuration Files

Instead of mounting external files:

```yaml
volumes:
  - type: bind
    source: ./clickhouse/clickhouse-config.xml
    target: /etc/clickhouse-server/config.d/logging.xml
    read_only: true
    content: |
      <clickhouse>
        <logger>
          <level>warning</level>
          ...
        </logger>
      </clickhouse>
```

Coolify creates this file at deploy time. The template is fully self-contained.

### Dual Database Pattern

Plausible uses both PostgreSQL (metadata) and ClickHouse (events):

```yaml
- DATABASE_URL=postgres://${SERVICE_USER_POSTGRES}:${SERVICE_PASSWORD_POSTGRES}@plausible-db:5432/...
- CLICKHOUSE_DATABASE_URL=http://plausible-events-db:8123/plausible_events_db
```

ClickHouse doesn't need credentials (internal network only), but PostgreSQL does.

### Health Check Start Period

```yaml
healthcheck:
  start_period: 45s  # Give app time to run migrations
```

Plausible runs database migrations on startup. The `start_period` prevents false failures during this initialization.

### ulimits Preservation

```yaml
ulimits:
  nofile:
    soft: 262144
    hard: 262144
```

ClickHouse needs high file descriptor limits. Standard Docker Compose features work in Coolify.

## Migration Container Pattern (Alternative)

If migrations are slow, consider a separate migration container:

```yaml
services:
  migrate:
    image: ghcr.io/plausible/community-edition:v3.0.1
    command: sh -c "/entrypoint.sh db createdb && /entrypoint.sh db migrate"
    exclude_from_hc: true  # Don't wait for this to stay running
    depends_on:
      plausible-db:
        condition: service_healthy

  plausible:
    command: /entrypoint.sh run  # Just run, no migrations
    depends_on:
      migrate:
        condition: service_completed_successfully
```
