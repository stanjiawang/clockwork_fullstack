<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  connectionState: 'connecting' | 'open' | 'closed'
  lastFrameAgeMs: number
  droppedFrames: number
  freshnessBudgetMs: number
  hasError: boolean
}>()

const runtimeState = computed(() => {
  if (props.connectionState === 'closed' || props.hasError) {
    return 'offline'
  }
  if (props.connectionState === 'connecting' || props.lastFrameAgeMs > props.freshnessBudgetMs) {
    return 'degraded'
  }
  return 'healthy'
})

const runtimeTone = computed(() => {
  switch (runtimeState.value) {
    case 'healthy':
      return 'bg-success/15 text-success border-success/20'
    case 'degraded':
      return 'bg-warning/15 text-warning border-warning/20'
    default:
      return 'bg-danger/15 text-danger border-danger/20'
  }
})

const freshnessTone = computed(() => {
  if (props.lastFrameAgeMs <= props.freshnessBudgetMs) {
    return 'text-success'
  }
  return 'text-warning'
})
</script>

<template>
  <section class="panel panel-muted" role="status" aria-live="polite" aria-label="Runtime signals">
    <div class="panel-header">
      <div>
        <div class="metric-label">Operational quality</div>
        <h2 class="section-title">Runtime posture</h2>
      </div>
    </div>
    <div class="panel-body pt-0">
      <div class="runtime-strip runtime-strip-grid">
        <span class="pill" :class="runtimeTone">
          <span class="h-2.5 w-2.5 rounded-full bg-current" />
          <span class="capitalize">{{ runtimeState }}</span>
        </span>
        <span class="pill runtime-pill-freshness">
          <span class="metric-label">Freshness budget</span>
          <span class="runtime-metric">
            <span :class="['runtime-metric-value', freshnessTone]">{{ lastFrameAgeMs }}</span>
            <span class="runtime-metric-unit">ms</span>
            <span class="runtime-metric-separator">/</span>
            <span class="runtime-metric-budget">{{ freshnessBudgetMs }}</span>
            <span class="runtime-metric-unit">ms</span>
          </span>
        </span>
        <span class="pill">
          <span class="metric-label">Dropped frames</span>
          <span class="runtime-metric">
            <span class="runtime-metric-value">{{ droppedFrames }}</span>
          </span>
        </span>
        <span class="pill">
          <span class="metric-label">Socket</span>
          <span class="capitalize">{{ connectionState }}</span>
        </span>
        <span class="pill">
          <span class="metric-label">Privacy</span>
          <span>Local-only session</span>
        </span>
        <span class="pill">
          <span class="metric-label">Accessibility</span>
          <span>Keyboard and screen-reader friendly</span>
        </span>
      </div>
    </div>
  </section>
</template>
