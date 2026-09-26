import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authService } from '@/services'
import type { AuthUser, AuthModalMode, LoginPayload, RegisterPayload } from '@/types'
import { translate as t } from '@/i18n'

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
      const message = err instanceof Error ? err.message : ''
      error.value = ({
        'Email verification required': t('auth.errors.verifyFirst'),
        'Account pending approval': t('auth.errors.pendingApproval'),
        'Account under verification': t('auth.errors.underReview'),
        'Account rejected': t('auth.errors.rejected'),
        'Account locked. Try again later': t('auth.errors.locked'),
        'This account has been suspended. Contact an administrator.': t('auth.errors.suspended'),
      } as Record<string, string>)[message] ?? t('auth.errors.invalidCredentials')
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
      error.value = t('auth.errors.invalidMfa')
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
          ? t('auth.errors.emailTaken')
          : message === 'Phone number already registered'
            ? t('auth.errors.phoneTaken')
            : message === 'Unable to send verification email'
              ? t('auth.errors.emailDelivery')
              : message === 'Disposable email not allowed'
                ? t('auth.errors.disposable')
              : message === 'Full name required'
                ? t('auth.errors.fullName')
              : message.startsWith('Password must be at least')
                ? t('auth.errors.passwordLength', { n: message.match(/\d+/)?.[0] ?? 12 })
                : t('auth.errors.registerFailed')
      return false
    } finally {
      isSubmitting.value = false
    }
  }

  async function logout() {
    await authService.logout()
    user.value = null
  }

  function setUser(nextUser: AuthUser | null) {
    user.value = nextUser
  }

  return { user, modalMode, isSubmitting, error, mfaRequired, openModal, closeModal, login, verifyMfa, register, logout, setUser }
})
