# Simple Conversion: Uptime Kuma

## Changes Made

| Original | Coolify | Why |
|----------|---------|-----|
| No header | Added metadata comments | Required for Coolify template discovery |
| `ports: "3001:3001"` | `SERVICE_URL_UPTIMEKUMA_3001` | Traefik proxy handles routing |
| `./data` bind mount | `uptime-kuma-data` named volume | Named volumes are more portable |
| No healthcheck | Added healthcheck | Coolify uses this to determine deployment success |
| `restart: unless-stopped` | Removed | Coolify manages restart policy |

## Key Patterns

### URL Generation
```yaml
- SERVICE_URL_UPTIMEKUMA_3001
```
This single line:
1. Generates a URL like `https://uptimekuma-abc123.example.com`
2. Configures Traefik to route traffic to container port 3001
3. Creates an editable `SERVICE_URL_UPTIMEKUMA` variable in Coolify UI

### Health Check
Uptime Kuma ships with a built-in healthcheck script at `extra/healthcheck`. Always prefer the application's native healthcheck when available.
