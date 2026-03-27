<script setup lang="ts">
import { computed } from 'vue'
import type { ClusterSummary } from '@clockwork/contracts'

const props = defineProps<{
  summary: ClusterSummary | null
}>()

const healthTone = computed(() => {
  const score = props.summary?.health_score ?? 0
  if (score >= 90) {
    return 'text-success'
  }
  if (score >= 70) {
    return 'text-warning'
  }
  return 'text-danger'
})

const healthNarrative = computed(() => {
  const score = props.summary?.health_score ?? 0
  if (score >= 90) {
    return 'Fabric timing is stable. Use the topology workspace to validate local hotspots, not global degradation.'
  }
  if (score >= 70) {
    return 'Cluster health is softening. Prioritize warning cohorts before they turn into training stragglers.'
  }
  return 'Fabric health is degraded. Focus first on critical nodes and host-level concentration in the topology.'
})
</script>

<template>
  <section class="panel">
    <div class="panel-header">
      <div class="summary-shell">
        <div class="summary-copy">
          <div class="metric-label">Cluster health</div>
          <h1 class="hero-title">AI Fabric Health Monitor</h1>
          <p class="lead-copy">A realtime operations view for GPU clock drift, transport instability, and straggler remediation.</p>
        </div>
        <div class="summary-hero-card">
          <div class="metric-label">Current priority</div>
          <div :class="['summary-hero-score', healthTone]">
            {{ summary?.health_score ?? '—' }}
          </div>
          <p class="summary-hero-copy">{{ healthNarrative }}</p>
        </div>
      </div>
    </div>
    <div class="panel-body pt-0">
      <div class="summary-metric-grid">
        <div class="summary-stat-card">
          <div class="metric-label">Stragglers</div>
          <div class="metric-value">{{ summary?.straggler_count ?? '—' }}</div>
          <p class="summary-stat-copy">Nodes currently slowing the training fabric and requiring operator attention.</p>
        </div>
        <div class="summary-stat-card">
          <div class="metric-label">P95 latency (us)</div>
          <div class="metric-value">{{ summary?.p95_latency_us ?? '—' }}</div>
          <p class="summary-stat-copy">Transport variability across the cluster, useful for spotting fabric-level contention.</p>
        </div>
        <div class="summary-stat-card">
          <div class="metric-label">Mean offset (ns)</div>
          <div class="metric-value">{{ summary?.mean_offset_ns ?? '—' }}</div>
          <p class="summary-stat-copy">Aggregate timing drift baseline. Rising values usually precede straggler formation.</p>
        </div>
        <div class="summary-stat-card">
          <div class="metric-label">Sync stability index</div>
          <div class="metric-value">{{ summary?.sync_stability_index ?? '—' }}</div>
          <p class="summary-stat-copy">High-level stability readout combining drift, latency, and node-level anomalies.</p>
        </div>
      </div>
    </div>
  </section>
  
  <section class="panel panel-muted">
    <div class="panel-header">
      <div>
        <div class="metric-label">Operator intent</div>
        <h2 class="section-title">How to use this workspace</h2>
        <p class="lead-copy">Read the summary first, inspect topology second, then use the right sidebar to isolate cohorts and act on the selected node.</p>
      </div>
    </div>
    <div class="panel-body pt-0">
      <div class="summary-priority-strip">
        <div class="summary-priority-item">
          <span class="metric-label">1</span>
          <span>Locate concentration of critical nodes on the topology.</span>
        </div>
        <div class="summary-priority-item">
          <span class="metric-label">2</span>
          <span>Confirm whether degradation is local to a host cohort or cluster-wide.</span>
        </div>
        <div class="summary-priority-item">
          <span class="metric-label">3</span>
          <span>Open node detail and act on the recommended remediation path.</span>
        </div>
      </div>
    </div>
  </section>
</template>
