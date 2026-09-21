import { ref, type Ref } from 'vue'

export function useAsyncData<T>(loader: () => Promise<T>) {
  const data: Ref<T | null> = ref(null) as Ref<T | null>
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  async function run() {
    isLoading.value = true
    error.value = null
    try {
      data.value = await loader()
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : 'Une erreur est survenue.'
    } finally {
      isLoading.value = false
    }
  }

  return { data, isLoading, error, run }
}
