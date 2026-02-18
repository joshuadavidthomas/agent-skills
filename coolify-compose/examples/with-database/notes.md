# Database Conversion: Ghost with MySQL

## Changes Made

| Original | Coolify | Why |
|----------|---------|-----|
| Hardcoded URL | `SERVICE_URL_GHOST_2368` | Dynamic URL based on Coolify domain |
| Hardcoded passwords | `SERVICE_PASSWORD_MYSQL` | Auto-generated secure credentials |
| Hardcoded username | `SERVICE_USER_MYSQL` | Auto-generated username |
| `depends_on: [mysql]` | `depends_on: mysql: condition: service_healthy` | Wait for MySQL to be ready |
| Bind mounts | Named volumes | Portable, managed by Coolify |
| No healthchecks | Added to both services | Deployment verification |

## Key Patterns

### Shared Credentials

The same identifier is used in both services:

```yaml
# In ghost service
- database__connection__user=$SERVICE_USER_MYSQL
- database__connection__password=$SERVICE_PASSWORD_MYSQL

# In mysql service  
- MYSQL_USER=$SERVICE_USER_MYSQL
- MYSQL_PASSWORD=$SERVICE_PASSWORD_MYSQL
```

Coolify generates these once and injects the same value everywhere they're referenced.

### Separate Root Password

MySQL needs a root password separate from the app user:

```yaml
- MYSQL_ROOT_PASSWORD=$SERVICE_PASSWORD_MYSQLROOT
```

Using a different identifier (`MYSQLROOT` vs `MYSQL`) generates a different password.

### Optional Defaults

```yaml
- MYSQL_DATABASE=${MYSQL_DATABASE:-ghost}
```

This creates an editable variable in Coolify UI with "ghost" as the default value.

### Health Check Dependency

```yaml
depends_on:
  mysql:
    condition: service_healthy
```

Ghost won't start until MySQL's healthcheck passes, preventing connection errors on startup.
