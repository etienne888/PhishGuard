import { api } from './api'
import { ApiError, apiFetch } from './http'
import type { AnalysisResult, AnalysisIndicator, AnalysisVerdict } from '@/types'

const SUSPICIOUS_TLDS = ['.tk', '.ga', '.ml', '.cf', '.gq']
const URGENCY_WORDS = ['urgent', 'bloqué', 'immédiatement', 'expire', 'confirmer maintenant', 'dernier délai']
const MONEY_WORDS = ['mobile money', 'momo', 'compte', 'transaction', 'pin', 'code secret', 'virement']

function normalizeVerdict(verdict: unknown): AnalysisVerdict {
  const normalized = String(verdict ?? '').toLowerCase()

  if (['critical', 'high', 'phishing'].includes(normalized)) return 'phishing'
  if (['medium', 'suspicious'].includes(normalized)) return 'suspicious'
  return 'legitimate'
}

/**
 * Local heuristic fallback so the analyzer works even without the Flask
 * backend running (e.g. during frontend-only development or a static demo).
 * The real scoring lives in backend/app/ml_engine — this mirrors its shape
 * so swapping in the live API is a drop-in change.
 */
function heuristicAnalyze(text: string): AnalysisResult {
  const lower = text.toLowerCase()
  const indicators: AnalysisIndicator[] = []
  let score = 8

  const hasSuspiciousTld = SUSPICIOUS_TLDS.some((tld) => lower.includes(tld))
  const hasUrgency = URGENCY_WORDS.some((w) => lower.includes(w))
  const hasMoneyTerms = MONEY_WORDS.some((w) => lower.includes(w))
  const hasLink = /(https?:\/\/|www\.)\S+/.test(lower)
  const hasPinRequest = /\b(pin|code secret|otp)\b/.test(lower)

  if (hasSuspiciousTld) {
    score += 35
    indicators.push({ label: 'Domaine non officiel détecté', positive: false })
  }
  if (hasUrgency) {
    score += 25
    indicators.push({ label: 'Urgence artificielle détectée', positive: false })
  }
  if (hasMoneyTerms && hasLink) {
    score += 20
    indicators.push({ label: 'Lien lié à un compte financier', positive: false })
  }
  if (hasPinRequest) {
    score += 30
    indicators.push({ label: 'Demande de code confidentiel', positive: false })
  }
  if (!hasLink && !hasPinRequest) {
    indicators.push({ label: 'Aucun lien suspect', positive: true })
  }
  if (!hasUrgency) {
    indicators.push({ label: 'Ton non pressant', positive: true })
  }

  score = Math.min(Math.max(score, 4), 98)

  let verdict: AnalysisVerdict = 'legitimate'
  if (score > 65) verdict = 'phishing'
  else if (score > 35) verdict = 'suspicious'

  return {
    score,
    verdict,
    indicators,
    analyzedAt: new Date().toISOString()
  }
}

/** Shape returned by POST /api/v2/scan (see backend/app/pipeline). */
interface ScanResponse {
  score: number
  verdict: string
  level: AnalysisResult['level']
  signals: AnalysisResult['signals']
  weights: AnalysisResult['weights']
  overrides: string[]
  evidence: string[]
  recommendation: string
  ai: AnalysisResult['ai']
  analysis_id?: number
  message: { sender: string | null; subject: string | null }
}

// The AI signal can take a few seconds; the default 10 s timeout is too tight
const SCAN_TIMEOUT_MS = 30_000

function fromScan(scan: ScanResponse): AnalysisResult {
  return {
    score: Number(scan.score ?? 0),
    verdict: normalizeVerdict(scan.verdict),
    level: scan.level,
    indicators: (scan.evidence ?? []).map((label) => ({
      label,
      positive: label.startsWith('Expéditeur officiel'),
    })),
    signals: scan.signals,
    weights: scan.weights,
    overrides: scan.overrides ?? [],
    recommendation: scan.recommendation,
    ai: scan.ai,
    analysisId: scan.analysis_id,
    sender: scan.message?.sender,
    subject: scan.message?.subject,
    analyzedAt: new Date().toISOString(),
  }
}

function isUnreachable(error: unknown) {
  return error instanceof ApiError && (error.code === 'NETWORK' || error.code === 'TIMEOUT')
}

export const analysisService = {
  async analyzeMessage(text: string): Promise<AnalysisResult> {
    try {
      const scan = await apiFetch<ScanResponse>('/v2/scan', {
        method: 'POST',
        body: JSON.stringify({ text }),
        timeoutMs: SCAN_TIMEOUT_MS,
        silent: true,
      })
      return fromScan(scan)
    } catch (error) {
      // Only fall back when the backend is unreachable; real errors (e.g. a
      // too-short message) must reach the user. The UI flags offline results.
      if (isUnreachable(error)) return { ...heuristicAnalyze(text), offline: true }
      throw error
    }
  },

  async analyzeEmlFile(file: File): Promise<AnalysisResult> {
    const form = new FormData()
    form.append('file', file)
    const scan = await apiFetch<ScanResponse>('/v2/scan', {
      method: 'POST',
      body: form,
      timeoutMs: SCAN_TIMEOUT_MS,
      silent: true,
    })
    return fromScan(scan)
  },

  async reportMessage(text: string, result: AnalysisResult): Promise<{ reported: boolean }> {
    try {
      return await api.post<{ reported: boolean }>('/analysis/report', { text, result })
    } catch {
      return { reported: false }
    }
  }
}
