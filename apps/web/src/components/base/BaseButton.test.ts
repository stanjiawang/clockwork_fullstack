// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseButton from './BaseButton.vue'

describe('BaseButton', () => {
  it('renders the primary industrial control variant', () => {
    const wrapper = mount(BaseButton, {
      props: {
        variant: 'primary',
      },
      slots: {
        default: 'Trigger burst',
      },
    })

    expect(wrapper.text()).toContain('Trigger burst')
    expect(wrapper.classes()).toContain('rounded-control')
    expect(wrapper.classes()).toContain('bg-primary-600')
  })
})
