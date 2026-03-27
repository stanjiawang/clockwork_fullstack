# Clockwork AI Fabric Health Monitor

Industrial-grade full-stack demo that visualizes how microsecond-level clock synchronization affects GPU-to-GPU communication in a large AI training fabric.

This repository is structured as a production-minded interview project, not a single-page mock. It includes:

- a Go telemetry simulator for a 256-GPU cluster
- a FastAPI BFF that computes straggler detection and cluster health
- a Vue 3 operations console with a dark, high-density interface
- shared contracts, integration tests, container images, and CI/CD workflows

## What The Demo Shows

- 256 simulated GPUs emit sync telemetry every `100ms`
- the BFF ingests the raw stream and computes:
  - cluster health score
  - sync stability
  - node severity
  - straggler recommendations
- the frontend renders:
  - a fabric topology overview grouped into pods and hosts
  - a live global health trend chart
  - a node decision panel
  - scenario controls for baseline, burst, and auto modes

The narrative is simple: stable clock sync keeps the training fabric healthy; drift and latency create stragglers that degrade the cluster and require intervention.

## Tech Stack

### Frontend

- Vue 3 with Composition API
- TypeScript
- Vite
- Tailwind CSS v4 with semantic design tokens
- Pinia for client state
- Vue Query for server state
- SVG-based topology and trend visualization
- Lucide icons

### BFF

- Python 3.12+
- FastAPI
- `httpx`
- `websockets`
- in-memory rolling state + anomaly scoring

### Backend

- Go 1.22+
- standard library HTTP server
- Gorilla WebSocket
- deterministic seeded simulation and runtime scenario control

### DevOps

- pnpm workspaces
- Docker / Docker Compose
- GitHub Actions CI
- GHCR image publishing
- GitHub Pages frontend deployment
- remote Docker-host deployment workflow with smoke tests

## Current Repository Structure

```text
apps/
  web/
    src/
      components/
        base/         # BaseButton, BaseCard, BaseInput, BaseSelect
        shell/        # CommandBar, SidebarNav, StatusPill, StatePanel
      composables/    # socket, queries, dashboard view model, resilience
      stores/         # Pinia cluster state
      views/          # DashboardView
packages/
  contracts/         # shared DTOs + example payloads
services/
  bff/               # FastAPI aggregation layer
  simulator/         # Go simulator and topology/scenario engine
infra/
  docker-compose.yml
  docker-compose.prod.yml
docs/
  architecture.md
  deployment-runbook.md
  demo-script.md
  testing-strategy.md
.github/workflows/
  ci.yml
  release-images.yml
  deploy.yml
```

## Runtime Architecture

### 1. Simulator

[services/simulator](/Users/stan/Work/clockwork_fullstack/services/simulator) owns:

- static topology generation
- seeded scenario behavior
- metric generation every `100ms`
- simulator health and runtime metrics
- raw websocket stream
- runtime control endpoint

Key endpoints:

- `GET /health`
- `GET /metrics`
- `GET /topology`
- `GET /scenario`
- `POST /scenario/control`
- `WS /stream`

### 2. BFF

[services/bff](/Users/stan/Work/clockwork_fullstack/services/bff) owns:

- simulator bootstrap
- rolling node state
- anomaly scoring and health calculation
- browser-facing API contracts
- websocket fanout to the UI
- scenario control proxying

Key endpoints:

- `GET /health`
- `GET /api/health`
- `GET /api/metrics`
- `GET /api/topology`
- `GET /api/scenario`
- `POST /api/scenario`
- `GET /api/nodes/{id}`
- `WS /api/stream`

### 3. Web App

[apps/web](/Users/stan/Work/clockwork_fullstack/apps/web) owns:

- application shell and command bar
- topology workspace
- trend analysis view
- node decision panel
- cohort controls and scenario controls
- keyboard/focus behavior and operator UX

The browser loads topology through Vue Query, consumes live cluster frames over websocket, and stores hot client-side state in Pinia.

## Frontend Architecture

The frontend is built as a tokenized operations console rather than a collection of isolated cards.

### Application Shell

- [App.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/App.vue): global frame
- [DashboardView.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/views/DashboardView.vue): main operational workspace

### Design System

- [BaseButton.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/base/BaseButton.vue)
- [BaseCard.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/base/BaseCard.vue)
- [BaseInput.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/base/BaseInput.vue)
- [BaseSelect.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/base/BaseSelect.vue)
- [tailwind.config.ts](/Users/stan/Work/clockwork_fullstack/apps/web/tailwind.config.ts)

### Shell Components

- [CommandBar.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/shell/CommandBar.vue)
- [SidebarNav.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/shell/SidebarNav.vue)
- [StatusPill.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/shell/StatusPill.vue)
- [StatePanel.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/shell/StatePanel.vue)

### Feature Components

- [ClusterMap.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/ClusterMap.vue)
- [JitterChart.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/JitterChart.vue)
- [NodeDetailPanel.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/NodeDetailPanel.vue)
- [KpiCard.vue](/Users/stan/Work/clockwork_fullstack/apps/web/src/components/KpiCard.vue)

### State Model

