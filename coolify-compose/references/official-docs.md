# Official Coolify Docker Compose Documentation

Source: https://github.com/coollabsio/coolify-docs/blob/v4.x/docs/knowledge-base/docker/compose.md

This is the authoritative reference for Coolify Docker Compose behavior.

## Key Concepts

### Magic Environment Variables

Coolify generates dynamic environment variables using `SERVICE_<TYPE>_<IDENTIFIER>`:

- **URL**: Generates URL for the service. Add ports and paths as suffixes.
- **FQDN**: Generates FQDN (hostname without scheme). No port suffix needed.
- **USER**: Random 16-char string via `Str::random(16)`
- **PASSWORD**: Random password via `Str::password(symbols: false)`. Use `PASSWORD_64` for 64-char.
- **BASE64**: Random string via `Str::random(32)`. Use `BASE64_64` or `BASE64_128` for longer.

### Identifier Naming Rule

Identifiers with underscores (`_`) cannot use ports. Use hyphens (`-`) instead:

```
SERVICE_URL_APPWRITE_SERVICE_3000 ❌
SERVICE_URL_APPWRITE-SERVICE_3000 ✅
```

### Complete Example from Official Docs

```yaml
services:
  appwrite:
    environment:
      # http://appwrite-vgsco4o.example.com
      - SERVICE_URL_APPWRITE
      # http://appwrite-vgsco4o.example.com/v1/realtime
      - SERVICE_URL_APPWRITE=/v1/realtime
      # _APP_URL gets the value of SERVICE_URL_APPWRITE
      - _APP_URL=$SERVICE_URL_APPWRITE
      # http://appwrite-vgsco4o.example.com/ proxied to port 3000
      - SERVICE_URL_APPWRITE_3000
      # DOMAIN_NAME gets FQDN (appwrite-vgsco4o.example.com) - no port needed
      - DOMAIN_NAME=${SERVICE_FQDN_APPWRITE}
      # http://api-vgsco4o.example.com/api proxied to port 2000
      - SERVICE_URL_API_2000=/api
      # Password injected as SERVICE_SPECIFIC_PASSWORD
      - SERVICE_SPECIFIC_PASSWORD=${SERVICE_PASSWORD_APPWRITE}
  not-appwrite:
    environment:
      # Reuses password from Appwrite service
      - APPWRITE_PASSWORD=${SERVICE_PASSWORD_APPWRITE}
      # New URL: http://not-appwrite-vgsco4o.example.com/api
      - SERVICE_URL_API=/api
```

Key observations:
1. `SERVICE_URL_APPWRITE_3000` declares URL AND configures proxy to port 3000
2. `$SERVICE_URL_APPWRITE` references the URL value (without port suffix)
3. `${SERVICE_FQDN_APPWRITE}` is available without explicit declaration
4. Same identifier (e.g., `SERVICE_PASSWORD_APPWRITE`) = same value everywhere

### Environment Variable Syntax

```yaml
environment:
  - HARDCODED=hello                    # Not visible in Coolify UI
  - VARIABLE=${UI_VARIABLE}            # Editable in UI (empty)
  - WITH_DEFAULT=${VAR:-hello}         # Editable with default "hello"
  - REQUIRED=${VAR:?}                  # Required - blocks deploy if empty
  - REQUIRED_DEFAULT=${VAR:?default}   # Required with prefilled default
```

### Storage Extensions

Create directory:
```yaml
volumes:
  - type: bind
    source: ./data
    target: /app/data
    is_directory: true  # Coolify creates this
```

Create file with content:
```yaml
volumes:
  - type: bind
    source: ./config.sql
    target: /docker-entrypoint-initdb.d/config.sql
    content: |
      ALTER USER authenticator WITH PASSWORD :'pgpass';
```

### Exclude from Health Checks

```yaml
services:
  migration:
    exclude_from_hc: true
```

## Version Requirements

Magic Environment Variables in Compose files based on Git sources requires Coolify v4.0.0-beta.411 and above.
