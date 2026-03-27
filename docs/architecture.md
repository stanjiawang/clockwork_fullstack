# Architecture

## System Context

The demo models a distributed AI training fabric where 256 GPU nodes exchange synchronization telemetry. It is structured as three runtime services:

- Simulator: generates raw node metrics and topology metadata
- BFF: ingests raw metrics, computes anomalies, and emits browser-facing frames
- Web app: renders cluster state, diagnostics, and remediation guidance

## Service Boundaries

- `services/simulator` owns topology generation, fault injection, and raw metric publication.
- `services/bff` owns rolling windows, Z-score analysis, cluster health, and recommendation strings.
- `apps/web` owns rendering, interaction, operator-facing status, and local view state.

## Data Flow

1. The Go simulator produces node-level metrics every 100ms over WebSocket.
2. The FastAPI service consumes that stream and updates rolling node state.
3. The FastAPI service emits a curated stream to the browser with cluster aggregates and changed node patches only.
4. The Vue app loads topology once via HTTP, then applies live patches from the BFF stream.

## Frontend Architecture

The frontend is organized as an operations console with a clear shell and state split:

- `App.vue`: top-level frame and shell
- `DashboardView.vue`: primary workflow composition
- `components/base/*`: reusable atomic primitives
- `components/shell/*`: sidebar, command bar, state patterns
- `stores/useClusterStore.ts`: Pinia state for live client data and interaction state
- `composables/useClusterQueries.ts`: Vue Query hooks for HTTP-backed state
- `composables/useSocket.ts`: websocket ingest path

The topology view uses a deterministic SVG layout grouped into fabric pods and hosts. The trend chart is also SVG-based so it stays visible and testable in the DOM.

## Topology Model

- 256 GPUs
- 32 hosts with 8 GPUs each
- Intra-host links represent NVLink-like dense connectivity
- Inter-host links represent aggregated RoCE-like uplinks
- The UI groups hosts into four fabric pods to improve readability at operator scale

## Failure Modes

- Simulator unavailable: BFF health degrades to stale and UI shows disconnected state.
- BFF stream lag: diagnostics expose last frame age and the UI marks data stale.
- Burst fault injection: a subset of nodes shows elevated drift, latency, and packet loss, reducing cluster health.

## Scaling Path

This v1 keeps state in memory. A scaled version would move raw metrics into a message bus such as Kafka or NATS, use stateless BFF workers, and deploy the stack onto Kubernetes or Azure Container Apps.

## Key Tradeoffs

- FastAPI owns derived analytics so the browser stays lightweight and deterministic.
- The topology uses a deterministic structured SVG layout rather than a force-directed graph because operator readability matters more than visual novelty.
- The trend chart uses SVG rather than Canvas so the current value, grid, and state remain visible, testable, and accessible even with short history.
- The browser consumes curated frames instead of raw metrics to limit client-side computation and reduce reactivity churn.
- Scenario control is routed through the BFF so the frontend has one backend integration surface.