- [useClusterStore.ts](/Users/stan/Work/clockwork_fullstack/apps/web/src/stores/useClusterStore.ts): Pinia store for live node state, selection, diagnostics, and filters
- [useClusterQueries.ts](/Users/stan/Work/clockwork_fullstack/apps/web/src/composables/useClusterQueries.ts): Vue Query hooks for topology, health, metrics, scenario, and node detail
- [useSocket.ts](/Users/stan/Work/clockwork_fullstack/apps/web/src/composables/useSocket.ts): websocket ingest and patch application
- [useDashboardViewModel.ts](/Users/stan/Work/clockwork_fullstack/apps/web/src/composables/useDashboardViewModel.ts): dashboard composition layer

## Detection and Health Model

The BFF uses a deterministic scoring path designed to be easy to explain in an interview:

- rolling windows per node
- Z-score based anomaly detection
- severity classification per node
- cluster health score from drift, latency, freshness, and straggler concentration
- recommendation strings based on the dominant failure mode

This keeps the UI lightweight while preserving a clear analytics story.

## Local Development

### Prerequisites

- Node.js 22+
- pnpm 10+
- Python 3.12+
- Go 1.22+

### Install

```bash
pnpm install
python3 -m venv .venv
.venv/bin/pip install -r services/bff/requirements.txt
```

### Run Locally

Terminal 1:

```bash
cd /Users/stan/Work/clockwork_fullstack/services/simulator
go run ./cmd/simulator
```

Terminal 2:

```bash
cd /Users/stan/Work/clockwork_fullstack
PYTHONPATH=/Users/stan/Work/clockwork_fullstack .venv/bin/uvicorn services.bff.app.main:app --host 0.0.0.0 --port 8000
```

Terminal 3:

```bash
cd /Users/stan/Work/clockwork_fullstack
pnpm --dir apps/web dev
```

Open:

- [http://localhost:5173](http://localhost:5173)

### Run With Docker Compose

Development stack:

```bash
docker compose -f infra/docker-compose.yml up
```

Production-style stack:

```bash
docker compose --env-file infra/.env.example -f infra/docker-compose.prod.yml up --build
```

## Testing

Frontend:

```bash
pnpm lint:web
pnpm test:web
pnpm build:web
```

BFF:

```bash
.venv/bin/python -m pytest services/bff/tests
```

Simulator:

```bash
cd services/simulator
GOCACHE=/tmp/go-build go test ./...
```

Integration:

```bash
.venv/bin/python -m pytest tests/integration
```

All major test expectations are documented in [testing-strategy.md](/Users/stan/Work/clockwork_fullstack/docs/testing-strategy.md).

## CI/CD

### CI

[ci.yml](/Users/stan/Work/clockwork_fullstack/.github/workflows/ci.yml) runs:

- frontend lint, test, build
- BFF import validation and unit tests
- simulator formatting and tests
- container image build validation
- cross-service integration tests

### Image Release

[release-images.yml](/Users/stan/Work/clockwork_fullstack/.github/workflows/release-images.yml):

- publishes `clockwork-web`, `clockwork-bff`, and `clockwork-simulator` to GHCR
- runs on `main` / `master` and `v*` tags

### Deployment

[deploy.yml](/Users/stan/Work/clockwork_fullstack/.github/workflows/deploy.yml):

- auto-deploys `main` / `master` to `staging`
- auto-deploys `v*` tags to `production`
- supports manual deploy and rollback by image tag
- runs post-deploy smoke tests against public URLs

See [deployment-runbook.md](/Users/stan/Work/clockwork_fullstack/docs/deployment-runbook.md).

### Free Frontend Hosting

[deploy-pages.yml](/Users/stan/Work/clockwork_fullstack/.github/workflows/deploy-pages.yml):

- deploys the frontend to GitHub Pages
- builds with a repository-relative base path
- expects:
  - `PAGES_BFF_HTTP_URL`
  - `PAGES_BFF_STREAM_URL`
- is the easiest free public hosting option for the UI layer

Important: GitHub Pages only hosts the frontend. The BFF and simulator still need their own runtime host.

## Interview Notes

If you need to present this in an interview, focus on these points:

### Technical Narrative

- The system separates concerns cleanly:
  - Go simulates a high-frequency distributed system
  - Python derives analytics and normalizes contracts
  - Vue renders an operator-facing console
- The browser does not process raw telemetry. It receives curated, patch-oriented frames from the BFF.
- The deployment story is not hypothetical: the repo includes CI, image publishing, and deployment workflows.

### Frontend Decisions

- Pinia is used for hot client state and selection
- Vue Query is used for server state
- the UI uses a tokenized dark design system and reusable primitives
- the topology visualization was redesigned for readability, not novelty

### Backend Decisions

- the simulator is deterministic for a given seed
- the BFF fails fast on invalid config and degrades health explicitly on stale/disconnected upstream state
- scenario control is proxied through the BFF so the frontend never needs to talk directly to the simulator

### Production-Minded Signals

- health endpoints on each service
- machine-readable metrics endpoints
- integration testing across services
- containerized runtimes
- GHCR-based artifact flow
- staged deployment workflow with smoke tests

## More Documentation

- [architecture.md](/Users/stan/Work/clockwork_fullstack/docs/architecture.md)
- [api-contracts.md](/Users/stan/Work/clockwork_fullstack/docs/api-contracts.md)
- [engineering-handbook.md](/Users/stan/Work/clockwork_fullstack/docs/engineering-handbook.md)
- [performance-guidelines.md](/Users/stan/Work/clockwork_fullstack/docs/performance-guidelines.md)
- [observability-runbook.md](/Users/stan/Work/clockwork_fullstack/docs/observability-runbook.md)
- [demo-script.md](/Users/stan/Work/clockwork_fullstack/docs/demo-script.md)
