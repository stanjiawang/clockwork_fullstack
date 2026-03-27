// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ClusterMap from './ClusterMap.vue'

describe('ClusterMap', () => {
  it('emits hover events and renders the industrial hover context', async () => {
    const wrapper = mount(ClusterMap, {
      props: {
        topology: {
          nodes: [
            { id: 'gpu-00-00', host_id: 'host-00', group: 0 },
            { id: 'gpu-00-01', host_id: 'host-00', group: 0 },
          ],
          links: [{ source: 'gpu-00-00', target: 'gpu-00-01', kind: 'nvlink' }],
        },
        nodes: [
          {
            node_id: 'gpu-00-00',
            host_id: 'host-00',
            group: 0,
            clock_offset_ns: 12.4,
            p2p_latency_us: 2.1,
            packet_loss_pct: 0.02,
            severity: 'warn',
            is_straggler: true,
            matchesSearch: true,
            matchesHost: true,
            matchesSeverity: true,
            isVisible: true,
            isSelected: false,
            isHovered: false,
          },
          {
            node_id: 'gpu-00-01',
            host_id: 'host-00',
            group: 0,
            clock_offset_ns: 8.1,
            p2p_latency_us: 1.5,
            packet_loss_pct: 0.01,
            severity: 'healthy',
            is_straggler: false,
            matchesSearch: true,
            matchesHost: true,
            matchesSeverity: true,
            isVisible: true,
            isSelected: false,
            isHovered: false,
          },
        ],
        selectedNodeId: null,
        hoveredNodeId: null,
      },
    })

    const nodeButton = wrapper.get('[aria-label="Select gpu-00-00"]')
    await nodeButton.trigger('mouseenter')
    expect(wrapper.emitted('hover-node')?.at(0)).toEqual(['gpu-00-00'])

    await wrapper.setProps({ hoveredNodeId: 'gpu-00-00' })
    expect(wrapper.text()).toContain('Hover context')
    expect(wrapper.text()).toContain('gpu-00-00')
    expect(wrapper.text()).toContain('host-00')
  })
})
