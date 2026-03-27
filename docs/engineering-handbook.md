# Engineering Handbook

## Ownership Boundaries

- Frontend owns operator workflows, visualization, shell UX, accessibility, and browser performance
- BFF owns browser-facing APIs, anomaly logic, recommendation strings, and scenario proxying
- Simulator owns topology generation, raw telemetry cadence, scenario execution, and runtime control
- Shared contract changes start in [packages/contracts](/Users/stan/Work/clockwork_fullstack/packages/contracts)

## Repository Expectations

- One logical change per branch
- Public interface changes must include docs and contract updates
- Runtime-path changes must call out health, stale-state, and performance impact
- Deployment changes must update [deployment-runbook.md](/Users/stan/Work/clockwork_fullstack/docs/deployment-runbook.md)

## Definition Of Done

A change is complete only when:

- types are updated where needed
- tests exist or are updated at the correct layer
- docs reflect the new behavior
- loading, disconnected, stale, and empty states are handled where applicable
- logs, metrics, or health behavior are considered for new runtime paths
- CI remains green

## Review Checklist

- Is ownership clear?
- Is the change consistent with shared contracts?
- Does it introduce hot-path rerenders, allocations, or transport regressions?
- Are degraded and stale states handled explicitly?
- Are the tests placed at the correct layer?
- If this affects deployment or operations, is the runbook updated?

## Safe Change Rules

### Add a new API field

- Update [packages/contracts/index.ts](/Users/stan/Work/clockwork_fullstack/packages/contracts/index.ts) first
- Update example payloads
- Update backend serializers and frontend DTO usage in the same change
- Prefer additive changes

### Add or redesign a visualization

- Define the operator question it answers
- Decide whether it belongs in topology, trend analysis, or the decision rail
- Choose the rendering model deliberately
- Document performance and accessibility implications

### Add a new simulator metric

- Name it with units where needed
- Document it in [api-contracts.md](/Users/stan/Work/clockwork_fullstack/docs/api-contracts.md)
- Handle absent or stale data explicitly in the BFF
- Decide whether it belongs in the browser-facing frame or only in metrics/diagnostics

## CI/CD Expectations

- CI must validate source and image builds
- Published images should be immutable and versionable
- Deployments should be image-driven, not source-driven on the target host
- Deployment workflows must include health validation or smoke tests

## Logging and Test Expectations

- Every runtime service must expose health endpoints
- Runtime logs should be structured
- Visual/runtime behavior requires automated tests where practical and a clear demo story when user-facing
- Cross-service integration changes should be covered by [tests/integration/test_stack.py](/Users/stan/Work/clockwork_fullstack/tests/integration/test_stack.py)
