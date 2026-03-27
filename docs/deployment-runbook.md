# Deployment Runbook

## Overview

The repository publishes three container images to GHCR:

- `clockwork-web`
- `clockwork-bff`
- `clockwork-simulator`

Deployment is handled by [`.github/workflows/deploy.yml`](/Users/stan/Work/clockwork_fullstack/.github/workflows/deploy.yml). The workflow targets a remote Docker host through GitHub Environments.

The repository also supports a frontend-only free hosting path through [`.github/workflows/deploy-pages.yml`](/Users/stan/Work/clockwork_fullstack/.github/workflows/deploy-pages.yml).

## Recommended Free Hosting Split

If the goal is a public demo with minimal cost:

- frontend: GitHub Pages
- BFF: separate free or low-cost runtime host
- simulator: same host as the BFF

GitHub Pages is a good fit for the frontend because it is static. It does not run the BFF or simulator.

## Simplest Full-Stack Hosting Path

If you want the least operational complexity, use one VM for all three runtime layers and put Caddy in front:

- [docker-compose.vm.yml](/Users/stan/Work/clockwork_fullstack/infra/docker-compose.vm.yml)
- [Caddyfile](/Users/stan/Work/clockwork_fullstack/infra/Caddyfile)

That path is documented in [oracle-vm-runbook.md](/Users/stan/Work/clockwork_fullstack/docs/oracle-vm-runbook.md).

## Promotion flow

- Push to `main` or `master`: automatic deploy to `staging` using the `latest` image tag
- Push a `v*` tag: automatic deploy to `production` using that tag
- Manual dispatch: deploy any chosen image tag to either environment

## GitHub Pages Frontend Deployment

[`.github/workflows/deploy-pages.yml`](/Users/stan/Work/clockwork_fullstack/.github/workflows/deploy-pages.yml) deploys the frontend to GitHub Pages on `main` / `master` pushes and on manual dispatch.

### Required repository secrets

- `PAGES_BFF_HTTP_URL`
- `PAGES_BFF_STREAM_URL`

These should point to the public BFF deployment, for example:

- `PAGES_BFF_HTTP_URL=https://api.example.com`
- `PAGES_BFF_STREAM_URL=wss://api.example.com/api/stream`

### Notes

- The Pages build uses a repository-relative base path
- The workflow copies `index.html` to `404.html` so SPA refreshes work on GitHub Pages
- This workflow is frontend-only and does not replace the full-stack deploy workflow

## Deployment model

- CI validates source code and container builds.
- [`.github/workflows/release-images.yml`](/Users/stan/Work/clockwork_fullstack/.github/workflows/release-images.yml) publishes immutable images to GHCR.
- [`.github/workflows/deploy.yml`](/Users/stan/Work/clockwork_fullstack/.github/workflows/deploy.yml) pulls those images onto a remote host and starts the stack with [infra/docker-compose.prod.yml](/Users/stan/Work/clockwork_fullstack/infra/docker-compose.prod.yml).

## Required GitHub Environment secrets

Configure these in each environment, for example `staging` and `production`:

- `DEPLOY_HOST`: remote Docker host DNS name or IP
- `DEPLOY_PORT`: SSH port, usually `22`
- `DEPLOY_USER`: SSH user on the remote host
- `DEPLOY_SSH_KEY`: private key used by GitHub Actions for SSH access
- `DEPLOY_PATH`: remote directory where the compose bundle is stored
- `GHCR_USERNAME`: account or service user with package pull access
- `GHCR_TOKEN`: token with `read:packages`
- `PUBLIC_BFF_HTTP_URL`: browser-visible BFF base URL, for example `https://fabric.example.com/api`
- `PUBLIC_BFF_STREAM_URL`: browser-visible websocket URL, for example `wss://fabric.example.com/api/stream`
- `PUBLIC_WEB_URL`: public web base URL, for example `https://fabric.example.com`
- `SIMULATOR_SEED`: runtime seed used by the simulator

## Triggering a deployment

The `Deploy Stack` workflow supports both automatic and manual deployment.

### Automatic deployment

- `main` / `master` pushes promote the latest images to `staging`
- `v*` tags promote the tagged images to `production`

### Manual deployment

Use the workflow manually when you need controlled promotion or rollback:

1. Choose `staging` or `production`.
2. Choose the image tag.
   - `latest` for the most recent `main` image set
   - a `v*` tag or SHA-derived tag for a pinned release

The workflow will:

1. generate a deployment environment file
2. copy the compose bundle to the remote host
3. log into GHCR on the remote host
4. `docker compose pull`
5. `docker compose up -d`
6. run public smoke tests unless explicitly skipped

## Post-deploy validation

After deployment, confirm:

- web health endpoint responds through the public URL
- BFF `/health` and `/api/health` respond
- simulator `/health` responds on the host network or internal network as designed
- frontend scenario controls and live websocket updates function
- workflow summary shows smoke tests passed

## Rollback

Roll back by redeploying a previous image tag through the same workflow. The stack is image-driven, so rollback does not require rebuilding the repo.
