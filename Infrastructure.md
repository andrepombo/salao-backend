## Deployment Infrastructure (VPS with Traefik)

The following `docker-compose.yml` defines the infrastructure for deploying the application on a VPS using Traefik as a reverse proxy.

```yaml
andre@srv1179843:~/apps/app2$ cat docker-compose.yml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: app2-postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app2_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL","pg_isready -U postgres -d app2_db"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - internal
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: app2-backend
    depends_on:
      db:
        condition: service_healthy
    env_file:
      - ./backend/.env
    environment:
      - DJANGO_SETTINGS_MODULE=core.settings
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app2_db
      - DB_SSL_REQUIRE=False
    volumes:
      - ./backend:/app
    networks:
      - internal
      - web
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=web"
      - "traefik.http.routers.app2.rule=Host(`app2.andrepombo.info`) && PathPrefix(`/api`)"
      - "traefik.http.routers.app2.entrypoints=websecure"
      - "traefik.http.routers.app2.tls.certresolver=le"
      - "traefik.http.services.app2.loadbalancer.server.port=8000"
      - "traefik.http.middlewares.app2-backend-stripprefix.stripprefix.prefixes=/api"
      - "traefik.http.routers.app2-backend.middlewares=app2-backend-stripprefix"
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: app2-frontend
    volumes:
      - ./frontend:/app
      - /app/node_modules
    networks:
      - internal
      - web
    labels:
      - "traefik.enable=true"
      - "traefik.docker.network=web"
      - "traefik.http.routers.app2-frontend.rule=Host(`app2.andrepombo.info`)"
      - "traefik.http.routers.app2-frontend.entrypoints=websecure"
      - "traefik.http.routers.app2-frontend.tls.certresolver=le"
      - "traefik.http.services.app2-frontend.loadbalancer.server.port=80"
    restart: unless-stopped

networks:
  internal:
  web:
    external: true

volumes:
  postgres-data:
```

