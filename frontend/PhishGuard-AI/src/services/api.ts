const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number | undefined>
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, ...rest } = options
  const url = new URL(`${BASE_URL}${path}`)

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) url.searchParams.set(key, String(value))
    })
  }

  const response = await fetch(url.toString(), {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...headers
    },
    ...rest
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new Error(body.message ?? body.error ?? `Request failed with status ${response.status}`)
  }

  return response.json() as Promise<T>
}

export const api = {
  get: <T>(path: string, params?: RequestOptions['params']) => request<T>(path, { method: 'GET', params }),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' })
}
