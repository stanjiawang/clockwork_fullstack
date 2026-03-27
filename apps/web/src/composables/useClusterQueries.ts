import { computed, type Ref } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import type {
  HealthResponse,
  NodeDetail,
  ScenarioControlRequest,
  ScenarioControlResponse,
  ScenarioStatusResponse,
  ServiceMetricsResponse,
  TopologyResponse,
} from '@clockwork/contracts'
import { computeRetryDelay, createTimeoutError, isRetryableStatus } from './resilience'

const DEFAULT_HTTP_URL =
  typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000'
const BFF_HTTP_URL = import.meta.env.VITE_BFF_HTTP_URL ?? DEFAULT_HTTP_URL
const HTTP_TIMEOUT_MS = 4000

async function fetchJson<T>(path: string): Promise<T> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), HTTP_TIMEOUT_MS)
  try {
    const response = await fetch(`${BFF_HTTP_URL}${path}`, {
    cache: 'no-store',
    credentials: 'omit',
    referrerPolicy: 'no-referrer',
    signal: controller.signal,
    })
    if (!response.ok) {
      const retryable = isRetryableStatus(response.status)
      throw new Error(
        `Request failed for ${path} with status ${response.status}${retryable ? ' (retryable)' : ''}`,
      )
    }
    return (await response.json()) as T
  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      throw createTimeoutError(path, HTTP_TIMEOUT_MS)
    }
    throw error
  } finally {
    window.clearTimeout(timeoutId)
  }
}

async function postJson<TResponse, TBody extends Record<string, unknown>>(path: string, body: TBody): Promise<TResponse> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), HTTP_TIMEOUT_MS)
  try {
    const response = await fetch(`${BFF_HTTP_URL}${path}`, {
      method: 'POST',
      cache: 'no-store',
      credentials: 'omit',
      referrerPolicy: 'no-referrer',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    })
    if (!response.ok) {
      throw new Error(`Request failed for ${path} with status ${response.status}`)
    }
    return (await response.json()) as TResponse
  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      throw createTimeoutError(path, HTTP_TIMEOUT_MS)
    }
    throw error
  } finally {
    window.clearTimeout(timeoutId)
  }
}

export function useTopologyQuery() {
  return useQuery({
    queryKey: ['topology'],
    queryFn: () => fetchJson<TopologyResponse>('/api/topology'),
    retry: (failureCount, error) => {
      if (failureCount >= 3) {
        return false
      }
      return !(error instanceof Error && error.message.includes('status 4'))
    },
    retryDelay: (attempt) => computeRetryDelay(attempt, 300, 3000),
    staleTime: Number.POSITIVE_INFINITY,
    gcTime: Number.POSITIVE_INFINITY,
  })
}

export function useHealthQuery() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => fetchJson<HealthResponse>('/api/health'),
    retry: (failureCount, error) => {
      if (failureCount >= 2) {
        return false
      }
      return !(error instanceof Error && error.message.includes('status 4'))
    },
    retryDelay: (attempt) => computeRetryDelay(attempt, 250, 2000),
    staleTime: 1_000,
    gcTime: 10_000,
  })
}

export function useMetricsQuery() {
  return useQuery({
    queryKey: ['metrics'],
    queryFn: () => fetchJson<ServiceMetricsResponse>('/api/metrics'),
    retry: (failureCount, error) => {
      if (failureCount >= 2) {
        return false
      }
      return !(error instanceof Error && error.message.includes('status 4'))
    },
    retryDelay: (attempt) => computeRetryDelay(attempt, 250, 2000),
    staleTime: 1_000,
    gcTime: 10_000,
  })
}

export function useScenarioQuery() {
  return useQuery({
    queryKey: ['scenario'],
    queryFn: () => fetchJson<ScenarioStatusResponse>('/api/scenario'),
    retry: (failureCount, error) => {
      if (failureCount >= 2) {
        return false
      }
      return !(error instanceof Error && error.message.includes('status 4'))
    },
    retryDelay: (attempt) => computeRetryDelay(attempt, 250, 2000),
    staleTime: 1_000,
    gcTime: 10_000,
  })
}

export function useNodeDetailQuery(selectedNodeId: Ref<string | null>) {
  const nodeId = computed(() => selectedNodeId.value)

  return useQuery({
    queryKey: computed(() => ['node-detail', nodeId.value]),
    queryFn: () => fetchJson<NodeDetail>(`/api/nodes/${nodeId.value}`),
    enabled: computed(() => Boolean(nodeId.value)),
    retry: (failureCount, error) => {
      if (failureCount >= 2) {
        return false
      }
      return !(error instanceof Error && error.message.includes('status 4'))
    },
    retryDelay: (attempt) => computeRetryDelay(attempt, 250, 2500),
    staleTime: 5_000,
    gcTime: 30_000,
  })
}

export function useScenarioControlMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: ScenarioControlRequest) =>
      postJson<ScenarioControlResponse, ScenarioControlRequest>('/api/scenario', request),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['scenario'] }),
        queryClient.invalidateQueries({ queryKey: ['health'] }),
        queryClient.invalidateQueries({ queryKey: ['metrics'] }),
      ])
    },
  })
}
