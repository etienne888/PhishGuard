export interface AuthUser {
  id: string
  email: string
  displayName?: string
  is_admin?: boolean
  mfa_active?: boolean
}

export type AuthModalMode = 'login' | 'register' | 'demo' | null

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload extends LoginPayload {
  confirmPassword: string
}
