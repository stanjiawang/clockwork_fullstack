<script setup lang="ts">
import { Bot, Play, Search, Sparkles } from 'lucide-vue-next'
import { computed } from 'vue'
import BaseButton from '@/components/base/BaseButton.vue'
import BaseInput from '@/components/base/BaseInput.vue'
import StatusPill from '@/components/shell/StatusPill.vue'
import type { AgentStatusItem, CommandAction } from '@/types/ui'

interface CommandBarProps {
  searchTerm: string
  searchSuggestions?: string[]
  actions: CommandAction[]
  agentStatuses: AgentStatusItem[]
  currentScenario: string
}

const props = withDefaults(defineProps<CommandBarProps>(), {
  searchSuggestions: () => [],
})

const emit = defineEmits<{
  'update:searchTerm': [value: string]
  action: [actionId: string]
}>()

const healthyAgentCount = computed(() => props.agentStatuses.filter((agent) => agent.status === 'healthy').length)

const actionIconMap = {
  auto: Sparkles,
  baseline: Play,
  'straggler-burst': Bot,
} as const
</script>

<template>
  <div class="grid gap-4 border-b border-border-default bg-canvas/90 px-6 py-4 backdrop-blur xl:grid-cols-[minmax(280px,420px)_minmax(0,1fr)_auto]">
    <BaseInput
      id="command-bar-search"
      list="command-bar-search-suggestions"
      name="command-bar-search"
      label="Search fabric telemetry"
      aria-label="Search nodes, hosts, or agent contexts"
      autocomplete="off"
      :model-value="searchTerm"
      :suggestions="searchSuggestions"
      placeholder="Search nodes, hosts, or agent contexts…"
      type="search"
      @update:model-value="emit('update:searchTerm', $event)"
    >
      <template #icon>
        <Search aria-hidden="true" class="h-4 w-4 text-subtle" />
      </template>
    </BaseInput>

    <div class="flex flex-wrap items-center gap-3">
      <StatusPill label="Context" :value="currentScenario" status="neutral" />
      <StatusPill
        label="Agents"
        :value="`${healthyAgentCount}/${agentStatuses.length} healthy`"
        :status="healthyAgentCount === agentStatuses.length ? 'healthy' : 'degraded'"
      />
      <div class="hidden h-8 w-px bg-white/10 xl:block" />
      <div class="hidden flex-wrap items-center gap-2 xl:flex">
        <div
          v-for="agent in agentStatuses"
          :key="agent.id"
          class="inline-flex items-center gap-2 rounded-utility border border-border-default px-3 py-2 text-xs tracking-normal text-subtle"
        >
          <span
            class="h-2 w-2 rounded-full"
            :class="{
              'bg-success-500': agent.status === 'healthy',
              'bg-warning-500': agent.status === 'degraded',
              'bg-white/30': agent.status === 'offline',
            }"
          />
          <span>{{ agent.label }}</span>
        </div>
      </div>
    </div>

    <div class="flex flex-wrap items-center justify-start gap-2 xl:justify-end">
      <BaseButton
        v-for="action in actions"
        :key="action.id"
        :disabled="action.disabled"
        :variant="action.intent === 'primary' ? 'primary' : action.intent === 'ghost' ? 'ghost' : 'secondary'"
        size="sm"
        @click="emit('action', action.id)"
      >
        <template #icon>
          <component :is="actionIconMap[action.id as keyof typeof actionIconMap] ?? Sparkles" aria-hidden="true" class="h-4 w-4" />
        </template>
        {{ action.label }}
      </BaseButton>
    </div>
  </div>
</template>
