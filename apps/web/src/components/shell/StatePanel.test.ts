// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import StatePanel from './StatePanel.vue'

describe('StatePanel', () => {
  it('renders the dashed null state treatment', () => {
    const wrapper = mount(StatePanel, {
      props: {
        kind: 'empty',
        title: 'No data',
        message: 'Waiting for telemetry',
      },
    })

    expect(wrapper.text()).toContain('No data')
    expect(wrapper.classes()).toContain('border-dashed')
  })
})
