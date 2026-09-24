import { defineStore } from 'pinia'
import { ref } from 'vue'
import { analysisService } from '@/services'
import { ApiError } from '@/services/http'
import type { AnalysisResult } from '@/types'

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : "L'analyse a échoué. Veuillez réessayer."
}

export const useAnalysisStore = defineStore('analysis', () => {
  const currentText = ref('')
  const result = ref<AnalysisResult | null>(null)
  const isAnalyzing = ref(false)
  const error = ref<string | null>(null)

  async function run(task: () => Promise<AnalysisResult>) {
    error.value = null
    isAnalyzing.value = true
    try {
      result.value = await task()
    } catch (err) {
      result.value = null
      error.value = errorMessage(err)
    } finally {
      isAnalyzing.value = false
    }
    return result.value
  }

  async function analyze(text: string) {
    const trimmed = text.trim()
    if (!trimmed) {
      error.value = 'Veuillez coller un message à analyser.'
      result.value = null
      return null
    }
    currentText.value = trimmed
    return run(() => analysisService.analyzeMessage(trimmed))
  }

  async function analyzeFile(file: File) {
    if (!file.name.toLowerCase().endsWith('.eml')) {
      error.value = 'Seuls les fichiers .eml sont acceptés.'
      return null
    }
    currentText.value = file.name
    return run(() => analysisService.analyzeEmlFile(file))
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

  return { currentText, result, isAnalyzing, error, analyze, analyzeFile, reset, report }
})
