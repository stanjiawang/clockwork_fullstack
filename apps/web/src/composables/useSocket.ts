import { onBeforeUnmount, shallowRef } from 'vue'
import type { ClusterFrame } from '@clockwork/contracts'
import { computeRetryDelay } from './resilience'

const DEFAULT_STREAM_URL =
  typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/stream`
    : 'ws://localhost:8000/api/stream'
const STREAM_URL = import.meta.env.VITE_BFF_STREAM_URL ?? DEFAULT_STREAM_URL
const STALE_STREAM_TIMEOUT_MS = 3000
const MAX_CONSECUTIVE_FAILURES = 5
const CIRCUIT_BREAKER_COOLDOWN_MS = 15000

export function useSocket() {
  const latestFrame = shallowRef<ClusterFrame | null>(null)
  const connectionState = shallowRef<'connecting' | 'open' | 'closed'>('connecting')
  const lastFrameAgeMs = shallowRef(0)
  const droppedFrames = shallowRef(0)

  let socket: WebSocket | null = null
  let reconnectDelay = 500
  let lastFrameTimestamp = 0
  let reconnectTimer: number | undefined
  let staleTimer: number | undefined
  let circuitBreakerUntil = 0
  let consecutiveFailures = 0
  let active = true

  const clearTimers = () => {
    if (reconnectTimer !== undefined) {
      window.clearTimeout(reconnectTimer)
      reconnectTimer = undefined
    }
    if (staleTimer !== undefined) {
      window.clearTimeout(staleTimer)
      staleTimer = undefined
    }
  }

  const scheduleStaleCheck = () => {
    if (staleTimer !== undefined) {
      window.clearTimeout(staleTimer)
    }
    staleTimer = window.setTimeout(() => {
      if (!active || connectionState.value !== 'open') {
        return
      }
      const age = Date.now() - lastFrameTimestamp
      if (age >= STALE_STREAM_TIMEOUT_MS) {
        connectionState.value = 'closed'
        socket?.close()
      } else {
        scheduleStaleCheck()
      }
    }, STALE_STREAM_TIMEOUT_MS)
  }

  const connect = () => {
    if (!active) {
      return
    }
    if (Date.now() < circuitBreakerUntil) {
      connectionState.value = 'closed'
      reconnectTimer = window.setTimeout(connect, circuitBreakerUntil - Date.now())
      return
    }
    connectionState.value = 'connecting'
    socket = new WebSocket(STREAM_URL)

    socket.addEventListener('open', () => {
      connectionState.value = 'open'
      reconnectDelay = 500
      consecutiveFailures = 0
      lastFrameTimestamp = Date.now()
      scheduleStaleCheck()
    })

    socket.addEventListener('message', (event) => {
      try {
        latestFrame.value = JSON.parse(event.data) as ClusterFrame
        lastFrameTimestamp = Date.now()
        scheduleStaleCheck()
      } catch {
        droppedFrames.value += 1
      }
    })

    socket.addEventListener('error', () => {
      connectionState.value = 'closed'
    })

    socket.addEventListener('close', () => {
      if (!active) {
        return
      }
      connectionState.value = 'closed'
      clearTimers()
      consecutiveFailures += 1
      if (consecutiveFailures >= MAX_CONSECUTIVE_FAILURES) {
        circuitBreakerUntil = Date.now() + CIRCUIT_BREAKER_COOLDOWN_MS
        reconnectDelay = 500
        reconnectTimer = window.setTimeout(connect, CIRCUIT_BREAKER_COOLDOWN_MS)
        consecutiveFailures = 0
        return
      }
      reconnectTimer = window.setTimeout(connect, reconnectDelay)
      reconnectDelay = computeRetryDelay(consecutiveFailures, 500, 5000)
    })
  }

  const tick = () => {
    if (lastFrameTimestamp > 0) {
      lastFrameAgeMs.value = Date.now() - lastFrameTimestamp
    } else {
      lastFrameAgeMs.value = 0
    }
  }

  connect()

  onBeforeUnmount(() => {
    active = false
    clearTimers()
    socket?.close()
  })

  return {
    latestFrame,
    connectionState,
    lastFrameAgeMs,
    droppedFrames,
    tick,
  }
}
