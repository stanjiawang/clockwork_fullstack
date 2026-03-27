<script setup lang="ts">
import { computed, useSlots } from 'vue'

interface BaseCardProps {
  padding?: 'compact' | 'standard' | 'hero'
  tone?: 'surface' | 'elevated'
  bezel?: boolean
  minHeight?: string
}

const props = withDefaults(defineProps<BaseCardProps>(), {
  padding: 'standard',
  tone: 'surface',
  bezel: true,
  minHeight: '',
})

const slots = useSlots()

const paddingClass = computed(() => {
  switch (props.padding) {
    case 'compact':
      return 'p-4'
    case 'hero':
      return 'p-10'
    default:
      return 'p-6'
  }
})

const toneClass = computed(() => (props.tone === 'elevated' ? 'bg-elevated' : 'bg-surface'))
const hasHeader = computed(() => Boolean(slots.header))
</script>

<template>
  <section
    class="rounded-card border border-border-subtle"
    :class="toneClass"
    :style="minHeight ? { minHeight } : undefined"
  >
    <header
      v-if="hasHeader"
      class="px-6 py-4"
      :class="{ 'border-b border-border-default': bezel }"
    >
      <slot name="header" />
    </header>
    <div :class="paddingClass">
      <slot />
    </div>
  </section>
</template>
