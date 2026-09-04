import { defineStore } from 'pinia'
import { ref } from 'vue'
import { threatsService } from '@/services'
import type { ThreatCategory } from '@/types'

export const useCategoriesStore = defineStore('categories', () => {
  const categories = ref<ThreatCategory[]>([])
  const activeCategoryId = ref<number | null>(null)
  const isLoading = ref(false)

  async function fetchCategories() {
    isLoading.value = true
    try {
      categories.value = await threatsService.getCategories()
    } finally {
      isLoading.value = false
    }
  }

  function selectCategory(id: number) {
    activeCategoryId.value = activeCategoryId.value === id ? null : id
  }

  function clearSelection() {
    activeCategoryId.value = null
  }

  return { categories, activeCategoryId, isLoading, fetchCategories, selectCategory, clearSelection }
})
