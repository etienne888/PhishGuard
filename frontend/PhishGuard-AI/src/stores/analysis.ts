import { defineStore } from 'pinia'
import { ref } from 'vue'
import { analysisService } from '@/services'
import type { AnalysisResult } from '@/types'

export const useAnalysisStore = defineStore('analysis', () => {
  const currentText = ref('')
  const result = ref<AnalysisResult | null>(null)
  const isAnalyzing = ref(false)
  const error = ref<string | null>(null)

  async function analyze(text: string) {
    const trimmed = text.trim()
    if (!trimmed) {
      error.value = 'Veuillez coller un message à analyser.'
      result.value = null
      return
    }
    error.value = null
    isAnalyzing.value = true
    currentText.value = trimmed
    try {
      result.value = await analysisService.analyzeMessage(trimmed)
    } catch {
      error.value = "L'analyse a échoué. Veuillez réessayer."
    } finally {
      isAnalyzing.value = false
    }
  }

  function reset() {
    currentText.value = ''
    result.value = null
    error.value = null
  }

  async function report() {
    if (!result.value) return
    return analysisService.reportMessage(currentText.value, result.value)
  }

  return { currentText, result, isAnalyzing, error, analyze, reset, report }
})
