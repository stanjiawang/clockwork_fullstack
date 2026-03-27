<script setup lang="ts">
import type { Severity } from '@clockwork/contracts'

const props = defineProps<{
  searchTerm: string
  hostOptions: string[]
  selectedHostId: string | null
  activeSeverities: Severity[]
  matchedNodeCount: number
  totalNodeCount: number
  scenarioName: string
  scenarioReasonCode: string
  scenarioControlAvailable: boolean
  scenarioControlMessage: string
  scenarioMutationPending: boolean
  filterSummary: string
}>()

const emit = defineEmits<{
  'update:search-term': [value: string]
  'update:selected-host-id': [value: string | null]
  'toggle-severity': [value: Severity]
  'reset-filters': []
  'trigger-scenario': [value: 'auto' | 'baseline' | 'straggler-burst']
}>()

const severityMeta: Record<Severity, { label: string; tone: string; description: string }> = {
  healthy: {
    label: 'Healthy',
    tone: 'bg-info/15 text-info border-info/20',
    description: 'Nodes within the expected drift and latency budget.',
  },
  warn: {
    label: 'Warn',
    tone: 'bg-warning/15 text-warning border-warning/20',
    description: 'Nodes starting to drift or show early latency pressure.',
  },
  critical: {
    label: 'Critical',
    tone: 'bg-danger/15 text-danger border-danger/20',
    description: 'Stragglers that warrant immediate investigation.',
  },
}

const scenarioModes = [
  {
    id: 'baseline',
    label: 'Baseline',
    description: 'Nominal fabric synchronization with low jitter.',
  },
  {
    id: 'straggler-burst',
    label: 'Straggler burst',
    description: 'Synthetic drift and packet loss burst across a host cohort.',
  },
]
</script>

<template>
  <section class="panel">
    <div class="panel-header">
      <div>
        <div class="metric-label">Control surface</div>
        <h2 class="section-title">Filters and scenario control</h2>
        <p class="lead-copy">
          Narrow the active cohort first, then switch scenarios only when you need to force a diagnostic narrative.
        </p>
      </div>
      <div class="flex flex-col items-end gap-2 text-right">
        <span class="pill">
          <span class="metric-label">Scenario</span>
          <span class="capitalize">{{ scenarioName }}</span>
        </span>
        <span class="text-xs text-muted">{{ scenarioReasonCode }}</span>
      </div>
    </div>
    <div class="panel-body pt-0">
      <div class="grid gap-4">
        <div class="detail-card">
          <div class="metric-label">Active readout</div>
          <p class="mt-2 text-sm leading-6 text-fg">
            {{ matchedNodeCount }} of {{ totalNodeCount }} nodes match the current filters.
          </p>
          <p class="mt-2 text-xs leading-6 text-muted">{{ filterSummary }}</p>
        </div>

        <div class="grid gap-4">
          <label class="grid gap-2">
            <span class="metric-label">Search node or host</span>
            <input
              :value="searchTerm"
              class="rounded-card border border-border bg-surface-soft px-4 py-3 text-sm text-fg placeholder:text-muted"
              placeholder="gpu-12-05, host-12"
              type="search"
              @input="emit('update:search-term', ($event.target as HTMLInputElement).value)"
            />
          </label>

          <div class="grid gap-2 detail-card">
            <div class="metric-label">Host filter</div>
            <div class="flex flex-wrap gap-2">
              <button
                class="pill"
                :class="selectedHostId === null ? 'bg-info/15 text-info border-info/20' : ''"
                type="button"
                @click="emit('update:selected-host-id', null)"
              >
                All hosts
              </button>
              <button
                v-for="hostId in hostOptions"
                :key="hostId"
                class="pill"
                :class="selectedHostId === hostId ? 'bg-info/15 text-info border-info/20' : ''"
                type="button"
                @click="emit('update:selected-host-id', hostId)"
                >
                {{ hostId }}
              </button>
            </div>
          </div>

          <div class="grid gap-2 detail-card">
            <div class="metric-label">Severity filters</div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="severity in (['healthy', 'warn', 'critical'] as Severity[])"
                :key="severity"
                class="pill"
                :class="activeSeverities.includes(severity) ? severityMeta[severity].tone : 'border-border-soft text-muted'"
                type="button"
                @click="emit('toggle-severity', severity)"
              >
                {{ severityMeta[severity].label }}
              </button>
              <button class="pill" type="button" @click="emit('reset-filters')">Clear filters</button>
            </div>
          </div>
        </div>

        <div class="grid gap-4">
          <div class="detail-card">
            <div class="metric-label">Scenario availability</div>
            <p class="mt-2 text-sm leading-6 text-fg">
              Current demo scenario: <span class="capitalize font-semibold">{{ scenarioName }}</span>
            </p>
            <p class="mt-2 text-xs leading-6 text-muted">{{ scenarioControlMessage }}</p>
            <div class="mt-4 grid gap-2">
              <button
                v-for="mode in scenarioModes"
                :key="mode.id"
                class="pill justify-between"
                type="button"
                :disabled="!scenarioControlAvailable || scenarioMutationPending"
                :title="scenarioControlMessage"
                @click="emit('trigger-scenario', mode.id as 'baseline' | 'straggler-burst')"
              >
                <span>{{ mode.label }}</span>
                <span class="text-xs text-muted">{{ mode.description }}</span>
              </button>
              <button
                class="pill justify-between"
                type="button"
                :disabled="!scenarioControlAvailable || scenarioMutationPending"
                :title="scenarioControlMessage"
                @click="emit('trigger-scenario', 'auto')"
              >
                <span>Auto</span>
                <span class="text-xs text-muted">Return to the seeded automatic burst schedule.</span>
              </button>
            </div>
          </div>

          <div class="detail-card">
            <div class="metric-label">Operator guidance</div>
            <ul class="mt-2 grid gap-2 text-sm leading-6 text-fg">
              <li>Use search when you already know the host or GPU cohort you want.</li>
              <li>Use severity filters when you need a rapid triage pass across the fabric.</li>
              <li>Trigger a scenario only after the baseline reading is understood.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
