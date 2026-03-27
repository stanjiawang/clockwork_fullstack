<script setup lang="ts">
import { Bot, Cpu, LayoutDashboard, Menu, Radar, Server } from 'lucide-vue-next'
import BaseButton from '@/components/base/BaseButton.vue'
import type { AgentStatusItem, SidebarNavItem } from '@/types/ui'

interface SidebarNavProps {
  collapsed: boolean
  items: SidebarNavItem[]
  agentStatuses: AgentStatusItem[]
}

defineProps<SidebarNavProps>()

const emit = defineEmits<{
  toggle: []
}>()

const iconMap = {
  overview: LayoutDashboard,
  fabric: Radar,
  agents: Bot,
  runtime: Server,
  telemetry: Cpu,
} as const
</script>

<template>
  <aside
    class="flex min-h-screen flex-col border-r border-border-default bg-canvas px-3 py-4 transition-[width] duration-150 ease-industrial"
    :class="collapsed ? 'w-20' : 'w-[272px]'"
  >
    <div class="mb-6 flex items-center justify-between gap-3 px-1">
      <div v-if="!collapsed">
        <p class="text-xs uppercase tracking-normal text-subtle">Clockwork</p>
        <h1 class="text-lg font-semibold tracking-tight text-strong">Industrial Console</h1>
      </div>
      <BaseButton
        :aria-label="collapsed ? 'Expand sidebar navigation' : 'Collapse sidebar navigation'"
        variant="ghost"
        size="sm"
        @click="emit('toggle')"
      >
        <template #icon>
          <Menu aria-hidden="true" class="h-4 w-4" />
        </template>
        <span v-if="!collapsed">Collapse</span>
      </BaseButton>
    </div>

    <nav aria-label="Primary" class="grid gap-2">
      <button
        v-for="item in items"
        :key="item.id"
        :aria-current="item.active ? 'page' : undefined"
        :aria-label="collapsed ? item.label : undefined"
        class="min-h-10 rounded-control border px-3 py-2 text-sm tracking-normal transition-colors duration-150 ease-industrial"
        :class="item.active ? 'border-border-default bg-surface text-strong' : 'border-transparent text-subtle hover:bg-elevated hover:text-default'"
        type="button"
      >
        <div
          :class="
            collapsed
              ? 'flex items-center justify-center'
              : 'grid grid-cols-[20px_minmax(0,1fr)_44px] items-center gap-3'
          "
        >
          <div class="flex items-center justify-center">
            <component :is="iconMap[item.icon as keyof typeof iconMap] ?? LayoutDashboard" aria-hidden="true" class="h-4 w-4 shrink-0" />
          </div>
          <span v-if="!collapsed" class="min-w-0 text-left">{{ item.label }}</span>
          <div v-if="!collapsed" class="flex justify-end">
            <span
              v-if="item.badge"
              class="inline-flex min-w-[32px] items-center justify-center rounded-utility border border-border-default px-2 py-1 text-[11px] text-subtle"
            >
              {{ item.badge }}
            </span>
          </div>
        </div>
      </button>
    </nav>

    <div class="mt-6 flex-1">
      <div
        class="rounded-card border border-border-subtle bg-surface"
        :class="collapsed ? 'mx-auto w-14 overflow-hidden px-1 py-2' : ''"
      >
        <div class="border-b border-border-default" :class="collapsed ? 'px-1 py-2' : 'px-4 py-3'">
          <p
            class="text-xs uppercase tracking-normal text-subtle"
            :class="collapsed ? 'text-center text-[9px] leading-tight [word-break:break-word]' : ''"
          >
            {{ collapsed ? 'Agents' : 'Agent status' }}
          </p>
          <h2 v-if="!collapsed" class="mt-2 text-sm font-semibold tracking-tight text-strong">Realtime service health</h2>
        </div>
        <div class="grid gap-2" :class="collapsed ? 'justify-items-center px-0 py-2' : 'p-4'">
          <div
            v-for="agent in agentStatuses"
            :key="agent.id"
            class="rounded-control border border-border-default"
            :class="collapsed ? 'flex h-10 w-10 items-center justify-center px-0 py-0' : 'px-3 py-3'"
          >
            <div class="flex items-center gap-3" :class="collapsed ? 'justify-center' : ''">
              <span
                class="rounded-full"
                :class="{
                  'h-2.5 w-2.5': true,
                  'bg-success-500': agent.status === 'healthy',
                  'bg-warning-500': agent.status === 'degraded',
                  'bg-white/30': agent.status === 'offline',
                }"
              />
              <div v-if="!collapsed" class="min-w-0">
                <p class="text-sm tracking-normal text-default">{{ agent.label }}</p>
                <p class="mt-1 text-xs leading-relaxed tracking-normal text-subtle">{{ agent.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </aside>
</template>
