import { api } from './api'

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
