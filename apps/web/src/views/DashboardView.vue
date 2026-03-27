<script setup lang="ts">
import { AlertTriangle, ArrowRight, Gauge, Layers3 } from 'lucide-vue-next'
import { computed } from 'vue'
import type { ClusterSummary, NodeDetail, Severity, TopologyResponse } from '@clockwork/contracts'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseCard from '@/components/base/BaseCard.vue'
import BaseSelect from '@/components/base/BaseSelect.vue'
import ClusterMap from '@/components/ClusterMap.vue'
import JitterChart from '@/components/JitterChart.vue'
import KpiCard from '@/components/KpiCard.vue'
import NodeDetailPanel from '@/components/NodeDetailPanel.vue'
import StatusPill from '@/components/shell/StatusPill.vue'
import StatePanel from '@/components/shell/StatePanel.vue'
import type { DashboardNode } from '@/composables/useDashboardViewModel'

interface DiagnosticsState {
  fps: number
  droppedFrames: number
}

interface DashboardViewProps {
  summary: ClusterSummary | null
  topology: TopologyResponse | null
  nodes: DashboardNode[]
  selectedNodeId: string | null
  hoveredNodeId: string | null
  selectedNodeDetail: NodeDetail | null
  hostOptions: string[]
  selectedHostId: string | null
  activeSeverities: Severity[]
  matchedNodeCount: number
  totalNodeCount: number
  filterSummary: string
  diagnostics: DiagnosticsState
  connectionState: 'connecting' | 'open' | 'closed'
  lastFrameAgeMs: number
  freshnessBudgetMs: number
  scenarioName: string
  scenarioReasonCode: string
  scenarioControlAvailable: boolean
  scenarioControlMessage: string
  scenarioMutationPending: boolean
  isTopologyLoading: boolean
  loadErrorMessage: string
  isFreshEnough: boolean
}

const props = defineProps<DashboardViewProps>()

const emit = defineEmits<{
  selectNode: [nodeId: string | null]
  hoverNode: [nodeId: string]
  clearHover: []
  updateSelectedHostId: [value: string | null]
  toggleSeverity: [value: Severity]
  resetFilters: []
  triggerScenario: [value: 'auto' | 'baseline' | 'straggler-burst']
}>()

const priorityLabel = computed(() => {
  const score = props.summary?.health_score ?? 0
  if (score >= 90) {
    return 'Fabric stable'
  }
  if (score >= 70) {
    return 'Watch warning cohort'
  }
  return 'Intervene now'
})

const priorityTone = computed(() => {
  const score = props.summary?.health_score ?? 0
  if (score >= 90) {
    return 'healthy'
  }
  if (score >= 70) {
    return 'degraded'
  }
  return 'offline'
})

const selectedHostValue = computed({
  get: () => props.selectedHostId ?? '',
  set: (value: string) => emit('updateSelectedHostId', value || null),
})

const runtimeStatus = computed(() => {
  if (props.connectionState === 'closed' || props.loadErrorMessage) {
    return 'offline'
  }
  if (!props.isFreshEnough || props.connectionState === 'connecting') {
    return 'degraded'
  }
  return 'healthy'
})

const formatFixedMetric = (value: number | null | undefined, digits = 2) => {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return '—'
  }
  return value.toFixed(digits)
}

const kpiValues = computed(() => ({
  healthScore: formatFixedMetric(props.summary?.health_score, 2),
  stragglers: typeof props.summary?.straggler_count === 'number' ? String(props.summary.straggler_count) : '—',
  p95Latency: formatFixedMetric(props.summary?.p95_latency_us, 2),
  syncStability: formatFixedMetric(props.summary?.sync_stability_index, 3),
}))

const hostFilterOptions = computed(() => [
  { label: 'All hosts', value: '' },
  ...props.hostOptions.map((hostId) => ({ label: hostId, value: hostId })),
])
</script>

