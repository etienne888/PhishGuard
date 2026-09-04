import { api } from './api'
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

export const analysisService = {
  async analyzeMessage(text: string): Promise<AnalysisResult> {
    try {
      const result = await api.post<AnalysisResult>('/analysis/message', { text })
      return {
        ...result,
        verdict: normalizeVerdict(result?.verdict),
        score: Number(result?.score ?? 0)
      }
    } catch {
      // Backend unreachable — fall back to local heuristic so the UI stays usable.
      return heuristicAnalyze(text)
    }
  },

  async reportMessage(text: string, result: AnalysisResult): Promise<{ reported: boolean }> {
    try {
      return await api.post<{ reported: boolean }>('/analysis/report', { text, result })
    } catch {
      return { reported: false }
    }
  }
}
