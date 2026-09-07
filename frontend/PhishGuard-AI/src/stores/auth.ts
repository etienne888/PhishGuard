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
    } catch (err) {
      error.value =
        err instanceof Error && err.message === 'Email verification required'
          ? 'Vérifiez votre adresse email avant de vous connecter.'
          : 'Identifiants invalides. Vérifiez votre email et mot de passe.'
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

  async function register(payload: RegisterPayload): Promise<boolean> {
    isSubmitting.value = true
    error.value = null
    try {
      await authService.register(payload)
      return true
    } catch (err) {
      const message = err instanceof Error ? err.message : ''
      error.value =
        message === 'Email already registered'
          ? 'Cette adresse email est déjà enregistrée.'
          : message === 'Unable to send verification email'
            ? "Le compte n'a pas pu être vérifié par email. Réessayez plus tard."
            : 'Impossible de créer le compte. Réessayez.'
      return false
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
