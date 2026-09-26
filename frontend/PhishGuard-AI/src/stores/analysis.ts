import { defineStore } from 'pinia'
import { ref } from 'vue'
import { analysisService, isGated, isUnreachable, type ScanOutcome } from '@/services/analysis.service'
import { ApiError } from '@/services/http'
import { translate as t } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import type { AnalysisResult, GatedScan } from '@/types'

function errorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : t('analysis.failed')
}

// Visitor scan waiting for sign-in, and scans typed while offline (survive reloads)
const PENDING_KEY = 'pg-pending-claim'
const QUEUE_KEY = 'pg-offline-queue'

interface PendingClaim { token: string; text: string; at: number }

function read<T>(key: string): T | null {
  try {
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}
function write(key: string, value: unknown) {
  try {
    if (value === null) localStorage.removeItem(key)
    else localStorage.setItem(key, JSON.stringify(value))
  } catch { /* storage blocked: kept in memory only */ }
}

export const useAnalysisStore = defineStore('analysis', () => {
  const currentText = ref('')
  const result = ref<AnalysisResult | null>(null)
  const gate = ref<GatedScan | null>(null)
  const queued = ref<string | null>(read<{ text: string }>(QUEUE_KEY)?.text ?? null)
  const isAnalyzing = ref(false)
  const isClaiming = ref(false)
  const error = ref<string | null>(null)

  function signedIn() {
    return !!useAuthStore().user
  }

  function accept(outcome: ScanOutcome) {
    if (isGated(outcome)) {
      gate.value = outcome
      result.value = null
      write(PENDING_KEY, { token: outcome.claimToken, text: currentText.value, at: Date.now() } satisfies PendingClaim)
    } else {
      gate.value = null
      result.value = { ...outcome, text: outcome.text ?? currentText.value }
    }
  }

  async function run(task: () => Promise<ScanOutcome>) {
    error.value = null
    isAnalyzing.value = true
    try {
      accept(await task())
    } catch (err) {
      result.value = null
      if (isUnreachable(err)) {
        // No connection: keep the message and run it when the network is back
        queue(currentText.value)
      } else {
        error.value = errorMessage(err)
      }
    } finally {
      isAnalyzing.value = false
    }
    return result.value ?? gate.value
  }

  function queue(text: string) {
    if (!text || text.endsWith('.eml')) return
    queued.value = text
    write(QUEUE_KEY, { text })
  }

  async function analyze(text: string, source: 'web' | 'share' = 'web') {
    const trimmed = text.trim()
    if (!trimmed) {
      error.value = t('analysis.emptyText')
      result.value = null
      return null
    }
    currentText.value = trimmed
    gate.value = null
    if (typeof navigator !== 'undefined' && navigator.onLine === false) {
      queue(trimmed)
      return null
    }
    return run(() => analysisService.analyzeMessage(trimmed, { source, allowEstimate: signedIn() }))
  }

  async function analyzeFile(file: File) {
    if (!file.name.toLowerCase().endsWith('.eml')) {
      error.value = t('analysis.emlOnly')
      return null
    }
    currentText.value = file.name
    return run(() => analysisService.analyzeEmlFile(file))
  }

  /** Run the scan typed while offline (called when the connection comes back). */
  async function flushQueue() {
    const text = queued.value
    if (!text || isAnalyzing.value) return null
    queued.value = null
    write(QUEUE_KEY, null)
    return analyze(text)
  }

  function cancelQueue() {
    queued.value = null
    write(QUEUE_KEY, null)
  }

  function pendingClaim(): PendingClaim | null {
    const pending = read<PendingClaim>(PENDING_KEY)
    // The server keeps the claim for 24 h
    if (pending && Date.now() - pending.at > 24 * 3600 * 1000) {
      write(PENDING_KEY, null)
      return null
    }
    return pending
  }

  /** Claim link from an email ("sign in to see the result"): kept until sign-in. */
  function rememberClaim(token: string) {
    write(PENDING_KEY, { token, text: '', at: Date.now() } satisfies PendingClaim)
  }

  /** After sign-in: reveal the visitor scan (from this browser, or a token in a link). */
  async function claim(token?: string) {
    const pending = pendingClaim()
    const claimToken = token ?? pending?.token
    if (!claimToken || isClaiming.value) return null
    isClaiming.value = true
    error.value = null
    try {
      const claimed = await analysisService.claim(claimToken)
      currentText.value = claimed.text || pending?.text || ''
      result.value = claimed
      gate.value = null
      return claimed
    } catch (err) {
      error.value = errorMessage(err)
      return null
    } finally {
      if (!token || token === pending?.token) write(PENDING_KEY, null)
      isClaiming.value = false
    }
  }

  async function open(id: number) {
    error.value = null
    isAnalyzing.value = true
    try {
      result.value = await analysisService.getResult(id)
      currentText.value = result.value.text ?? ''
      gate.value = null
    } catch (err) {
      error.value = errorMessage(err)
    } finally {
      isAnalyzing.value = false
    }
    return result.value
  }

  async function sendFeedback(value: 1 | -1, note?: string) {
    const id = result.value?.analysisId
    if (!id) return
    await analysisService.sendFeedback(id, value, note)
    if (result.value) result.value = { ...result.value, feedback: value }
  }

  function reset() {
    currentText.value = ''
    result.value = null
    gate.value = null
    error.value = null
  }

  async function report() {
    if (!result.value) return
    return analysisService.reportMessage(currentText.value, result.value)
  }

  return {
    currentText, result, gate, queued, isAnalyzing, isClaiming, error,
    analyze, analyzeFile, flushQueue, cancelQueue, pendingClaim, rememberClaim, claim, open, sendFeedback, reset, report,
  }
})
