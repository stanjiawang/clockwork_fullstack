import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { ChangedNode, ClusterFrame, ClusterSummary } from '@clockwork/contracts'

export type NodeState = ChangedNode
export type NodeSeverity = ChangedNode['severity']

type DiagnosticsState = {
  fps: number
  droppedFrames: number
}

type ConnectionState = 'connecting' | 'open' | 'closed'

export const useClusterStore = defineStore('cluster', () => {
  const nodesById = ref<Record<string, NodeState>>({})
  const selectedNodeId = ref<string | null>(null)
  const hoveredNodeId = ref<string | null>(null)
  const searchTerm = ref('')
  const selectedHostId = ref<string | null>(null)
  const activeSeverities = ref<NodeSeverity[]>(['healthy', 'warn', 'critical'])
  const diagnostics = ref<DiagnosticsState>({
    fps: 0,
    droppedFrames: 0,
  })
  const connectionState = ref<ConnectionState>('connecting')
  const lastFrameAgeMs = ref(0)
  const clusterSummary = ref<ClusterSummary | null>(null)

  const nodeList = computed(() => Object.values(nodesById.value))

  const applyFrame = (frame: ClusterFrame) => {
    const nextNodes = { ...nodesById.value }
    for (const changedNode of frame.changed_nodes) {
      nextNodes[changedNode.node_id] = {
        ...nextNodes[changedNode.node_id],
        ...changedNode,
      }
    }
    nodesById.value = nextNodes
    clusterSummary.value = frame.cluster
  }

  const selectNode = (nodeId: string | null) => {
    selectedNodeId.value = nodeId
  }

  const setHoveredNodeId = (nodeId: string | null) => {
    hoveredNodeId.value = nodeId
  }

  const setSearchTerm = (value: string) => {
    searchTerm.value = value
  }

  const setSelectedHostId = (value: string | null) => {
    selectedHostId.value = value
  }

  const toggleSeverity = (severity: NodeSeverity) => {
    if (activeSeverities.value.includes(severity)) {
      const next = activeSeverities.value.filter((entry) => entry !== severity)
      activeSeverities.value = next.length > 0 ? next : ['healthy', 'warn', 'critical']
      return
    }
    activeSeverities.value = [...activeSeverities.value, severity]
  }

  const resetFilters = () => {
    searchTerm.value = ''
    selectedHostId.value = null
    activeSeverities.value = ['healthy', 'warn', 'critical']
  }

  const setDiagnostics = (fps: number, droppedFrames: number) => {
    diagnostics.value = { fps, droppedFrames }
  }

  const setDroppedFrames = (droppedFrames: number) => {
    diagnostics.value = {
      ...diagnostics.value,
      droppedFrames,
    }
  }

  const setConnectionState = (state: ConnectionState) => {
    connectionState.value = state
  }

  const setLastFrameAgeMs = (value: number) => {
    lastFrameAgeMs.value = value
  }

  return {
    nodesById,
    nodeList,
    selectedNodeId,
    hoveredNodeId,
    searchTerm,
    selectedHostId,
    activeSeverities,
    diagnostics,
    connectionState,
    lastFrameAgeMs,
    clusterSummary,
    applyFrame,
    selectNode,
    setHoveredNodeId,
    setSearchTerm,
    setSelectedHostId,
    toggleSeverity,
    resetFilters,
    setDiagnostics,
    setDroppedFrames,
    setConnectionState,
    setLastFrameAgeMs,
  }
})
