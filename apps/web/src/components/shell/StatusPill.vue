<script setup lang="ts">
import { computed } from 'vue'

interface StatusPillProps {
  label: string
  value: string
  status?: 'healthy' | 'degraded' | 'offline' | 'neutral'
}

const props = withDefaults(defineProps<StatusPillProps>(), {
  status: 'neutral',
})

const toneClass = computed(() => {
  switch (props.status) {
    case 'healthy':
      return 'border-success-500 bg-success-500/10 text-success-500'
    case 'degraded':
      return 'border-warning-500 bg-warning-500/10 text-warning-500'
    case 'offline':
      return 'border-border-default bg-surface text-subtle'
    default:
      return 'border-border-default bg-surface text-subtle'
  }
})
</script>

<template>
  <div
    class="inline-flex min-h-8 min-w-[136px] items-center justify-between gap-3 rounded-utility border px-3 py-2 text-xs tracking-normal"
    :class="toneClass"
  >
    <span class="shrink-0 uppercase text-[11px] text-subtle">{{ label }}</span>
    <span class="min-w-[48px] text-right tabular-nums text-default">{{ value }}</span>
  </div>
</template>
