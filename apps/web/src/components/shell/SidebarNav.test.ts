// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import SidebarNav from './SidebarNav.vue'

describe('SidebarNav', () => {
  it('renders agent status content and supports collapsed mode', async () => {
    const wrapper = mount(SidebarNav, {
      props: {
        collapsed: false,
        items: [{ id: 'overview', label: 'Overview', icon: 'overview', active: true }],
        agentStatuses: [{ id: 'frontend', label: 'Frontend', status: 'healthy', description: '60 FPS' }],
      },
    })

    expect(wrapper.text()).toContain('Realtime service health')
    await wrapper.setProps({ collapsed: true })
    expect(wrapper.text()).not.toContain('Realtime service health')
  })
})
