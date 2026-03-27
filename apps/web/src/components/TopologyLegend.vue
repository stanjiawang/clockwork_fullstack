<script setup lang="ts">
const severityItems = [
  {
    label: 'Healthy',
    tone: 'bg-info',
    description: 'Within expected sync drift and latency budget.',
  },
  {
    label: 'Warn',
    tone: 'bg-warning',
    description: 'Emerging jitter or drift pressure.',
  },
  {
    label: 'Critical',
    tone: 'bg-danger',
    description: 'Active straggler requiring operator attention.',
  },
]

const linkItems = [
  {
    label: 'NVLink',
    lineClass: 'bg-success/40',
    description: 'Dense intra-host GPU fabric links.',
  },
  {
    label: 'RoCE',
    lineClass: 'bg-info/40',
    description: 'Aggregated cross-host fabric connectivity.',
  },
]
</script>

<template>
  <section class="panel panel-muted">
    <div class="panel-header">
      <div>
        <div class="metric-label">Legend</div>
        <h2 class="section-title">Visual encoding guide</h2>
      </div>
    </div>
    <div class="panel-body grid gap-4 pt-0">
      <div>
        <div class="metric-label">Severity</div>
        <div class="mt-3 grid gap-3">
          <div v-for="item in severityItems" :key="item.label" class="flex items-start gap-3 rounded-card border border-border-soft bg-surface-soft p-card">
            <span class="mt-1 h-3 w-3 rounded-full" :class="item.tone" />
            <div>
              <div class="text-sm font-semibold text-fg">{{ item.label }}</div>
              <div class="text-xs leading-5 text-muted">{{ item.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <div class="metric-label">Link types</div>
        <div class="mt-3 grid gap-3">
          <div v-for="item in linkItems" :key="item.label" class="flex items-center gap-3 rounded-card border border-border-soft bg-surface-soft p-card">
            <span class="h-0.5 w-10 rounded-full" :class="item.lineClass" />
            <div>
              <div class="text-sm font-semibold text-fg">{{ item.label }}</div>
              <div class="text-xs leading-5 text-muted">{{ item.description }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="rounded-card border border-border-soft bg-surface-soft p-card text-sm leading-6 text-muted">
        Filtered nodes stay dimmed instead of disappearing so the operator retains topology context while narrowing the investigation.
      </div>
    </div>
  </section>
</template>
