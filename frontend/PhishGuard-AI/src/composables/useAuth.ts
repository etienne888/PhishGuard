import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'

export function useAuth() {
    const authStore = useAuthStore()
    const { user, modalMode, isSubmitting, error } = storeToRefs(authStore)

    return {
        user,
        modalMode,
        isSubmitting,
        error,
        openModal: authStore.openModal,
        closeModal: authStore.closeModal,
        login: authStore.login,
        verifyMfa: authStore.verifyMfa,
        register: authStore.register,
        logout: authStore.logout,
    }
}
