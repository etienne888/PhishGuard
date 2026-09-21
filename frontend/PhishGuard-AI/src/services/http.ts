import { useNotificationsStore } from '@/stores/notifications'

const DEFAULT_TIMEOUT = 10_000
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public detail?: string,
    public requestId?: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export interface ApiFetchOptions extends RequestInit {
  timeoutMs?: number
  silent?: boolean
}

interface ApiEnvelope<T> {
  data: T
  meta: {
    request_id: string
    duration_ms: number
  }
}

interface ApiErrorEnvelope {
  error?: {
    code?: string
    message?: string
    detail?: string
  }
  meta?: {
    request_id?: string
  }
}

function notifyError(error: ApiError, silent: boolean) {
  if (!silent) {
    useNotificationsStore().push(error.message, 'error')
  }
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT, silent = false, ...init } = options
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  const url = new URL(`${BASE_URL}${path}`, window.location.origin)

  try {
    const response = await fetch(url, {
      ...init,
      credentials: 'include',
      headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) },
      signal: controller.signal,
    })
    const body = (await response.json().catch(() => ({}))) as ApiEnvelope<T> & ApiErrorEnvelope

    if (!response.ok) {
      const apiError = new ApiError(
        body.error?.code ?? 'UNKNOWN',
        body.error?.message ?? `HTTP ${response.status}`,
        body.error?.detail,
        body.meta?.request_id,
      )
      notifyError(apiError, silent)
      throw apiError
    }

    return body.data
  } catch (error) {
    if (error instanceof ApiError) throw error
    const apiError = error instanceof DOMException && error.name === 'AbortError'
      ? new ApiError('TIMEOUT', 'Délai dépassé')
      : new ApiError('NETWORK', 'Erreur réseau')
    notifyError(apiError, silent)
    throw apiError
  } finally {
    window.clearTimeout(timer)
  }
}
