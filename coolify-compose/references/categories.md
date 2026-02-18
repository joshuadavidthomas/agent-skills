# Template Categories

Valid values for the `# category:` header field.

## Categories by Usage (from 337 Coolify templates)

| Category | Count | Examples |
|----------|-------|----------|
| `productivity` | 70 | Nextcloud, Outline, Vikunja |
| `cms` | 38 | WordPress, Ghost, Strapi |
| `media` | 24 | Jellyfin, Plex, Immich |
| `devtools` | 20 | Hoppscotch, Code Server, Jenkins |
| `storage` | 18 | MinIO, Seafile, Filebrowser |
| `monitoring` | 18 | Uptime Kuma, Grafana, Prometheus |
| `ai` | 18 | Ollama, Flowise, AnythingLLM |
| `automation` | 15 | N8N, Activepieces, Huginn |
| `git` | 14 | GitLab, Gitea, Forgejo |
| `analytics` | 14 | Plausible, Umami, Matomo |
| `backend` | 13 | Supabase, Appwrite, Pocketbase |
| `messaging` | 10 | Mattermost, Rocket.Chat, Matrix |
| `auth` | 10 | Authentik, Keycloak, Authelia |
| `database` | 6 | pgAdmin, Redis Insight, Adminer |
| `security` | 6 | Vaultwarden, CrowdSec |
| `search` | 5 | Meilisearch, Elasticsearch, Typesense |
| `proxy` | 3 | Traefik, Nginx Proxy Manager |
| `vpn` | 2 | WireGuard, Tailscale |
| `RSS` | 2 | FreshRSS, Miniflux |
| `email` | 2 | Mailpit, Listmonk |
| `games` | 1 | Minecraft, Terraria |
| `documentation` | 1 | WikiJS, BookStack |
| `ci` | 1 | Jenkins, Drone |

## Header Template

```yaml
# documentation: https://example.com/docs
# slogan: Brief one-line description
# category: backend
# tags: keyword1, keyword2, keyword3
# logo: svgs/myservice.svg
# port: 3000
```

## Optional Fields

| Field | Description |
|-------|-------------|
| `# minversion: 4.0.0-beta.411` | Minimum Coolify version required |
| `# ignore: true` | Hide template from the service list |
