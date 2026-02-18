# Magic Environment Variables

Complete reference for Coolify's auto-generated environment variables.

## Syntax

```
SERVICE_<TYPE>_<IDENTIFIER>
```

- **TYPE**: The generation method (see tables below)
- **IDENTIFIER**: Any alphanumeric name (used to reference the same value across services)

## Credentials

| Type | Syntax | Generated Value |
|------|--------|-----------------|
| `PASSWORD` | `SERVICE_PASSWORD_<ID>` | Random password, no symbols |
| `PASSWORD_64` | `SERVICE_PASSWORD_64_<ID>` | 64-char password, no symbols |
| `PASSWORDWITHSYMBOLS` | `SERVICE_PASSWORDWITHSYMBOLS_<ID>` | Random password with symbols |
| `PASSWORDWITHSYMBOLS_64` | `SERVICE_PASSWORDWITHSYMBOLS_64_<ID>` | 64-char password with symbols |
| `USER` | `SERVICE_USER_<ID>` | Random 16-char alphanumeric |
| `LOWERCASEUSER` | `SERVICE_LOWERCASEUSER_<ID>` | Lowercase 16-char alphanumeric |

## Random Strings

| Type | Syntax | Generated Value |
|------|--------|-----------------|
| `BASE64` | `SERVICE_BASE64_<ID>` | 32-char random string |
| `BASE64_32` | `SERVICE_BASE64_32_<ID>` | 32-char random string |
| `BASE64_64` | `SERVICE_BASE64_64_<ID>` | 64-char random string |
| `BASE64_128` | `SERVICE_BASE64_128_<ID>` | 128-char random string |

> ⚠️ **Note:** `BASE64` types are misleadingly named — they're just random alphanumeric strings, NOT base64-encoded. Use `REALBASE64` for actual base64 encoding.

## Actual Base64

| Type | Syntax | Generated Value |
|------|--------|-----------------|
| `REALBASE64` | `SERVICE_REALBASE64_<ID>` | base64-encoded 32-char random |
| `REALBASE64_32` | `SERVICE_REALBASE64_32_<ID>` | base64-encoded 32-char random |
| `REALBASE64_64` | `SERVICE_REALBASE64_64_<ID>` | base64-encoded 64-char random |
| `REALBASE64_128` | `SERVICE_REALBASE64_128_<ID>` | base64-encoded 128-char random |

## Hex Strings

| Type | Syntax | Generated Value |
|------|--------|-----------------|
| `HEX_32` | `SERVICE_HEX_32_<ID>` | 64-char hex (32 bytes) |
| `HEX_64` | `SERVICE_HEX_64_<ID>` | 128-char hex (64 bytes) |
| `HEX_128` | `SERVICE_HEX_128_<ID>` | 256-char hex (128 bytes) |

## URLs & Domains

| Type | Syntax | Generated Value |
|------|--------|-----------------|
| `URL` | `SERVICE_URL_<NAME>` | `https://<name>-<uuid>.<domain>` |
| `URL` + port | `SERVICE_URL_<NAME>_<PORT>` | Same URL, proxy routes to container port |
| `URL` + path | `SERVICE_URL_<NAME>=/path` | URL with path suffix |
| `URL` + port + path | `SERVICE_URL_<NAME>_<PORT>=/path` | Combined |
| `FQDN` | `SERVICE_FQDN_<NAME>` | `<name>-<uuid>.<domain>` (no scheme) |
| `FQDN` + port | `SERVICE_FQDN_<NAME>_<PORT>` | Same FQDN, proxy routes to port |

### URL Examples

```yaml
environment:
  # Basic URL generation
  - SERVICE_URL_APP                    # https://app-abc123.example.com
  
  # With port routing (proxy sends traffic to container port 3000)
  - SERVICE_URL_APP_3000               # https://app-abc123.example.com
  
  # With path
  - SERVICE_URL_API=/v1                # https://api-abc123.example.com/v1
  
  # With port AND path
  - SERVICE_URL_API_8080=/v1           # https://api-abc123.example.com/v1
  
  # FQDN only (no scheme)
  - SERVICE_FQDN_APP                   # app-abc123.example.com
  
  # Reference in other variables
  - PUBLIC_URL=$SERVICE_URL_APP
  - CORS_ORIGIN=${SERVICE_URL_APP}
```

### ⚠️ Port Syntax Warning

Underscores in the identifier break port parsing:

```yaml
# ❌ WRONG - underscore before port
SERVICE_URL_MY_SERVICE_3000    # Coolify can't parse the port

# ✅ CORRECT - use hyphen
SERVICE_URL_MY-SERVICE_3000    # Works correctly
```

## Special Types

| Type | Syntax | Use Case |
|------|--------|----------|
| `SUPABASEANON_KEY` | `SERVICE_SUPABASEANON_KEY` | Supabase anon JWT (requires `SERVICE_PASSWORD_JWT`) |
| `SUPABASESERVICE_KEY` | `SERVICE_SUPABASESERVICE_KEY` | Supabase service_role JWT |

These generate valid JWTs signed with `SERVICE_PASSWORD_JWT` for Supabase deployments.

## Reusing Values

The same identifier always generates the same value:

```yaml
services:
  app:
    environment:
      - DB_PASSWORD=$SERVICE_PASSWORD_POSTGRES
  
  worker:
    environment:
      - DB_PASSWORD=$SERVICE_PASSWORD_POSTGRES  # Identical value
  
  db:
    environment:
      - POSTGRES_PASSWORD=$SERVICE_PASSWORD_POSTGRES  # Identical value
```

## Declaration vs Reference

```yaml
environment:
  # Declaration - generates the URL AND sets up proxy routing
  - SERVICE_URL_APP_3000
  
  # Reference - uses the generated value in another variable
  - PUBLIC_URL=$SERVICE_URL_APP
  - WEBHOOK_URL=${SERVICE_URL_APP}/webhooks
```

## Version Requirements

Magic environment variables in Git-sourced compose files require **Coolify v4.0.0-beta.411** or later.
