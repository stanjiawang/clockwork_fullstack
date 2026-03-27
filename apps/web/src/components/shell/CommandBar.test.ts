// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import CommandBar from './CommandBar.vue'

describe('CommandBar', () => {
  it('emits search updates and action clicks', async () => {
    const wrapper = mount(CommandBar, {
      props: {
        searchTerm: '',
        currentScenario: 'baseline',
        agentStatuses: [
          { id: 'frontend', label: 'Frontend', status: 'healthy', description: 'ok' },
          { id: 'bff', label: 'BFF', status: 'healthy', description: 'ok' },
          { id: 'backend', label: 'Simulator', status: 'healthy', description: 'ok' },
        ],
        actions: [
          { id: 'baseline', label: 'Baseline', intent: 'secondary' },
          { id: 'straggler-burst', label: 'Burst', intent: 'primary' },
        ],
      },
    })

    await wrapper.get('input').setValue('host-12')
    expect(wrapper.emitted('update:searchTerm')?.at(-1)).toEqual(['host-12'])

    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('action')?.at(0)).toEqual(['baseline'])
  })
})
