<script setup lang="ts">
import { computed, ref } from 'vue'

interface BaseInputProps {
  modelValue: string
  placeholder?: string
  type?: 'text' | 'search'
  disabled?: boolean
  id?: string
  name?: string
  label?: string
  ariaLabel?: string
  autocomplete?: string
  list?: string
  suggestions?: string[]
}

const props = withDefaults(defineProps<BaseInputProps>(), {
  placeholder: '',
  type: 'text',
  disabled: false,
  id: undefined,
  name: undefined,
  label: undefined,
  ariaLabel: undefined,
  autocomplete: 'off',
  list: undefined,
  suggestions: () => [],
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const isFocused = ref(false)
const highlightedIndex = ref(0)

const filteredSuggestions = computed(() => {
  const query = props.modelValue.trim().toLowerCase()
  const values = query.length === 0
    ? props.suggestions
    : props.suggestions.filter((suggestion) => suggestion.toLowerCase().includes(query))
  return values.slice(0, 8)
})

const showSuggestions = computed(() => isFocused.value && filteredSuggestions.value.length > 0)

const commitSuggestion = (value: string) => {
  emit('update:modelValue', value)
  highlightedIndex.value = 0
}

const handleBlur = () => {
  globalThis.setTimeout(() => {
    isFocused.value = false
    highlightedIndex.value = 0
  }, 100)
}

const handleInput = (event: Event) => {
  emit('update:modelValue', (event.target as HTMLInputElement).value)
  highlightedIndex.value = 0
}

const handleKeydown = (event: KeyboardEvent) => {
  if (!showSuggestions.value) {
    return
  }

  if (event.key === 'ArrowDown') {
    event.preventDefault()
    highlightedIndex.value = Math.min(highlightedIndex.value + 1, filteredSuggestions.value.length - 1)
    return
  }

  if (event.key === 'ArrowUp') {
    event.preventDefault()
    highlightedIndex.value = Math.max(highlightedIndex.value - 1, 0)
    return
  }

  if (event.key === 'Enter') {
    const suggestion = filteredSuggestions.value[highlightedIndex.value]
    if (suggestion) {
      event.preventDefault()
      commitSuggestion(suggestion)
    }
    return
  }

  if (event.key === 'Escape') {
    highlightedIndex.value = 0
    isFocused.value = false
  }
}
</script>

<template>
  <div class="relative">
    <div class="flex min-h-10 items-center gap-3 rounded-control border border-border-default bg-surface px-3 py-2 transition-colors duration-150 ease-industrial hover:bg-elevated focus-within:ring-2 focus-within:ring-primary-600 focus-within:ring-offset-2 focus-within:ring-offset-canvas">
      <slot name="icon" />
      <input
        :id="id"
        :name="name"
        :aria-expanded="showSuggestions"
        :aria-label="ariaLabel ?? label"
        aria-autocomplete="list"
        :aria-controls="list"
        :autocomplete="autocomplete"
        :disabled="disabled"
        :placeholder="placeholder"
        :type="type"
        :value="modelValue"
        class="w-full bg-transparent text-sm tracking-normal text-default outline-none placeholder:text-subtle"
        @focus="isFocused = true"
        @blur="handleBlur"
        @keydown="handleKeydown"
        @input="handleInput"
      />
    </div>

    <div
      v-if="showSuggestions"
      :id="list"
      class="absolute left-0 right-0 top-[calc(100%+8px)] z-30 overflow-hidden rounded-card border border-border-default bg-elevated"
      role="listbox"
    >
      <button
        v-for="(suggestion, index) in filteredSuggestions"
        :key="suggestion"
        :aria-selected="index === highlightedIndex"
        class="flex w-full items-center justify-start border-b border-border-subtle px-4 py-3 text-left text-sm tracking-normal text-default transition-colors duration-150 ease-industrial last:border-b-0 hover:bg-surface focus:bg-surface focus:outline-none"
        :class="index === highlightedIndex ? 'bg-surface' : ''"
        type="button"
        @mousedown.prevent="commitSuggestion(suggestion)"
        @mouseenter="highlightedIndex = index"
      >
        {{ suggestion }}
      </button>
    </div>
  </div>
</template>
