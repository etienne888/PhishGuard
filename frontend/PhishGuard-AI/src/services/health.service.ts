import { apiFetch } from './http'

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy'
  version: string
  db: 'connected' | 'unavailable'
  ml_engine: 'loaded' | 'unavailable'
  ai_provider: string
  uptime_seconds: number
}

export const healthService = {
  getStatus(): Promise<HealthStatus> {
    return apiFetch<HealthStatus>('/health', { silent: true, timeoutMs: 5_000 })
  },
}
