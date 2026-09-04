import { api } from './api'
import type { AuthUser, LoginPayload, RegisterPayload } from '@/types'

interface LoginResponse {
  user?: AuthUser
  mfa_required?: boolean
}

interface RegisterResponse {
  user_id: string | number
  user?: AuthUser
}

export const authService = {
  async login(payload: LoginPayload): Promise<LoginResponse> {
    return api.post<LoginResponse>('/auth/login', payload)
  },

  async verifyMfa(code: string): Promise<AuthUser> {
    const response = await api.post<{ user: AuthUser }>('/auth/mfa/verify-login', { code })
    return response.user
  },

  async completeGoogleLogin(code: string): Promise<AuthUser> {
    const response = await api.post<{ user: AuthUser }>('/oauth/google/callback', { code })
    return response.user
  },

  async setupMfa(): Promise<{ secret: string; otpauth_uri: string }> {
    return api.post('/auth/mfa/setup')
  },

  async enableMfa(code: string): Promise<void> {
    await api.post('/auth/mfa/enable', { code })
  },

  async disableMfa(): Promise<void> {
    await api.post('/auth/mfa/disable')
  },

  async register(payload: RegisterPayload): Promise<AuthUser> {
    const response = await api.post<RegisterResponse>('/auth/register', payload)
    return response.user ?? { id: String(response.user_id), email: payload.email }
  },

  async logout(): Promise<void> {
    await api.post('/auth/logout')
  },

  async me(): Promise<AuthUser | null> {
    try {
      return await api.get<AuthUser>('/auth/me')
    } catch {
      return null
    }
  }
}
