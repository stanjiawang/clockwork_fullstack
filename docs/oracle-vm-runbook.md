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

Fastest path:

1. SSH into the VM
2. Run [bootstrap-oracle-vm.sh](/Users/stan/Work/clockwork_fullstack/infra/bootstrap-oracle-vm.sh) as `root`
3. Point your DNS record at the VM public IP

The bootstrap script installs:

- Docker Engine
- Docker Compose plugin
- firewall rules for `22`, `80`, and `443`

## Files to copy to the VM

- [infra/docker-compose.vm.yml](/Users/stan/Work/clockwork_fullstack/infra/docker-compose.vm.yml)
- [infra/Caddyfile](/Users/stan/Work/clockwork_fullstack/infra/Caddyfile)
- [infra/deploy-vm.sh](/Users/stan/Work/clockwork_fullstack/infra/deploy-vm.sh)
- [infra/push-vm-bundle.sh](/Users/stan/Work/clockwork_fullstack/infra/push-vm-bundle.sh)
- [infra/vm.env.example](/Users/stan/Work/clockwork_fullstack/infra/vm.env.example)

From your local machine, you can copy the bundle with:

```bash
./infra/push-vm-bundle.sh <ssh-user> <host> <remote-dir> [ssh-port]
```

## Required environment file

Example `.env` on the VM:

```env
APP_DOMAIN=demo.example.com
WEB_IMAGE=ghcr.io/stanjiawang/clockwork-web:latest
BFF_IMAGE=ghcr.io/stanjiawang/clockwork-bff:latest
SIMULATOR_IMAGE=ghcr.io/stanjiawang/clockwork-simulator:latest
SIMULATOR_SEED=42
```

Create it by copying [vm.env.example](/Users/stan/Work/clockwork_fullstack/infra/vm.env.example) to `infra/.env` and editing `APP_DOMAIN`.

## Start the stack

```bash
cd infra
./deploy-vm.sh
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
