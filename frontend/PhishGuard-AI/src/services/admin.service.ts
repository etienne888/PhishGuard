import { api } from './api'
import { apiFetch } from './http'
import type { AnalysisDetail } from './userAccount.service'
import type { DashboardMessage } from './userDashboard.service'

export type AdminRole = 'admin' | 'user'
export type AdminUserStatus = 'active' | 'suspended'

export interface AdminUser {
  id: number
  name: string
  email: string
  phone: string | null
  role: AdminRole
  status: AdminUserStatus
  mfa_enabled: boolean
  email_verified: boolean
  auth_provider: string
  created_at: string | null
  last_login: string | null
  locked: boolean
  threat_count: number
  analyses_count: number
}

export interface AdminStatsOverview {
  total_users: number
  active_users: number
  suspended_users: number
  admin_users: number
  mfa_enabled_users: number
  total_analyses: number
  phishing_detected: number
}

export interface PlatformSettings {
  allow_signup: boolean
  require_email_verification: boolean
  mfa_required: boolean
  session_timeout_min: number
  max_login_attempts: number
  lockout_duration_min: number
  password_min_length: number
  password_require_upper: boolean
  password_require_number: boolean
  password_require_symbol: boolean
}

// ---------- Operations (backend/app/api/admin_ops.py) ----------

export interface AdminOverview {
  analyses: {
    total: number; today: number; last_7_days: number
    phishing: number; suspicious: number; safe: number
    phishing_rate: number; anonymous_share: number
  }
  series: Array<{ date: string; phishing: number; suspicious: number; safe: number }>
  top_domains: Array<{ domain: string; count: number }>
  top_brands: Array<{ brand: string; count: number }>
  review: { pending: number; reported: number; reviewed: number }
  users: {
    total: number; new_7_days: number; suspended: number; mfa_rate: number
    recent: Array<{ id: number; email: string; name: string | null; status: string; is_admin: boolean; created_at: string | null; last_login: string | null }>
  }
  engine: {
    name: string
    components: Array<{ key: string; label: string; active: boolean; note?: string | null }>
    ai_enabled: boolean; ai_model: string; whitelist_domains: number
  }
  latest: Array<DashboardMessage & { source: string }>
}

export type ReviewView = 'pending' | 'reported' | 'borderline' | 'reviewed'
export type ReviewLabel = 'phishing' | 'safe'

export interface ReviewItem extends DashboardMessage {
  source: string
  reason: 'reported' | 'borderline'
  report_note: string | null
  review_label: ReviewLabel | null
  reviewed_at: string | null
  review_note: string | null
  reviewer: string | null
}

export type ReviewDetail = AnalysisDetail & ReviewItem

export type WhitelistCategory = 'mobile_money' | 'banking' | 'telecom' | 'government' | 'other'

export interface WhitelistEntry {
  id: number
  domain: string
  institution: string
  category: WhitelistCategory
  is_active: boolean
  created_at: string | null
}

export interface ThreatPoint {
  host: string
  count: number
  max_score: number
  status: 'phishing' | 'suspicious' | 'safe'
  last_seen: string | null
  analysis_ids: number[]
  ip?: string
  lat?: number
  lon?: number
  city?: string
  country?: string
  country_code?: string
  isp?: string
  asn?: string
}

export interface ThreatMapData {
  target: { lat: number; lon: number; label: string }
  days: number
  scope: 'threats' | 'all'
  analyses_scanned: number
  points: ThreatPoint[]
  unlocated: ThreatPoint[]
  countries: Array<{ country: string; count: number }>
  generated_at: string
}

export const adminOpsService = {
  getOverview: () => apiFetch<AdminOverview>('/admin/overview', { silent: true }),
  /** scope 'all' also maps links from safe messages; retry re-checks domains that failed to resolve. */
  getThreatMap: (days = 30, scope: 'threats' | 'all' = 'threats', retry = false) =>
    apiFetch<ThreatMapData>(`/admin/threat-map?days=${days}&scope=${scope}${retry ? '&retry=1' : ''}`, { silent: true, timeoutMs: 25_000 }),

  listReviewQueue: (view: ReviewView, page = 1) =>
    apiFetch<{ items: ReviewItem[]; total: number; page: number; per_page: number }>(
      `/admin/review-queue?view=${view}&page=${page}`),
  getReviewItem: (id: number) => apiFetch<ReviewDetail>(`/admin/review-queue/${id}`),
  decide: (id: number, label: ReviewLabel | 'reset', note?: string) =>
    apiFetch<ReviewItem>(`/admin/review-queue/${id}/decision`, { method: 'POST', body: JSON.stringify({ label, note }) }),
  exportUrl: '/api/admin/review-queue/export',

  listWhitelist: (q = '') => apiFetch<{ items: WhitelistEntry[]; total: number }>(`/admin/whitelist?q=${encodeURIComponent(q)}`),
  createWhitelist: (entry: { domain: string; institution: string; category: WhitelistCategory }) =>
    apiFetch<WhitelistEntry>('/admin/whitelist', { method: 'POST', body: JSON.stringify(entry) }),
  updateWhitelist: (id: number, patch: Partial<Pick<WhitelistEntry, 'institution' | 'category' | 'is_active'>>) =>
    apiFetch<WhitelistEntry>(`/admin/whitelist/${id}`, { method: 'PATCH', body: JSON.stringify(patch) }),
  deleteWhitelist: (id: number) => apiFetch<{ deleted: boolean }>(`/admin/whitelist/${id}`, { method: 'DELETE' }),
}

export const adminService = {
  // ---------- Users ----------
  listUsers(): Promise<{ items: AdminUser[]; total: number }> {
    return api.get('/admin/users')
  },
  getUser(id: number): Promise<AdminUser> {
    return api.get(`/admin/users/${id}`)
  },
  updateUser(id: number, patch: Partial<{ role: AdminRole; status: AdminUserStatus; name: string }>): Promise<AdminUser> {
    const { name, ...rest } = patch
    return api.patch(`/admin/users/${id}`, { ...rest, ...(name !== undefined ? { full_name: name } : {}) })
  },
  suspendUser(id: number): Promise<AdminUser> {
    return api.post(`/admin/users/${id}/suspend`)
  },
  reactivateUser(id: number): Promise<AdminUser> {
    return api.post(`/admin/users/${id}/reactivate`)
  },
  forceLogout(id: number): Promise<{ ok: boolean }> {
    return api.post(`/admin/users/${id}/force-logout`)
  },
  deleteUser(id: number): Promise<{ deleted: boolean }> {
    return api.delete(`/admin/users/${id}`)
  },

  // ---------- Stats ----------
  getStatsOverview(): Promise<AdminStatsOverview> {
    return api.get('/admin/stats/overview')
  },

  // ---------- Profile (the logged-in admin) ----------
  getProfile(): Promise<AdminUser> {
    return api.get('/admin/profile')
  },
  updateProfile(patch: { full_name?: string; phone?: string }): Promise<AdminUser> {
    return api.put('/admin/profile', patch)
  },

  // ---------- Platform settings (security policy, signup/login control) ----------
  getSettings(): Promise<PlatformSettings> {
    return api.get('/admin/settings')
  },
  updateSettings(patch: Partial<PlatformSettings>): Promise<PlatformSettings> {
    return api.put('/admin/settings', patch)
  },
}
