<script setup lang="ts">
import { computed } from 'vue'

interface BaseButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'subtle'
  size?: 'sm' | 'md'
  type?: 'button' | 'submit' | 'reset'
  disabled?: boolean
  loading?: boolean
  fullWidth?: boolean
  ariaLabel?: string
}

const props = withDefaults(defineProps<BaseButtonProps>(), {
  variant: 'secondary',
  size: 'md',
  type: 'button',
  disabled: false,
  loading: false,
  fullWidth: false,
  ariaLabel: undefined,
})

const className = computed(() => {
  const classes = [
    'inline-flex items-center justify-center gap-2 rounded-control border text-sm tracking-normal transition-colors duration-150 ease-industrial focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-offset-2 focus-visible:ring-offset-canvas disabled:cursor-not-allowed disabled:opacity-50',
    props.size === 'sm' ? 'min-h-8 px-3 py-2' : 'min-h-10 px-4 py-2',
  ]

  switch (props.variant) {
    case 'primary':
      classes.push('border-primary-600 bg-primary-600 text-strong hover:bg-elevated')
      break
    case 'ghost':
      classes.push('border-transparent bg-transparent text-subtle hover:bg-elevated hover:text-strong')
      break
    case 'subtle':
      classes.push('border-border-default bg-surface text-subtle hover:bg-elevated hover:text-default')
      break
    default:
      classes.push('border-border-default bg-surface text-default hover:bg-elevated')
      break
  }

  if (props.fullWidth) {
    classes.push('w-full')
  }

  return classes.join(' ')
})
</script>

<template>
  <button :aria-label="ariaLabel" :class="className" :disabled="disabled || loading" :type="type">
    <slot name="icon" />
    <span><slot /></span>
  </button>
</template>
