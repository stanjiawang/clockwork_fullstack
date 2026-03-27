# Demo Script

## Startup

1. Start the stack with Docker Compose or the three local services.
2. Confirm simulator and BFF health endpoints are healthy.
3. Open the web app and verify the cluster starts in a healthy baseline state.

## Narrative

1. Explain the system split:
   - Go simulates the fabric
   - FastAPI computes health and anomaly signals
   - Vue renders the operator console
2. Explain that the simulator models 256 GPUs exchanging sync telemetry every 100ms.
3. Show the topology view first, then the trend panel, then the node decision panel.
4. Note that the browser only receives curated frames from the BFF, not the raw simulator stream.

## Interview Talking Points

- The frontend is structured with atomic primitives, Pinia, Vue Query, and a shell-driven dashboard layout.
- The BFF centralizes anomaly logic and keeps the browser lightweight.
- The simulator is deterministic for a given seed, which makes scenarios reproducible in demos and tests.
- The repo includes integration tests, container builds, image publishing, and deployment workflows.

## Fault Injection

1. Use the operator control panel to switch the simulator into `straggler-burst`, or wait for the automatic burst schedule.
2. Watch cluster health degrade and affected nodes turn warning or critical.
3. Click a straggler node and explain the recommendation.
4. Call out that the scenario action goes through the BFF instead of directly to the simulator.

## Closing

- Reiterate the split of responsibilities between simulator, BFF, and frontend.
- Mention the upgrade path to message queues and Kubernetes or Azure deployment for scale.
- Mention that CI validates code and containers, images are published to GHCR, and deployment is image-driven.
