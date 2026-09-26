import { useNotificationsStore } from '@/stores/notifications'
import { apiLanguage, translate } from '@/i18n'

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
  // SUDO_REQUIRED opens the confirmation dialog instead of an error toast
  if (!silent && !(error.code === 'SUDO_REQUIRED' && sudoPrompt)) {
    useNotificationsStore().push(error.message, 'error')
  }
}

/**
 * Step-up authentication: sensitive admin endpoints answer SUDO_REQUIRED when the
 * admin has not re-entered their password recently. The admin layout registers a
 * prompt (SudoModal); the request is replayed once after a successful confirmation.
 */
type SudoPrompt = () => Promise<boolean>
let sudoPrompt: SudoPrompt | null = null
export function setSudoPrompt(prompt: SudoPrompt | null) {
  sudoPrompt = prompt
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  try {
    return await rawFetch<T>(path, options)
  } catch (error) {
    if (error instanceof ApiError && error.code === 'SUDO_REQUIRED' && sudoPrompt) {
      if (await sudoPrompt()) return rawFetch<T>(path, options)
    }
    throw error
  }
}

async function rawFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT, silent = false, ...init } = options
  const controller = new AbortController()
  const timer = window.setTimeout(() => controller.abort(), timeoutMs)
  const url = new URL(`${BASE_URL}${path}`, window.location.origin)

  try {
    const response = await fetch(url, {
      ...init,
      credentials: 'include',
      // FormData (file uploads) must let the browser set its own multipart boundary
      // Accept-Language lets the backend answer in the interface language
      headers: init.body instanceof FormData
        ? { 'Accept-Language': apiLanguage.value, ...(init.headers ?? {}) }
        : { 'Content-Type': 'application/json', 'Accept-Language': apiLanguage.value, ...(init.headers ?? {}) },
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
      ? new ApiError('TIMEOUT', translate('errors.timeout'))
      : new ApiError('NETWORK', translate('errors.network'))
    notifyError(apiError, silent)
    throw apiError
  } finally {
    window.clearTimeout(timer)
  }
}
