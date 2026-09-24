import { defineStore } from 'pinia'
import { ref } from 'vue'
import { adminOpsService, type AdminOverview } from '@/services/admin.service'

/** Live admin statistics, shared by the layout (badges, bell) and the overview page. */
export const useAdminOpsStore = defineStore('adminOps', () => {
  const overview = ref<AdminOverview | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function load() {
    isLoading.value = true
    error.value = null
    try {
      overview.value = await adminOpsService.getOverview()
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : 'Impossible de charger les statistiques.'
    } finally {
      isLoading.value = false
    }
  }

  return { overview, isLoading, error, load }
})
