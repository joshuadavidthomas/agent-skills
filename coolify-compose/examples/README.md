# Coolify Compose Examples

Before/after examples showing standard Docker Compose files converted to Coolify templates.

## Which Example to Use

Analyze the user's compose file:

| Compose file characteristics | Example |
|------------------------------|---------|
| 1 service, no database | [simple/](simple/) |
| 2 services: app + single database | [with-database/](with-database/) |
| 3+ services, config file mounts, or multiple databases | [multi-service/](multi-service/) |

## Detection Rules

**→ simple/**
- Only 1 entry under `services:`
- No database images (postgres, mysql, mariadb, mongo, redis)
- Just needs URL routing + healthcheck

**→ with-database/**
- Exactly 2 services
- One is a database image (`postgres:*`, `mysql:*`, `mariadb:*`)
- App references database credentials in environment

**→ multi-service/**
- 3 or more services
- Multiple database images (e.g., postgres + clickhouse, postgres + redis)
- Config files mounted from host (`./config.xml:/etc/app/config.xml`)
- Init/migration containers that run once and exit

## Each Example Contains

- `before.yml` — Standard Docker Compose (user's input)
- `after.yml` — Coolify-compatible template (desired output)
- `notes.md` — Explanation of each transformation
