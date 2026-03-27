<script setup lang="ts">
import { computed } from 'vue'
import type { TopologyResponse } from '@clockwork/contracts'
import type { DashboardNode } from '@/composables/useDashboardViewModel'

interface ClusterMapProps {
  topology: TopologyResponse
  nodes: DashboardNode[]
  selectedNodeId: string | null
  hoveredNodeId: string | null
}

type HostRegion = {
  hostId: string
  zoneId: string
  x: number
  y: number
  width: number
  height: number
  nodeIds: string[]
  visibleCount: number
  stragglerCount: number
  dominantSeverity: DashboardNode['severity']
}

type ZoneRegion = {
  id: string
  label: string
  x: number
  y: number
  width: number
  height: number
  hostIds: string[]
  stragglerCount: number
  dominantSeverity: DashboardNode['severity']
}

const props = defineProps<ClusterMapProps>()

const emit = defineEmits<{
  select: [nodeId: string]
  'hover-node': [nodeId: string]
  'clear-hover': []
}>()

const svgWidth = 960
const svgHeight = 660
const zoneWidth = 444
const zoneHeight = 276
const zoneGapX = 20
const zoneGapY = 24
const canvasPaddingX = 24
const canvasPaddingY = 24
const zoneHeaderHeight = 36
const zoneInnerPaddingX = 18
const zoneInnerPaddingY = 18
const hostColumns = 4
const hostWidth = 92
const hostHeight = 86
const hostGapX = 10
const hostGapY = 12
const hostInnerPaddingX = 14
const hostInnerPaddingY = 28
const nodeGapX = 16
const nodeGapY = 16

const zoneLabels = ['Fabric pod A', 'Fabric pod B', 'Fabric pod C', 'Fabric pod D']

const nodeMap = computed(() => new Map(props.nodes.map((node) => [node.node_id, node])))
const topologyNodeMap = computed(() => new Map(props.topology.nodes.map((node) => [node.id, node])))

const sortedHostEntries = computed(() => {
  const byHost = new Map<string, string[]>()
  for (const topologyNode of props.topology.nodes) {
    const nodeIds = byHost.get(topologyNode.host_id) ?? []
    nodeIds.push(topologyNode.id)
    byHost.set(topologyNode.host_id, nodeIds)
  }

  return Array.from(byHost.entries()).sort(([left], [right]) => {
    const leftValue = Number(left.match(/(\d+)$/)?.[1] ?? Number.MAX_SAFE_INTEGER)
    const rightValue = Number(right.match(/(\d+)$/)?.[1] ?? Number.MAX_SAFE_INTEGER)
    return leftValue - rightValue
  })
})

const zoneRegions = computed<ZoneRegion[]>(() =>
  Array.from({ length: 4 }, (_, zoneIndex) => {
    const column = zoneIndex % 2
    const row = Math.floor(zoneIndex / 2)
    const x = canvasPaddingX + column * (zoneWidth + zoneGapX)
    const y = canvasPaddingY + row * (zoneHeight + zoneGapY)
    const hostIds = sortedHostEntries.value.slice(zoneIndex * 8, zoneIndex * 8 + 8).map(([hostId]) => hostId)
    const zoneHosts = hostIds.map((hostId) => {
      const nodeIds = sortedHostEntries.value.find(([entryHostId]) => entryHostId === hostId)?.[1] ?? []
      return nodeIds.map((nodeId) => nodeMap.value.get(nodeId)).filter(Boolean) as DashboardNode[]
    })
    const flatNodes = zoneHosts.flat()
    const stragglerCount = flatNodes.filter((node) => node.is_straggler).length
    const dominantSeverity = flatNodes.some((node) => node.severity === 'critical')
      ? 'critical'
      : flatNodes.some((node) => node.severity === 'warn')
        ? 'warn'
        : 'healthy'

    return {
      id: `zone-${zoneIndex}`,
      label: zoneLabels[zoneIndex],
      x,
      y,
      width: zoneWidth,
      height: zoneHeight,
      hostIds,
      stragglerCount,
      dominantSeverity,
    }
  }),
)

const zoneMap = computed(() => new Map(zoneRegions.value.map((zone) => [zone.id, zone])))
const hostZoneMap = computed(() => {
  const mapping = new Map<string, string>()
  zoneRegions.value.forEach((zone) => {
    zone.hostIds.forEach((hostId) => {
      mapping.set(hostId, zone.id)
    })
  })
  return mapping
})

