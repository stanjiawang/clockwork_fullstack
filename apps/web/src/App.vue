<script setup lang="ts">
import { computed, ref } from 'vue'
import CommandBar from '@/components/shell/CommandBar.vue'
import SidebarNav from '@/components/shell/SidebarNav.vue'
import { useAnimationLoop } from '@/composables/useAnimationLoop'
import { useSocket } from '@/composables/useSocket'
import { useDashboardViewModel } from '@/composables/useDashboardViewModel'
import type { AgentStatusItem, CommandAction, SidebarNavItem } from '@/types/ui'
import DashboardView from '@/views/DashboardView.vue'

const sidebarCollapsed = ref(false)
const { latestFrame, connectionState, lastFrameAgeMs, droppedFrames, tick } = useSocket()
const {
  store,
  diagnostics,
  storeLastFrameAgeMs,
  storeConnectionState,
  summary,
  topology,
  mergedNodes,
  hostOptions,
  matchedNodeCount,
  totalNodeCount,
  filterSummary,
  scenarioName,
  scenarioReasonCode,
  scenarioControlAvailable,
  scenarioControlMessage,
  isScenarioMutationPending,
  selectedNodeDetail,
  selectedNodeId,
  hoveredNodeId,
  searchTerm,
  selectedHostId,
  activeSeverities,
  isTopologyLoading,
  loadErrorMessage,
  freshnessBudgetMs,
  isFreshEnough,
  triggerScenario,
} = useDashboardViewModel()

let lastFpsMark = performance.now()
let frames = 0
let lastDroppedFrames = -1

useAnimationLoop((timestamp) => {
  tick()
  if (latestFrame.value) {
    store.applyFrame(latestFrame.value)
  }
  store.setConnectionState(connectionState.value)
  store.setLastFrameAgeMs(lastFrameAgeMs.value)
  if (droppedFrames.value !== lastDroppedFrames) {
    store.setDroppedFrames(droppedFrames.value)
    lastDroppedFrames = droppedFrames.value
  }
  frames += 1
  if (timestamp - lastFpsMark >= 1000) {
    store.setDiagnostics(frames, droppedFrames.value)
    frames = 0
    lastFpsMark = timestamp
  }
})

const sidebarItems = computed<SidebarNavItem[]>(() => [
  { id: 'overview', label: 'Overview', icon: 'overview', active: true },
  { id: 'fabric', label: 'Fabric map', icon: 'fabric', active: false, badge: `${matchedNodeCount.value}` },
  { id: 'agents', label: 'Agents', icon: 'agents', active: false, badge: '3' },
  { id: 'runtime', label: 'Runtime', icon: 'runtime', active: false },
])

const agentStatuses = computed<AgentStatusItem[]>(() => {
  const transportStatus: AgentStatusItem['status'] =
    storeConnectionState.value === 'open' && !loadErrorMessage.value
      ? 'healthy'
      : storeConnectionState.value === 'connecting'
        ? 'degraded'
        : 'offline'

  return [
    {
      id: 'frontend',
      label: 'Frontend',
      status: diagnostics.value.droppedFrames > 0 ? 'degraded' : 'healthy',
      description: `${diagnostics.value.fps} FPS · ${diagnostics.value.droppedFrames} dropped`,
    },
    {
      id: 'bff',
      label: 'BFF',
      status: transportStatus,
      description: loadErrorMessage.value || `${storeConnectionState.value} · ${storeLastFrameAgeMs.value}ms frame age`,
    },
    {
      id: 'backend',
      label: 'Simulator',
      status: scenarioControlAvailable.value ? 'healthy' : 'degraded',
      description: scenarioControlAvailable.value ? `Scenario ${scenarioName.value}` : scenarioControlMessage.value,
    },
  ]
})

const commandActions = computed<CommandAction[]>(() => [
  {
    id: 'baseline',
    label: 'Baseline',
    icon: 'baseline',
    intent: 'secondary',
    disabled: !scenarioControlAvailable.value || isScenarioMutationPending.value,
  },
  {
    id: 'straggler-burst',
    label: 'Burst',
    icon: 'straggler-burst',
    intent: 'primary',
    disabled: !scenarioControlAvailable.value || isScenarioMutationPending.value,
  },
  {
    id: 'auto',
    label: 'Auto',
    icon: 'auto',
    intent: 'ghost',
    disabled: !scenarioControlAvailable.value || isScenarioMutationPending.value,
  },
])

const searchSuggestions = computed(() => {
  const values = new Set<string>()

  for (const node of mergedNodes.value) {
    values.add(node.node_id)
  }

  for (const hostId of hostOptions.value) {
    values.add(hostId)
  }

  for (const agent of agentStatuses.value) {
    values.add(agent.label)
  }

  values.add(scenarioName.value)
  values.add('critical')
  values.add('warn')
  values.add('healthy')

  return Array.from(values).slice(0, 16)
})

const handleCommandAction = (actionId: string) => {
  if (actionId === 'baseline' || actionId === 'straggler-burst' || actionId === 'auto') {
    void triggerScenario(actionId)
  }
}
</script>

<template>
  <a class="sr-only focus:not-sr-only fixed left-4 top-4 z-50 rounded-control border border-border-default bg-surface px-4 py-2 text-sm text-default" href="#main-content">
    Skip to main content
  </a>

  <div class="min-h-screen bg-canvas text-default">
    <div class="mx-auto flex min-h-screen max-w-shell">
      <SidebarNav
        :collapsed="sidebarCollapsed"
        :items="sidebarItems"
        :agent-statuses="agentStatuses"
        @toggle="sidebarCollapsed = !sidebarCollapsed"
      />

      <div class="flex min-h-screen min-w-0 flex-1 flex-col">
        <CommandBar
          :actions="commandActions"
          :agent-statuses="agentStatuses"
          :current-scenario="scenarioName"
          :search-suggestions="searchSuggestions"
          :search-term="searchTerm"
          @update:search-term="store.setSearchTerm"
          @action="handleCommandAction"
        />

        <main id="main-content" class="flex-1 overflow-x-hidden p-6" tabindex="-1">
          <DashboardView
            :summary="summary"
            :topology="topology"
            :nodes="mergedNodes"
            :selected-node-id="selectedNodeId"
            :hovered-node-id="hoveredNodeId"
            :selected-node-detail="selectedNodeDetail"
            :host-options="hostOptions"
            :selected-host-id="selectedHostId"
            :active-severities="activeSeverities"
            :matched-node-count="matchedNodeCount"
            :total-node-count="totalNodeCount"
            :filter-summary="filterSummary"
            :diagnostics="diagnostics"
            :connection-state="storeConnectionState"
            :last-frame-age-ms="storeLastFrameAgeMs"
            :freshness-budget-ms="freshnessBudgetMs"
            :scenario-name="scenarioName"
            :scenario-reason-code="scenarioReasonCode"
            :scenario-control-available="scenarioControlAvailable"
            :scenario-control-message="scenarioControlMessage"
            :scenario-mutation-pending="isScenarioMutationPending"
            :is-topology-loading="isTopologyLoading"
            :load-error-message="loadErrorMessage"
            :is-fresh-enough="isFreshEnough"
            @select-node="store.selectNode"
            @hover-node="store.setHoveredNodeId"
            @clear-hover="store.setHoveredNodeId(null)"
            @update-selected-host-id="store.setSelectedHostId"
            @toggle-severity="store.toggleSeverity"
            @reset-filters="store.resetFilters"
            @trigger-scenario="triggerScenario"
          />
        </main>
      </div>
    </div>
  </div>
</template>
