import { apiFetch } from './http'
import type { AiVerdict, RiskLevel, SignalKey } from '@/types'
import type { DashboardMessage, MessageStatus } from './userDashboard.service'

export interface UserProfile {
  id: number
  email: string
  full_name: string | null
  phone: string | null
  email_verified: boolean
  mfa_active: boolean
  auth_provider: string
  created_at: string | null
  last_login: string | null
  avatar_url: string | null
}

export interface AnalysisDetail extends DashboardMessage {
  text: string
  urls: string[]
  evidence: string[]
  level: RiskLevel | null
  signals: Partial<Record<SignalKey, number | null>> | null
  weights: Partial<Record<SignalKey, number>> | null
  overrides: string[]
  ai: AiVerdict | null
  recommendation: string | null
}

export interface UserNotification {
  id: string
  analysis_id: number | null
  type: 'threat' | 'warning' | 'tip'
  title: string
  body: string
  created_at: string | null
}

export interface HistoryQuery {
  page?: number
  per_page?: number
  status?: MessageStatus | ''
  q?: string
}

function query(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') search.set(key, String(value))
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

export const userAccountService = {
  // ---------- History ----------
  listAnalyses: (params: HistoryQuery = {}) =>
    apiFetch<{ items: DashboardMessage[]; total: number; page: number; per_page: number }>(
      `/user/analyses${query({ ...params })}`),
  getAnalysis: (id: number) => apiFetch<AnalysisDetail>(`/user/analyses/${id}`),

  // ---------- Notifications ----------
  listNotifications: () => apiFetch<{ items: UserNotification[] }>('/user/notifications', { silent: true }),

  // ---------- Profile ----------
  getProfile: () => apiFetch<UserProfile>('/user/profile'),
  updateProfile: (patch: { full_name?: string; email?: string; current_password?: string }) =>
    apiFetch<UserProfile>('/user/profile', { method: 'PUT', body: JSON.stringify(patch) }),
  changePassword: (current_password: string, new_password: string) =>
    apiFetch<{ changed: boolean }>('/user/profile/password', {
      method: 'POST', body: JSON.stringify({ current_password, new_password }),
    }),
  uploadAvatar: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiFetch<UserProfile>('/user/profile/avatar', { method: 'POST', body: form })
  },
  deleteAvatar: () => apiFetch<UserProfile>('/user/profile/avatar', { method: 'DELETE' }),
}
