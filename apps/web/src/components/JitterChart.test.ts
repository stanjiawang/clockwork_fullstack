// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import JitterChart from './JitterChart.vue'

describe('JitterChart', () => {
  it('renders a visible SVG trend surface', () => {
    const wrapper = mount(JitterChart, {
      props: {
        summary: {
          health_score: 62.05,
          straggler_count: 54,
          mean_offset_ns: 12,
          p95_latency_us: 2.2,
          sync_stability_index: 0.61,
          is_stale: false,
          last_frame_age_ms: 50,
        },
      },
    })

    expect(wrapper.find('svg[aria-label="Global health trend chart"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Live health score stream')
  })
})
