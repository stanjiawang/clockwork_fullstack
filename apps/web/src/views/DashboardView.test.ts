// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import DashboardView from './DashboardView.vue'

describe('DashboardView', () => {
  it('renders stable null states for selection and topology loading', () => {
    const wrapper = mount(DashboardView, {
      props: {
        summary: null,
        topology: null,
        nodes: [],
        selectedNodeId: null,
        hoveredNodeId: null,
        selectedNodeDetail: null,
        hostOptions: [],
        selectedHostId: null,
        activeSeverities: ['healthy', 'warn', 'critical'],
        matchedNodeCount: 0,
        totalNodeCount: 0,
        filterSummary: 'all hosts | all nodes | healthy, warn, critical',
        diagnostics: { fps: 0, droppedFrames: 0 },
        connectionState: 'connecting',
        lastFrameAgeMs: 0,
        freshnessBudgetMs: 750,
        scenarioName: 'baseline',
        scenarioReasonCode: 'waiting_for_first_frame',
        scenarioControlAvailable: false,
        scenarioControlMessage: 'Scenario control unavailable',
        scenarioMutationPending: false,
        isTopologyLoading: true,
        loadErrorMessage: '',
        isFreshEnough: false,
      },
    })

    expect(wrapper.text()).toContain('No node selected')
    expect(wrapper.text()).toContain('Loading topology')
  })
})
