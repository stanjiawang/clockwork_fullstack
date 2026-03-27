export function computeRetryDelay(attempt: number, baseDelayMs = 500, maxDelayMs = 5000) {
  const boundedAttempt = Math.max(0, attempt)
  const delay = baseDelayMs * 2 ** boundedAttempt
  return Math.min(delay, maxDelayMs)
}

export function createTimeoutError(operation: string, timeoutMs: number) {
  return new Error(`${operation} timed out after ${timeoutMs}ms`)
}

export function isRetryableStatus(status: number) {
  return status === 408 || status === 429 || status >= 500
}
