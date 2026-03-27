# Coding Conventions

## Cross-Language Rules

- Keep public field names stable across layers
- Use epoch milliseconds for timestamps
- Include units in metric names where ambiguity is possible
- Do not silently swallow contract mismatches
- Document public wire shapes in [api-contracts.md](/Users/stan/Work/clockwork_fullstack/docs/api-contracts.md)

## Frontend: Vue, TypeScript, Tailwind

### Architecture

- Use Vue 3 Composition API only
- Use `script setup`
- Use strict TypeScript
- Use Pinia for hot client state
- Use Vue Query for HTTP-backed server state
- Keep the dashboard shell in `App.vue` and page composition in `views/`
- Keep reusable primitives in `components/base/`
- Keep shell UI in `components/shell/`

### Design System

- Use semantic tokens from [tailwind.config.ts](/Users/stan/Work/clockwork_fullstack/apps/web/tailwind.config.ts)
- Prefer `BaseButton`, `BaseCard`, `BaseInput`, and `BaseSelect` over one-off controls
- Preserve the dark industrial look without adding ad hoc color systems
- Avoid box-shadow-based hierarchy; prefer border and tone layering

### Rendering and State

- Keep business logic out of templates
- Visualization components own their rendering logic
- The topology uses deterministic SVG positioning, not free-form force layout during runtime
- The trend chart uses bounded SVG history and must avoid unbounded point growth
- Avoid layout shift in live metrics and status UI
- Use composables for transport, timing, retry, and resilience behavior

### Accessibility

- All interactive controls must be keyboard reachable
- Focus-visible treatment is required
- Native browser styling should not leak into autocomplete or select patterns
- Empty, loading, and error states must preserve layout stability

## BFF: Python and FastAPI

- Use Pydantic models for request and response shapes
- Keep transport concerns thin; move logic into services and helpers
- Prefer pure functions for anomaly and scoring logic where practical
- Use explicit typing throughout
- Avoid hidden mutable global state outside the clearly owned runtime store
- Use structured logging only
- Fail fast on invalid configuration
- Health degradation should be explicit and machine-readable

## Backend: Go

- Keep packages small and single-purpose
- Use structs for contracts and runtime snapshots
- Keep goroutine lifecycles explicit and bounded
- Handle shutdown through context and server lifecycle management
- Prefer deterministic simulation behavior for seeded runs
- Fanout should evict slow clients rather than block the broadcast path
- Add benchmarks if stream-path changes materially affect throughput

## Documentation and Testing Rules

- Shared contract changes must update docs and example payloads
- Visual changes should update demo/interview notes if they change the product story
- Realtime-path changes require tests at the correct layer
- CI/CD changes should update the runbook and README, not just workflow files
