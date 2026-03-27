<script setup lang="ts">
import { computed } from 'vue'
import { ArrowRightCircle } from 'lucide-vue-next'
import StatePanel from '@/components/shell/StatePanel.vue'
import type { NodeDetail } from '@clockwork/contracts'

interface NodeDetailPanelProps {
  detail: NodeDetail | null
}

const props = defineProps<NodeDetailPanelProps>()

const latestMetric = computed(() => props.detail?.recent_metrics.at(-1) ?? null)
const urgencyTone = computed(() => (props.detail?.anomaly.is_straggler ? 'text-warning-500' : 'text-default'))
</script>

<template>
  <StatePanel
    v-if="!detail"
    kind="empty"
    title="No node selected"
    message="Select a warning or critical node from the topology to lock a remediation path and inspect retained telemetry."
  />

  <div v-else class="grid gap-4">
    <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
      <p class="text-xs uppercase tracking-normal text-subtle">Recommendation</p>
      <div class="mt-3 flex items-start gap-3">
        <ArrowRightCircle aria-hidden="true" class="mt-1 h-4 w-4 text-subtle" />
        <p class="text-sm leading-relaxed tracking-normal text-default">{{ detail.anomaly.recommendation }}</p>
      </div>
    </div>

    <div class="grid gap-4 sm:grid-cols-2">
      <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
        <p class="text-xs uppercase tracking-normal text-subtle">Offset z-score</p>
        <p class="mt-3 text-3xl font-semibold tracking-tight" :class="urgencyTone">{{ detail.anomaly.offset_zscore }}</p>
      </div>
      <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
        <p class="text-xs uppercase tracking-normal text-subtle">Latency z-score</p>
        <p class="mt-3 text-3xl font-semibold tracking-tight" :class="urgencyTone">{{ detail.anomaly.latency_zscore }}</p>
      </div>
    </div>

    <div class="rounded-control border border-border-subtle bg-canvas px-4 py-4">
      <p class="text-xs uppercase tracking-normal text-subtle">Latest telemetry</p>
      <div class="mt-4 grid grid-cols-2 gap-3 text-sm leading-relaxed tracking-normal text-subtle">
        <span>Node</span>
        <span class="text-right text-default">{{ detail.node_id }}</span>
        <span>Host</span>
        <span class="text-right text-default">{{ detail.host_id }}</span>
        <span>Clock offset</span>
        <span class="text-right text-default">{{ latestMetric?.clock_offset_ns ?? '—' }}</span>
        <span>P2P latency</span>
        <span class="text-right text-default">{{ latestMetric?.p2p_latency_us ?? '—' }}</span>
        <span>Packet loss</span>
        <span class="text-right text-default">{{ latestMetric?.packet_loss_pct ?? '—' }}</span>
      </div>
    </div>
  </div>
</template>
