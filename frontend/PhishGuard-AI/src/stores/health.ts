import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { healthService, type HealthStatus } from '@/services/health.service'
import { translate } from '@/i18n'

const CACHE_DURATION_MS = 30_000

export const useHealthStore = defineStore('health', () => {
  const status = ref<HealthStatus | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastFetched = ref<number | null>(null)

  const tone = computed<'green' | 'amber' | 'red'>(() => {
    if (error.value || status.value?.status === 'unhealthy') return 'red'
    if (!status.value || status.value.status === 'degraded') return 'amber'
    return 'green'
  })

  async function refresh(force = false) {
    const isFresh = lastFetched.value !== null && Date.now() - lastFetched.value < CACHE_DURATION_MS
    if (isLoading.value || (!force && isFresh)) return

    isLoading.value = true
    error.value = null
    try {
      status.value = await healthService.getStatus()
      lastFetched.value = Date.now()
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : translate('errors.healthUnavailable')
    } finally {
      isLoading.value = false
    }
  }

  return { status, isLoading, error, lastFetched, tone, refresh }
})
