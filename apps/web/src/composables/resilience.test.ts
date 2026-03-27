import { describe, expect, it } from 'vitest'
import { computeRetryDelay, isRetryableStatus } from './resilience'

describe('resilience helpers', () => {
  it('computes exponential backoff with a ceiling', () => {
    expect(computeRetryDelay(0, 250, 2000)).toBe(250)
    expect(computeRetryDelay(1, 250, 2000)).toBe(500)
    expect(computeRetryDelay(3, 250, 2000)).toBe(2000)
    expect(computeRetryDelay(10, 250, 2000)).toBe(2000)
  })

  it('flags retryable http status codes', () => {
    expect(isRetryableStatus(408)).toBe(true)
    expect(isRetryableStatus(429)).toBe(true)
    expect(isRetryableStatus(500)).toBe(true)
    expect(isRetryableStatus(404)).toBe(false)
  })
})
