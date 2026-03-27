# Performance Guidelines

## Rendering Rules

- `requestAnimationFrame` is the render clock for hot UI paths.
- Socket ingest must not directly trigger full component rerenders.
- Topology is immutable after initial load.
- Topology layout is deterministic and should not relayout during steady-state updates.
- The trend chart uses bounded SVG point history and should avoid unbounded DOM growth.

## State Design

- Separate static topology from live telemetry.
- Separate selection state from stream state.
- Use shallow refs or non-reactive buffers for frequently updated metrics.
- Batch node patch application once per animation frame.

## UX Requirements

- Loading, disconnected, and stale states are mandatory.
- Tooltips must be concise and operator-oriented.
- Visual encodings must remain legible at cluster density.
- Interactions must not depend on the timing of animations.
- Detail panels and controls must keep readable labels and keyboard focus behavior.

## Target Budgets

- frame time: under 16ms
- patch application: under 4ms
- trend chart updates: no unbounded history growth or layout shift
- graph relayouts: zero during steady-state streaming
