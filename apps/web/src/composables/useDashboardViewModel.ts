import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import {
  useHealthQuery,
  useMetricsQuery,
  useNodeDetailQuery,
  useScenarioControlMutation,
  useScenarioQuery,
  useTopologyQuery,
} from '@/composables/useClusterQueries'
import { useClusterStore, type NodeState } from '@/stores/useClusterStore'
import type { ScenarioControlRequest, Severity } from '@clockwork/contracts'

export type DashboardNode = NodeState & {
  host_id: string
  group: number
  matchesSearch: boolean
  matchesHost: boolean
  matchesSeverity: boolean
  isVisible: boolean
  isSelected: boolean
  isHovered: boolean
}

export function useDashboardViewModel() {
  const store = useClusterStore()
  const {
    clusterSummary,
    diagnostics,
    lastFrameAgeMs: storeLastFrameAgeMs,
    connectionState: storeConnectionState,
    nodesById,
    selectedNodeId,
    hoveredNodeId,
    searchTerm,
    selectedHostId,
    activeSeverities,
  } =
    storeToRefs(store)

  const topologyQuery = useTopologyQuery()
  const healthQuery = useHealthQuery()
  const metricsQuery = useMetricsQuery()
  const scenarioQuery = useScenarioQuery()
  const scenarioControlMutation = useScenarioControlMutation()
  const nodeDetailQuery = useNodeDetailQuery(selectedNodeId)

  const summary = computed(() => clusterSummary.value ?? healthQuery.data.value?.cluster ?? null)
  const topology = computed(() => topologyQuery.data.value ?? null)
  const topologyNodes = computed(() => topologyQuery.data.value?.nodes ?? [])
  const topologyNodesByHost = computed(() => {
    const next = new Map<string, { id: string; group: number }[]>()
    for (const node of topologyNodes.value) {
      const entries = next.get(node.host_id) ?? []
      entries.push({ id: node.id, group: node.group })
      next.set(node.host_id, entries)
    }
    return next
  })
  const hostOptions = computed(() => Array.from(topologyNodesByHost.value.keys()))
  const normalizedSearch = computed(() => searchTerm.value.trim().toLowerCase())
  const activeSeveritySet = computed(() => new Set<Severity>(activeSeverities.value))
  const mergedNodes = computed<DashboardNode[]>(() => {
    return topologyNodes.value.map((node) => {
      const liveNode = nodesById.value[node.id]
      const severity = liveNode?.severity ?? 'healthy'
      const matchesSearch =
        normalizedSearch.value.length === 0 ||
        node.id.toLowerCase().includes(normalizedSearch.value) ||
        node.host_id.toLowerCase().includes(normalizedSearch.value)
      const matchesHost = selectedHostId.value === null || selectedHostId.value === node.host_id
      const matchesSeverity = activeSeveritySet.value.has(severity)
      const isVisible = matchesSearch && matchesHost && matchesSeverity
      return {
        node_id: node.id,
        clock_offset_ns: liveNode?.clock_offset_ns ?? 0,
        p2p_latency_us: liveNode?.p2p_latency_us ?? 0,
        packet_loss_pct: liveNode?.packet_loss_pct ?? 0,
        severity,
        is_straggler: liveNode?.is_straggler ?? false,
        host_id: node.host_id,
        group: node.group,
        matchesSearch,
        matchesHost,
        matchesSeverity,
        isVisible,
        isSelected: selectedNodeId.value === node.id,
        isHovered: hoveredNodeId.value === node.id,
      }
    })
  })
  const visibleNodes = computed(() => mergedNodes.value.filter((node) => node.isVisible))
  const matchedNodeCount = computed(() => visibleNodes.value.length)
  const totalNodeCount = computed(() => topologyNodes.value.length)
  const scenarioName = computed(() => scenarioQuery.data.value?.name ?? healthQuery.data.value?.scenario ?? 'baseline')
  const scenarioReasonCode = computed(() => healthQuery.data.value?.reason_code ?? metricsQuery.data.value?.reason_code ?? 'ok')
  const scenarioControlAvailable = computed(() => scenarioQuery.data.value?.control_supported ?? false)
  const scenarioControlMessage = computed(() => {
    if (scenarioControlMutation.isPending.value) {
      return 'Applying scenario control request to the simulator...'
    }
    return (
      scenarioQuery.data.value?.message ??
      'Scenario control is not available from the current backend configuration.'
    )
  })
  const filterSummary = computed(() => {
    const selectedHost = selectedHostId.value ?? 'all hosts'
    const search = normalizedSearch.value || 'all nodes'
    const severities = activeSeverities.value.join(', ')
    return `${selectedHost} | ${search} | ${severities}`
  })

  const selectedNodeDetail = computed(() => nodeDetailQuery.data.value ?? null)
  const isTopologyLoading = computed(() => topologyQuery.isPending.value)
  const loadErrorMessage = computed(() => topologyQuery.error.value?.message ?? healthQuery.error.value?.message ?? '')
  const freshnessBudgetMs = 750
  const isFreshEnough = computed(() => storeConnectionState.value === 'open' && storeLastFrameAgeMs.value <= freshnessBudgetMs)
  const badgeLastFrameAgeMs = computed(() => {
    const value = storeLastFrameAgeMs.value
    return value <= 0 ? 0 : Math.max(50, Math.round(value / 50) * 50)
  })

  const triggerScenario = async (scenario: ScenarioControlRequest['scenario']) => {
    await scenarioControlMutation.mutateAsync({
      scenario,
      duration_steps: scenario === 'straggler-burst' ? 32 : undefined,
    })
  }

  return {
    store,
    clusterSummary,
    diagnostics,
    storeLastFrameAgeMs,
    storeConnectionState,
    summary,
    topology,
    mergedNodes,
    visibleNodes,
    hostOptions,
    matchedNodeCount,
    totalNodeCount,
    filterSummary,
    scenarioName,
    scenarioReasonCode,
    scenarioControlAvailable,
    scenarioControlMessage,
    isScenarioMutationPending: computed(() => scenarioControlMutation.isPending.value),
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
    badgeLastFrameAgeMs,
    triggerScenario,
  }
}
