<script setup lang="ts">
import { ChevronDown, Check } from 'lucide-vue-next'
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

interface SelectOption {
  label: string
  value: string
}

interface BaseSelectProps {
  modelValue: string
  options: SelectOption[]
  placeholder?: string
  ariaLabel?: string
}

const props = withDefaults(defineProps<BaseSelectProps>(), {
  placeholder: 'Select…',
  ariaLabel: 'Select option',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const rootRef = ref<HTMLElement | null>(null)
const isOpen = ref(false)
const highlightedIndex = ref(0)
const menuPlacement = ref<'top' | 'bottom'>('bottom')
const menuMaxHeight = ref(320)

const selectedOption = computed(
  () => props.options.find((option) => option.value === props.modelValue) ?? null,
)

const menuStyle = computed(() => {
  if (menuPlacement.value === 'top') {
    return {
      bottom: 'calc(100% + 8px)',
      maxHeight: `${menuMaxHeight.value}px`,
    }
  }

  return {
    top: 'calc(100% + 8px)',
    maxHeight: `${menuMaxHeight.value}px`,
  }
})

const updateMenuPosition = () => {
  if (!rootRef.value) {
    return
  }

  const bounds = rootRef.value.getBoundingClientRect()
  const viewportHeight = globalThis.innerHeight
  const gap = 8
  const minMenuHeight = 160
  const availableBelow = Math.max(120, viewportHeight - bounds.bottom - gap - 16)
  const availableAbove = Math.max(120, bounds.top - gap - 16)

  if (availableBelow < minMenuHeight && availableAbove > availableBelow) {
    menuPlacement.value = 'top'
    menuMaxHeight.value = Math.min(320, availableAbove)
    return
  }

  menuPlacement.value = 'bottom'
  menuMaxHeight.value = Math.min(320, availableBelow)
}

const openMenu = () => {
  isOpen.value = true
  highlightedIndex.value = Math.max(
    0,
    props.options.findIndex((option) => option.value === props.modelValue),
  )
  nextTick(() => {
    updateMenuPosition()
  })
}

const closeMenu = () => {
  isOpen.value = false
}

const commitSelection = (value: string) => {
  emit('update:modelValue', value)
  closeMenu()
}

const handleKeydown = (event: KeyboardEvent) => {
  if (!isOpen.value && (event.key === 'ArrowDown' || event.key === 'ArrowUp' || event.key === 'Enter' || event.key === ' ')) {
    event.preventDefault()
    openMenu()
    return
  }

  if (!isOpen.value) {
    return
  }

  if (event.key === 'ArrowDown') {
    event.preventDefault()
    highlightedIndex.value = Math.min(highlightedIndex.value + 1, props.options.length - 1)
    return
  }

  if (event.key === 'ArrowUp') {
    event.preventDefault()
    highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0)
    return
  }

  if (event.key === 'Escape') {
    event.preventDefault()
    closeMenu()
    return
  }

  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    const option = props.options[highlightedIndex.value]
    if (option) {
      commitSelection(option.value)
    }
  }
}

const handleDocumentPointerDown = (event: PointerEvent) => {
  if (!rootRef.value?.contains(event.target as Node)) {
    closeMenu()
  }
}

onMounted(() => {
  document.addEventListener('pointerdown', handleDocumentPointerDown)
  globalThis.addEventListener('resize', updateMenuPosition)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', handleDocumentPointerDown)
  globalThis.removeEventListener('resize', updateMenuPosition)
})
</script>

<template>
  <div ref="rootRef" class="relative">
    <button
      :aria-expanded="isOpen"
      :aria-label="ariaLabel"
      aria-haspopup="listbox"
      class="flex min-h-10 w-full items-center justify-between gap-3 rounded-control border border-border-default bg-surface px-3 py-2 text-sm tracking-normal text-default transition-colors duration-150 ease-industrial hover:bg-elevated focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-600 focus-visible:ring-offset-2 focus-visible:ring-offset-canvas"
      type="button"
      @click="isOpen ? closeMenu() : openMenu()"
      @keydown="handleKeydown"
    >
      <span class="truncate">{{ selectedOption?.label ?? placeholder }}</span>
      <ChevronDown aria-hidden="true" class="h-4 w-4 shrink-0 text-subtle" :class="{ 'rotate-180': isOpen }" />
    </button>

    <div
      v-if="isOpen"
      :style="menuStyle"
      class="absolute left-0 right-0 z-30 overflow-y-auto rounded-card border border-border-default bg-elevated"
      role="listbox"
    >
      <button
        v-for="(option, index) in options"
        :key="option.value"
        :aria-selected="option.value === modelValue"
        class="flex w-full items-center justify-between gap-3 border-b border-border-subtle px-4 py-3 text-left text-sm tracking-normal text-default transition-colors duration-150 ease-industrial last:border-b-0 hover:bg-surface focus:bg-surface focus:outline-none"
        :class="index === highlightedIndex ? 'bg-surface' : ''"
        type="button"
        @mouseenter="highlightedIndex = index"
        @mousedown.prevent="commitSelection(option.value)"
      >
        <span class="truncate">{{ option.label }}</span>
        <Check v-if="option.value === modelValue" aria-hidden="true" class="h-4 w-4 shrink-0 text-primary-600" />
      </button>
    </div>
  </div>
</template>
