import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useClusterStore } from './useClusterStore'

describe('useClusterStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('applies changed nodes from the latest frame', () => {
    const store = useClusterStore()

    store.applyFrame({
      timestamp_ms: 1710000000000,
      cluster: {
        health_score: 95,
        straggler_count: 1,
        mean_offset_ns: 150,
        p95_latency_us: 3.2,
        sync_stability_index: 0.94,
        is_stale: false,
        last_frame_age_ms: 80,
      },
      changed_nodes: [
        {
          node_id: 'gpu-00-00',
          clock_offset_ns: 220,
          p2p_latency_us: 3.6,
          packet_loss_pct: 0.1,
          severity: 'warn',
          is_straggler: true,
        },
      ],
      straggler_ids: ['gpu-00-00'],
    })

    expect(store.nodeList).toHaveLength(1)
    expect(store.nodeList[0]).toMatchObject({
      node_id: 'gpu-00-00',
      severity: 'warn',
      is_straggler: true,
    })
  })

  it('tracks fps and dropped frame diagnostics separately', () => {
    const store = useClusterStore()

    store.setDiagnostics(57, 3)
    store.setDroppedFrames(7)

    expect(store.diagnostics).toMatchObject({
      fps: 57,
      droppedFrames: 7,
    })
  })
})
