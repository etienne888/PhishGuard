import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authService } from '@/services'
import type { AuthUser, AuthModalMode, LoginPayload, RegisterPayload } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const modalMode = ref<AuthModalMode>(null)
  const isSubmitting = ref(false)
  const error = ref<string | null>(null)
  const mfaRequired = ref(false)

  function openModal(mode: AuthModalMode) {
    error.value = null
    mfaRequired.value = false
    modalMode.value = mode
  }

  function closeModal() {
    modalMode.value = null
  }

  async function login(payload: LoginPayload) {
    isSubmitting.value = true
    error.value = null
    try {
      const result = await authService.login(payload)
      if (result.mfa_required) {
        mfaRequired.value = true
        return
      }
      if (!result.user) throw new Error('Login response did not include a user')
      user.value = result.user
      closeModal()
    } catch {
      error.value = 'Identifiants invalides. Vérifiez votre email et mot de passe.'
    } finally {
      isSubmitting.value = false
    }
  }

  async function verifyMfa(code: string) {
    isSubmitting.value = true
    error.value = null
    try {
      user.value = await authService.verifyMfa(code)
      mfaRequired.value = false
      closeModal()
    } catch {
      error.value = 'Code authenticator invalide.'
    } finally {
      isSubmitting.value = false
    }
  }

  async function register(payload: RegisterPayload) {
    isSubmitting.value = true
    error.value = null
    try {
      user.value = await authService.register(payload)
    } catch {
      error.value = 'Impossible de créer le compte. Réessayez.'
    } finally {
      isSubmitting.value = false
    }
  }

  async function logout() {
    await authService.logout()
    user.value = null
  }

  return { user, modalMode, isSubmitting, error, mfaRequired, openModal, closeModal, login, verifyMfa, register, logout }
})