const hostRegions = computed<HostRegion[]>(() =>
  sortedHostEntries.value.map(([hostId, nodeIds]) => {
    const zoneId = hostZoneMap.value.get(hostId) ?? 'zone-0'
    const zone = zoneMap.value.get(zoneId)
    const zoneHostIndex = zone?.hostIds.indexOf(hostId) ?? 0
    const column = zoneHostIndex % hostColumns
    const row = Math.floor(zoneHostIndex / hostColumns)
    const x = (zone?.x ?? 0) + zoneInnerPaddingX + column * (hostWidth + hostGapX)
    const y = (zone?.y ?? 0) + zoneHeaderHeight + zoneInnerPaddingY + row * (hostHeight + hostGapY)
    const hostNodes = nodeIds.map((nodeId) => nodeMap.value.get(nodeId)).filter(Boolean) as DashboardNode[]
    const stragglerCount = hostNodes.filter((node) => node.is_straggler).length
    const visibleCount = hostNodes.filter((node) => node.isVisible).length
    const dominantSeverity = hostNodes.some((node) => node.severity === 'critical')
      ? 'critical'
      : hostNodes.some((node) => node.severity === 'warn')
        ? 'warn'
        : 'healthy'

    return {
      hostId,
      zoneId,
      x,
      y,
      width: hostWidth,
      height: hostHeight,
      nodeIds,
      visibleCount,
      stragglerCount,
      dominantSeverity,
    }
  }),
)

const hostRegionMap = computed(() => new Map(hostRegions.value.map((host) => [host.hostId, host])))

const nodePositions = computed(() => {
  const positions = new Map<string, { x: number; y: number }>()
  hostRegions.value.forEach((host) => {
    host.nodeIds.forEach((nodeId, index) => {
      const column = index % 4
      const row = Math.floor(index / 4)
      positions.set(nodeId, {
        x: host.x + hostInnerPaddingX + column * nodeGapX,
        y: host.y + hostInnerPaddingY + row * nodeGapY,
      })
    })
  })
  return positions
})

const zoneLinks = computed(() => {
  const seen = new Set<string>()
  const links: Array<{ sourceZoneId: string; targetZoneId: string }> = []

  for (const topologyLink of props.topology.links) {
    const source = topologyNodeMap.value.get(topologyLink.source)
    const target = topologyNodeMap.value.get(topologyLink.target)
    if (!source || !target) {
      continue
    }
    const sourceZoneId = hostZoneMap.value.get(source.host_id)
    const targetZoneId = hostZoneMap.value.get(target.host_id)
    if (!sourceZoneId || !targetZoneId || sourceZoneId === targetZoneId) {
      continue
    }
    const key = [sourceZoneId, targetZoneId].sort().join(':')
    if (seen.has(key)) {
      continue
    }
    seen.add(key)
    links.push({ sourceZoneId, targetZoneId })
  }

  return links
})

const zoneCenter = (zoneId: string) => {
  const zone = zoneMap.value.get(zoneId)
  if (!zone) {
    return { x: 0, y: 0 }
  }
  return {
    x: zone.x + zone.width / 2,
    y: zone.y + zone.height / 2,
  }
}

const hoveredNode = computed(() => props.nodes.find((node) => node.node_id === props.hoveredNodeId) ?? null)
const hoveredPosition = computed(() => (hoveredNode.value ? nodePositions.value.get(hoveredNode.value.node_id) ?? null : null))

const toneFill = (severity: DashboardNode['severity']) => {
  if (severity === 'critical') {
    return 'rgba(245, 158, 11, 0.08)'
  }
  if (severity === 'warn') {
    return 'rgba(91, 140, 255, 0.07)'
  }
  return 'rgba(255,255,255,0.02)'
}

const toneStroke = (severity: DashboardNode['severity']) => {
  if (severity === 'critical') {
    return 'rgba(245, 158, 11, 0.24)'
  }
  if (severity === 'warn') {
    return 'rgba(91, 140, 255, 0.22)'
  }
  return 'rgba(255,255,255,0.10)'
}

const nodeFill = (nodeId: string) => {
  const node = nodeMap.value.get(nodeId)
  if (!node) {
    return '#d6deed'
  }
  if (node.severity === 'critical') {
    return '#f59e0b'
  }
  if (node.severity === 'warn') {
    return '#5b8cff'
  }
  return '#d6deed'
}

const nodeStroke = (nodeId: string) => {
  if (props.selectedNodeId === nodeId) {
    return '#f8fbff'
  }
  if (props.hoveredNodeId === nodeId) {
    return 'rgba(248,251,255,0.72)'
  }
  return 'rgba(255,255,255,0.14)'
}

const nodeRadius = (nodeId: string) => {
  const node = nodeMap.value.get(nodeId)
  if (props.selectedNodeId === nodeId) {
    return 6
  }
  if (node?.is_straggler) {
    return 5
  }
  return 4
}

const shortHostLabel = (hostId: string) => hostId.replace(/^host-/, 'H')
</script>

