<script setup lang="ts">
import { AlertCircle, DatabaseZap, LoaderCircle } from 'lucide-vue-next'
import { computed } from 'vue'
import type { StatePanelProps } from '@/types/ui'

const props = defineProps<StatePanelProps>()

const iconComponent = computed(() => {
  switch (props.kind) {
    case 'loading':
      return LoaderCircle
    case 'error':
      return AlertCircle
    default:
      return DatabaseZap
  }
})
</script>

<template>
  <div class="flex min-h-[220px] flex-col items-center justify-center rounded-card border-2 border-dashed border-muted px-6 py-8 text-center">
    <component :is="iconComponent" class="mb-4 h-10 w-10 text-subtle/40" :class="{ 'animate-spin': kind === 'loading' }" />
    <h3 class="text-lg font-semibold tracking-tight text-strong">{{ title }}</h3>
    <p class="mt-3 max-w-md text-sm leading-relaxed tracking-normal text-subtle">{{ message }}</p>
    <p v-if="actionLabel" class="mt-4 text-xs uppercase tracking-normal text-subtle">{{ actionLabel }}</p>
  </div>
</template>
