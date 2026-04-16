# Docker Deployment

## Build and run
```bash
docker compose up -d --build
```

## Logs
```bash
docker compose logs -f web
```

## Stop
```bash
docker compose down
```

## Rebuild only
```bash
docker compose build --no-cache
```

## Notes
- Runtime DB is SQLite at `./prisma/dev.db` mounted into container.
- Startup runs `prisma migrate deploy` before `next start`.
- This avoids local SWC binary issues by compiling in Linux container.