<template>
  <div class="relative overflow-hidden rounded-card border border-border-subtle bg-canvas">
    <svg :viewBox="`0 0 ${svgWidth} ${svgHeight}`" class="h-[660px] w-full" preserveAspectRatio="xMidYMid meet">
      <g>
        <line
          v-for="link in zoneLinks"
          :key="`${link.sourceZoneId}-${link.targetZoneId}`"
          :x1="zoneCenter(link.sourceZoneId).x"
          :y1="zoneCenter(link.sourceZoneId).y"
          :x2="zoneCenter(link.targetZoneId).x"
          :y2="zoneCenter(link.targetZoneId).y"
          stroke="rgba(91,140,255,0.14)"
          stroke-width="1.5"
        />

        <g v-for="zone in zoneRegions" :key="zone.id">
          <rect
            :x="zone.x"
            :y="zone.y"
            :width="zone.width"
            :height="zone.height"
            rx="16"
            :fill="toneFill(zone.dominantSeverity)"
            :stroke="toneStroke(zone.dominantSeverity)"
          />
          <line
            :x1="zone.x + 1"
            :y1="zone.y + zoneHeaderHeight"
            :x2="zone.x + zone.width - 1"
            :y2="zone.y + zoneHeaderHeight"
            stroke="rgba(255,255,255,0.08)"
          />
          <text :x="zone.x + 16" :y="zone.y + 20" fill="#f8fbff" font-size="12" font-weight="600">
            {{ zone.label }}
          </text>
          <text :x="zone.x + zone.width - 16" :y="zone.y + 20" fill="#8c98ad" font-size="10" text-anchor="end">
            {{ zone.stragglerCount }} stragglers
          </text>
        </g>

        <g v-for="host in hostRegions" :key="host.hostId">
          <rect
            :x="host.x"
            :y="host.y"
            :width="host.width"
            :height="host.height"
            rx="12"
            fill="rgba(9, 13, 22, 0.82)"
            :stroke="toneStroke(host.dominantSeverity)"
          />
          <text :x="host.x + 10" :y="host.y + 14" fill="#f8fbff" font-size="10" font-weight="600">
            {{ shortHostLabel(host.hostId) }}
          </text>
          <text :x="host.x + host.width - 10" :y="host.y + 14" fill="#8c98ad" font-size="9" text-anchor="end">
            {{ host.stragglerCount > 0 ? `${host.stragglerCount} hot` : 'stable' }}
          </text>
          <circle
            v-for="nodeId in host.nodeIds"
            :key="nodeId"
            :cx="nodePositions.get(nodeId)?.x ?? 0"
            :cy="nodePositions.get(nodeId)?.y ?? 0"
            :r="nodeRadius(nodeId)"
            :fill="nodeFill(nodeId)"
            :stroke="nodeStroke(nodeId)"
            :stroke-width="props.selectedNodeId === nodeId ? 2 : 1"
            :opacity="nodeMap.get(nodeId)?.isVisible ? 1 : 0.18"
            class="cursor-pointer transition-opacity duration-150 ease-industrial"
            role="button"
            :aria-label="`Select ${nodeId}`"
            tabindex="0"
            @click="emit('select', nodeId)"
            @mouseenter="emit('hover-node', nodeId)"
            @mouseleave="emit('clear-hover')"
            @focus="emit('hover-node', nodeId)"
            @blur="emit('clear-hover')"
            @keydown.enter.prevent="emit('select', nodeId)"
            @keydown.space.prevent="emit('select', nodeId)"
          />
          <text
            v-if="host.visibleCount < host.nodeIds.length"
            :x="host.x + 10"
            :y="host.y + host.height - 10"
            fill="#8c98ad"
            font-size="9"
          >
            {{ host.visibleCount }}/{{ host.nodeIds.length }} visible
          </text>
        </g>
      </g>
    </svg>

    <div
      v-if="hoveredNode && hoveredPosition"
      class="pointer-events-none absolute max-w-[256px] rounded-card border border-border-subtle bg-elevated px-4 py-4"
      :style="{ left: `${Math.min(hoveredPosition.x + 18, svgWidth - 280)}px`, top: `${Math.min(Math.max(hoveredPosition.y - 18, 16), svgHeight - 136)}px` }"
    >
      <p class="text-xs uppercase tracking-normal text-subtle">Hover context</p>
      <h3 class="mt-2 text-sm font-semibold tracking-tight text-strong">{{ hoveredNode.node_id }}</h3>
      <p class="mt-1 text-xs tracking-normal text-subtle">{{ hoveredNode.host_id }} · group {{ hoveredNode.group }}</p>
      <div class="mt-4 grid grid-cols-2 gap-2 text-xs tracking-normal text-subtle">
        <span>Offset</span>
        <span class="text-right text-default">{{ hoveredNode.clock_offset_ns }}</span>
        <span>Latency</span>
        <span class="text-right text-default">{{ hoveredNode.p2p_latency_us }}</span>
        <span>Loss</span>
        <span class="text-right text-default">{{ hoveredNode.packet_loss_pct }}</span>
      </div>
    </div>
  </div>
</template>
