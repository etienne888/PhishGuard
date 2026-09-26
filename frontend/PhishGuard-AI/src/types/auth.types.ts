export interface AuthUser {
  id: string
  email: string
  displayName?: string
  is_admin?: boolean
  mfa_active?: boolean
  avatar_url?: string | null
  /** false until the 3-screen welcome tour has been completed or skipped */
  onboarded?: boolean
}

export type AuthModalMode = 'login' | 'register' | 'demo' | null

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload extends LoginPayload {
  confirmPassword: string
  phone?: string
  full_name: string
  region?: string
  city?: string
  acceptTerms: boolean
  /** Hidden honeypot field: only bots fill it in */
  website?: string
  /** When the form was first shown (ms epoch): bots submit in under a second */
  form_started_at?: number
}
