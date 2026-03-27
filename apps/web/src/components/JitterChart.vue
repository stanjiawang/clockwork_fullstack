<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { ClusterSummary } from '@clockwork/contracts'

interface JitterChartProps {
  summary: ClusterSummary
}

const props = defineProps<JitterChartProps>()

const history = ref<number[]>([])
const maxPoints = 180
const chartWidth = 760
const chartHeight = 256
const padding = { top: 20, right: 20, bottom: 32, left: 44 }

watch(
  () => props.summary.health_score,
  (value) => {
    const nextHistory = [...history.value]
    if (nextHistory.length === 0) {
      nextHistory.push(value)
    }
    nextHistory.push(value)
    if (nextHistory.length > maxPoints) {
      nextHistory.shift()
    }
    history.value = nextHistory
  },
  { immediate: true },
)

const chartInnerWidth = computed(() => chartWidth - padding.left - padding.right)
const chartInnerHeight = computed(() => chartHeight - padding.top - padding.bottom)

const points = computed(() =>
  history.value.map((value, index) => {
    const x = padding.left + (index / Math.max(1, maxPoints - 1)) * chartInnerWidth.value
    const y = padding.top + (1 - value / 100) * chartInnerHeight.value
    return { x, y, value }
  }),
)

const linePath = computed(() =>
  points.value
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(' '),
)

const areaPath = computed(() => {
  if (points.value.length === 0) {
    return ''
  }
  const firstPoint = points.value[0]
  const lastPoint = points.value[points.value.length - 1]
  const topPath = points.value
    .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`)
    .join(' ')

  return `${topPath} L ${lastPoint.x.toFixed(2)} ${(chartHeight - padding.bottom).toFixed(2)} L ${firstPoint.x.toFixed(2)} ${(chartHeight - padding.bottom).toFixed(2)} Z`
})

const lastPoint = computed(() => points.value[points.value.length - 1] ?? null)
const tickValues = [0, 50, 100]
</script>

<template>
  <svg
    :viewBox="`0 0 ${chartWidth} ${chartHeight}`"
    class="block h-64 w-full rounded-control border border-border-subtle bg-surface"
    preserveAspectRatio="none"
    role="img"
    aria-label="Global health trend chart"
  >
    <rect x="0" y="0" :width="chartWidth" :height="chartHeight" fill="rgba(14, 20, 31, 0.88)" />

    <g>
      <line
        :x1="padding.left"
        :y1="padding.top"
        :x2="padding.left"
        :y2="chartHeight - padding.bottom"
        stroke="rgba(255,255,255,0.10)"
      />
      <line
        :x1="padding.left"
        :y1="chartHeight - padding.bottom"
        :x2="chartWidth - padding.right"
        :y2="chartHeight - padding.bottom"
        stroke="rgba(255,255,255,0.10)"
      />

      <g v-for="tick in tickValues" :key="tick">
        <line
          :x1="padding.left"
          :y1="padding.top + (1 - tick / 100) * chartInnerHeight"
          :x2="chartWidth - padding.right"
          :y2="padding.top + (1 - tick / 100) * chartInnerHeight"
          :stroke="tick === 0 ? 'rgba(255,255,255,0.10)' : 'rgba(255,255,255,0.05)'"
        />
        <text
          :x="padding.left - 8"
          :y="padding.top + (1 - tick / 100) * chartInnerHeight + 4"
          fill="#8c98ad"
          font-size="11"
          text-anchor="end"
        >
          {{ tick }}
        </text>
      </g>
    </g>

    <path v-if="areaPath" :d="areaPath" fill="rgba(91, 140, 255, 0.18)" />
    <path
      v-if="linePath"
      :d="linePath"
      fill="none"
      stroke="#5b8cff"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="3"
    />
    <circle
      v-if="lastPoint"
      :cx="lastPoint.x"
      :cy="lastPoint.y"
      r="4.5"
      fill="#f8fbff"
      stroke="#5b8cff"
      stroke-width="2"
    />

    <text :x="padding.left" :y="chartHeight - 10" fill="#8c98ad" font-size="11">Older</text>
    <text :x="chartWidth / 2" :y="chartHeight - 10" fill="#8c98ad" font-size="11" text-anchor="middle">
      Live health score stream
    </text>
    <text :x="chartWidth - padding.right" :y="chartHeight - 10" fill="#8c98ad" font-size="11" text-anchor="end">
      Now
    </text>
  </svg>
</template>
