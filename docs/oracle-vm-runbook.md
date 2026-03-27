# Oracle Free VM Runbook

This is the simplest fully free full-stack deployment path for the current repository.

## Recommended topology

- one Oracle Always Free VM
- Docker Engine + Docker Compose plugin
- Caddy as the public HTTPS reverse proxy
- simulator, BFF, and web running as internal containers

Public routing:

- `https://your-domain` -> frontend
- `https://your-domain/api/*` -> BFF
- `wss://your-domain/api/stream` -> BFF websocket

This avoids cross-origin issues and gives the frontend same-origin defaults.

## Why this is the simplest option

- one host
- one domain
- one TLS endpoint
- no separate frontend and backend domains
- no extra CORS work needed for the normal browser flow

## VM preparation

Install:

- Docker Engine
- Docker Compose plugin

Open inbound ports:

- `80`
- `443`

Point your DNS record at the VM public IP.

## Files to copy to the VM

- [infra/docker-compose.vm.yml](/Users/stan/Work/clockwork_fullstack/infra/docker-compose.vm.yml)
- [infra/Caddyfile](/Users/stan/Work/clockwork_fullstack/infra/Caddyfile)

## Required environment file

Example `.env` on the VM:

```env
APP_DOMAIN=demo.example.com
WEB_IMAGE=ghcr.io/stanjiawang/clockwork-web:latest
BFF_IMAGE=ghcr.io/stanjiawang/clockwork-bff:latest
SIMULATOR_IMAGE=ghcr.io/stanjiawang/clockwork-simulator:latest
SIMULATOR_SEED=42
```

## Start the stack

```bash
docker login ghcr.io -u <github-user>
docker compose --env-file .env -f docker-compose.vm.yml pull
docker compose --env-file .env -f docker-compose.vm.yml up -d
docker compose --env-file .env -f docker-compose.vm.yml ps
```

## Validation

Check:

- `https://your-domain/healthz`
- `https://your-domain/api/health`
- `https://your-domain/api/scenario`
- `https://your-domain/api/topology`

Then open the app and verify:

- topology loads
- websocket connects
- trend updates
- scenario controls function

## GitHub Pages note

If you use this VM setup, you do not need GitHub Pages for the frontend.

GitHub Pages is still useful if you want:

- a free static frontend host
- a separate public UI deployment

But the one-VM deployment is operationally simpler for this full-stack demo.