<template>
  <section class="grid gap-6">
    <BaseCard padding="hero">
      <template #header>
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-normal text-subtle">Cluster status</p>
            <h2 class="mt-2 text-3xl font-semibold tracking-tight text-strong">AI Fabric Health Monitor</h2>
          </div>
          <StatusPill label="Priority" :value="priorityLabel" :status="priorityTone" />
        </div>
      </template>

      <div class="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(280px,0.65fr)]">
        <div>
          <p class="max-w-2xl text-base leading-relaxed tracking-normal text-subtle">
            Industrial telemetry view for clock drift, GPU-to-GPU latency pressure, and straggler remediation. Read left to right: cluster health, concentrated topology issues, then the recommended action for the selected node.
          </p>
          <div class="mt-6 grid gap-4 md:grid-cols-2">
            <KpiCard label="Health score" :value="kpiValues.healthScore" />
            <KpiCard label="Stragglers" :value="kpiValues.stragglers" />
            <KpiCard label="P95 latency (us)" :value="kpiValues.p95Latency" />
            <KpiCard label="Sync stability" :value="kpiValues.syncStability" />
          </div>
        </div>

        <div class="rounded-card border border-border-subtle bg-canvas px-6 py-6">
          <p class="text-xs uppercase tracking-normal text-subtle">Operational priority</p>
          <h3 class="mt-3 text-xl font-semibold tracking-tight text-strong">Current recommendation</h3>
          <p class="mt-4 text-sm leading-relaxed tracking-normal text-subtle">
            {{ summary?.health_score && summary.health_score >= 90
              ? 'Baseline conditions are healthy. Use the topology to confirm local anomalies before forcing scenario changes.'
              : summary?.health_score && summary.health_score >= 70
                ? 'Watch the warning cohort and confirm whether degradation is host-local or spreading across the fabric.'
                : 'Prioritize the critical cohort, inspect the selected node, and apply the recommended mitigation path.' }}
          </p>
          <div class="mt-6 grid gap-3">
            <div class="flex items-center gap-3 rounded-control border border-border-subtle px-4 py-3">
              <Layers3 aria-hidden="true" class="h-4 w-4 text-subtle" />
              <span class="text-sm tracking-normal text-default">Read the topology for host concentration first.</span>
            </div>
            <div class="flex items-center gap-3 rounded-control border border-border-subtle px-4 py-3">
              <Gauge aria-hidden="true" class="h-4 w-4 text-subtle" />
              <span class="text-sm tracking-normal text-default">Use runtime signals to separate live instability from transport lag.</span>
            </div>
            <div class="flex items-center gap-3 rounded-control border border-border-subtle px-4 py-3">
              <ArrowRight aria-hidden="true" class="h-4 w-4 text-subtle" />
              <span class="text-sm tracking-normal text-default">Act from the selected-node decision panel, not the map alone.</span>
            </div>
          </div>
        </div>
      </div>
    </BaseCard>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1.5fr)_380px]">
      <BaseCard>
        <template #header>
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div class="min-w-0">
              <p class="text-xs uppercase tracking-normal text-subtle">Primary workspace</p>
              <h2 class="mt-2 text-xl font-semibold tracking-tight text-strong">Fabric topology</h2>
              <p class="mt-2 max-w-2xl text-sm leading-relaxed tracking-normal text-subtle">
                Read pod concentration first, then inspect selected GPUs. Filter changes should narrow the cohort without erasing the surrounding fabric context.
              </p>
            </div>
            <div class="flex flex-wrap items-center gap-2">
              <StatusPill label="Connection" :value="connectionState" :status="runtimeStatus" />
              <StatusPill label="Frame age" :value="`${lastFrameAgeMs}ms`" :status="runtimeStatus" />
            </div>
          </div>
        </template>

        <div v-if="isTopologyLoading">
          <StatePanel kind="loading" title="Loading topology" message="Fetching the latest interconnect graph from the BFF without shifting the workspace layout." />
        </div>
        <div v-else-if="loadErrorMessage">
          <StatePanel kind="error" title="Topology unavailable" :message="loadErrorMessage" action-label="Check BFF and simulator connectivity" />
        </div>
        <div v-else-if="!topology">
          <StatePanel kind="empty" title="No topology loaded" message="The topology workspace is reserved and stable, but no graph has been returned yet." />
        </div>
        <div v-else class="grid gap-4">
          <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_220px]">
            <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
              <p class="text-xs uppercase tracking-normal text-subtle">Active cohort</p>
              <p class="mt-3 text-sm leading-relaxed tracking-normal text-default">{{ matchedNodeCount }} of {{ totalNodeCount }} nodes visible</p>
              <p class="mt-2 text-sm leading-relaxed tracking-normal text-subtle">{{ filterSummary }}</p>
            </div>
            <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
              <p class="text-xs uppercase tracking-normal text-subtle">Current read</p>
              <p class="mt-3 text-sm leading-relaxed tracking-normal text-default">
                {{ selectedNodeId ? 'Decision rail locked to selected node.' : 'Select a warning or critical GPU to lock remediation context.' }}
              </p>
            </div>
          </div>

          <ClusterMap
            :topology="topology"
            :nodes="nodes"
            :selected-node-id="selectedNodeId"
            :hovered-node-id="hoveredNodeId"
            @select="emit('selectNode', $event)"
            @hover-node="emit('hoverNode', $event)"
            @clear-hover="emit('clearHover')"
          />
        </div>
      </BaseCard>

      <div class="grid gap-4 xl:grid-rows-[minmax(0,1fr)_auto]">
        <BaseCard min-height="100%">
          <template #header>
            <div class="min-w-0">
              <p class="text-xs uppercase tracking-normal text-subtle">Selection</p>
              <h2 class="mt-2 text-lg font-semibold tracking-tight text-strong">Node decision panel</h2>
              <p class="mt-2 text-sm leading-relaxed tracking-normal text-subtle">
                Keep this panel adjacent to the topology so action and evidence stay in the same reading path.
              </p>
            </div>
          </template>

          <NodeDetailPanel :detail="selectedNodeDetail" />
        </BaseCard>

        <BaseCard>
          <template #header>
            <div class="min-w-0">
              <p class="text-xs uppercase tracking-normal text-subtle">Filter context</p>
              <h2 class="mt-2 text-lg font-semibold tracking-tight text-strong">Cohort controls</h2>
              <p class="mt-2 text-sm leading-relaxed tracking-normal text-subtle">
                Narrow the visible cohort without losing map readability. Use host scope first, then severity refinement.
              </p>
            </div>
          </template>

          <div class="grid gap-4">
            <div class="grid gap-4 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
              <label class="grid gap-2">
                <span class="text-xs uppercase tracking-normal text-subtle">Host filter</span>
                <BaseSelect
                  aria-label="Filter topology by host"
                  v-model="selectedHostValue"
                  :options="hostFilterOptions"
                />
              </label>

              <BaseButton size="sm" variant="subtle" @click="emit('resetFilters')">Reset filters</BaseButton>
            </div>

            <div class="grid gap-3">
              <span class="text-xs uppercase tracking-normal text-subtle">Severity filters</span>
              <div class="flex flex-wrap gap-2">
                <BaseButton
                  v-for="severity in (['healthy', 'warn', 'critical'] as Severity[])"
                  :key="severity"
                  :variant="activeSeverities.includes(severity) ? 'secondary' : 'ghost'"
                  size="sm"
                  @click="emit('toggleSeverity', severity)"
                >
                  {{ severity }}
                </BaseButton>
              </div>
            </div>

            <div class="grid gap-3 sm:grid-cols-3">
              <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
                <div class="flex items-start gap-3">
                  <span class="mt-1 h-3 w-3 rounded-full bg-primary-600" />
                  <div>
                    <p class="text-sm tracking-normal text-default">Healthy</p>
                    <p class="mt-1 text-xs leading-relaxed tracking-normal text-subtle">Stable drift envelope.</p>
                  </div>
                </div>
              </div>
              <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
                <div class="flex items-start gap-3">
                  <span class="mt-1 h-3 w-3 rounded-full bg-warning-500" />
                  <div>
                    <p class="text-sm tracking-normal text-default">Warn</p>
                    <p class="mt-1 text-xs leading-relaxed tracking-normal text-subtle">Escalating instability.</p>
                  </div>
                </div>
              </div>
              <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
                <div class="flex items-start gap-3">
                  <span class="mt-1 h-3 w-3 rounded-full bg-white/60" />
                  <div>
                    <p class="text-sm tracking-normal text-default">Context only</p>
                    <p class="mt-1 text-xs leading-relaxed tracking-normal text-subtle">Filtered but preserved.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </BaseCard>
      </div>
    </div>

    <div class="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
      <BaseCard>
        <template #header>
          <div>
            <p class="text-xs uppercase tracking-normal text-subtle">Trend analysis</p>
            <h2 class="mt-2 text-lg font-semibold tracking-tight text-strong">Global health over time</h2>
          </div>
        </template>

        <div class="grid gap-4">
          <template v-if="summary">
            <div class="grid gap-4 sm:grid-cols-3">
              <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
                <p class="text-xs uppercase tracking-normal text-subtle">Current health</p>
                <p class="mt-3 text-3xl font-semibold tracking-tight tabular-nums text-strong">
                  {{ kpiValues.healthScore }}
                </p>
              </div>
              <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
                <p class="text-xs uppercase tracking-normal text-subtle">Trend state</p>
                <p class="mt-3 text-2xl font-semibold tracking-tight text-strong">
                  {{ summary.health_score >= 90 ? 'Stable' : summary.health_score >= 70 ? 'Watch' : 'Degraded' }}
                </p>
              </div>
              <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
                <p class="text-xs uppercase tracking-normal text-subtle">Stragglers</p>
                <p class="mt-3 text-3xl font-semibold tracking-tight tabular-nums text-strong">
                  {{ kpiValues.stragglers }}
                </p>
              </div>
            </div>
            <JitterChart :summary="summary" />
          </template>
          <StatePanel
            v-else
            kind="empty"
            title="No health trend yet"
            message="The chart reserves its footprint immediately and will populate once the cluster summary arrives."
          />
        </div>
      </BaseCard>

      <div class="grid gap-6">
        <BaseCard>
          <template #header>
            <div>
              <p class="text-xs uppercase tracking-normal text-subtle">Runtime telemetry</p>
              <h2 class="mt-2 text-lg font-semibold tracking-tight text-strong">Operational signals</h2>
            </div>
          </template>

          <div class="grid gap-4 sm:grid-cols-2">
            <div class="min-w-0 rounded-control border border-border-subtle bg-canvas px-4 py-4">
              <p class="text-xs uppercase tracking-normal text-subtle">Approx FPS</p>
              <p class="mt-3 overflow-hidden text-[clamp(1.75rem,3vw,2.25rem)] leading-none font-semibold tracking-tight text-strong [overflow-wrap:anywhere]">
                {{ diagnostics.fps }}
              </p>
            </div>
            <div class="min-w-0 rounded-control border border-border-subtle bg-canvas px-4 py-4">
              <p class="text-xs uppercase tracking-normal text-subtle">Dropped frames</p>
              <p class="mt-3 overflow-hidden text-[clamp(1.75rem,3vw,2.25rem)] leading-none font-semibold tracking-tight text-strong [overflow-wrap:anywhere]">
                {{ diagnostics.droppedFrames }}
              </p>
            </div>
            <div class="min-w-0 rounded-control border border-border-subtle bg-canvas px-4 py-4">
              <p class="text-xs uppercase tracking-normal text-subtle">Freshness budget</p>
              <p class="mt-3 overflow-hidden text-[clamp(1.75rem,3vw,2.25rem)] leading-none font-semibold tracking-tight text-strong [overflow-wrap:anywhere]">
                {{ freshnessBudgetMs }}ms
              </p>
            </div>
            <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
              <p class="text-xs uppercase tracking-normal text-subtle">State</p>
              <div class="mt-3">
                <StatusPill label="Transport" :value="scenarioReasonCode" :status="runtimeStatus" />
              </div>
            </div>
          </div>
        </BaseCard>

        <BaseCard>
          <template #header>
            <div class="flex items-center justify-between gap-4">
              <div>
                <p class="text-xs uppercase tracking-normal text-subtle">Scenario control</p>
                <h2 class="mt-2 text-lg font-semibold tracking-tight text-strong">Simulation actions</h2>
              </div>
              <StatusPill label="Mode" :value="scenarioName" :status="scenarioControlAvailable ? 'healthy' : 'offline'" />
            </div>
          </template>

          <div class="grid gap-4">
            <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
              <div class="flex items-start gap-3">
                <AlertTriangle aria-hidden="true" class="mt-1 h-4 w-4 text-subtle" />
                <p class="text-sm leading-relaxed tracking-normal text-subtle">{{ scenarioControlMessage }}</p>
              </div>
            </div>
            <div class="grid gap-2 sm:grid-cols-3">
              <BaseButton
                :disabled="!scenarioControlAvailable || scenarioMutationPending"
                variant="secondary"
                @click="emit('triggerScenario', 'baseline')"
              >
                Baseline
              </BaseButton>
              <BaseButton
                :disabled="!scenarioControlAvailable || scenarioMutationPending"
                variant="primary"
                @click="emit('triggerScenario', 'straggler-burst')"
              >
                Straggler burst
              </BaseButton>
              <BaseButton
                :disabled="!scenarioControlAvailable || scenarioMutationPending"
                variant="subtle"
                @click="emit('triggerScenario', 'auto')"
              >
                Auto
              </BaseButton>
            </div>
          </div>
        </BaseCard>
      </div>
    </div>
  </section>
</template>
