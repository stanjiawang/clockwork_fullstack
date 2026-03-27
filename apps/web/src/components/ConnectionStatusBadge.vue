<script setup lang="ts">
defineProps<{
  state: 'connecting' | 'open' | 'closed'
  lastFrameAgeMs: number
}>()
</script>

<template>
  <div class="pill w-[28ch] shrink-0 justify-start whitespace-nowrap bg-surface-soft" aria-live="polite">
    <span
      class="h-2.5 w-2.5 rounded-full"
      :class="{
        'bg-warning': state === 'connecting',
        'bg-success': state === 'open',
        'bg-danger': state === 'closed',
      }"
    />
    <span class="shrink-0 capitalize">{{ state }}</span>
    <span class="ml-1 inline-flex shrink-0 items-baseline gap-1 text-muted">
      <span class="shrink-0">frame age</span>
      <span class="inline-block min-w-[4ch] text-right tabular-nums text-fg">
        {{ lastFrameAgeMs }}
      </span>
      <span class="shrink-0">ms</span>
    </span>
  </div>
</template>
