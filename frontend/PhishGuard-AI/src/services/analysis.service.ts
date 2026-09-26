import { api } from './api'
import { ApiError, apiFetch } from './http'
import type { AnalysisResult, AnalysisIndicator, AnalysisVerdict, AnalysisUrl, GatedScan, OfficialContact } from '@/types'
import { apiLanguage, translate as t } from '@/i18n'

const SUSPICIOUS_TLDS = ['.tk', '.ga', '.ml', '.cf', '.gq']
const URGENCY_WORDS = ['urgent', 'bloqué', 'immédiatement', 'expire', 'confirmer maintenant', 'dernier délai', 'blocked', 'immediately', 'suspended', 'final notice']
const MONEY_WORDS = ['mobile money', 'momo', 'compte', 'transaction', 'pin', 'code secret', 'virement', 'account', 'transfer']

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
    indicators.push({ label: t('analysis.local.unofficialDomain'), positive: false })
  }
  if (hasUrgency) {
    score += 25
    indicators.push({ label: t('analysis.local.urgency'), positive: false })
  }
  if (hasMoneyTerms && hasLink) {
    score += 20
    indicators.push({ label: t('analysis.local.financialLink'), positive: false })
  }
  if (hasPinRequest) {
    score += 30
    indicators.push({ label: t('analysis.local.pinRequest'), positive: false })
  }
  if (!hasLink && !hasPinRequest) {
    indicators.push({ label: t('analysis.local.noSuspiciousLink'), positive: true })
  }
  if (!hasUrgency) {
    indicators.push({ label: t('analysis.local.calmTone'), positive: true })
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
  /** Same length as `evidence`: true for reassuring items (e.g. an official sender) */
  evidence_positive?: boolean[]
  recommendation: string
  ai: AnalysisResult['ai']
  analysis_id?: number
  message: { sender: string | null; subject: string | null }
  urls?: AnalysisUrl[]
  brand?: string | null
  official?: OfficialContact | null
  text?: string
  feedback?: 1 | -1 | null
  duration_ms?: number
  source?: AnalysisResult['source']
  origin?: AnalysisResult['origin']
}

/** Visitor response of POST /api/v2/scan: analysed, result shown after sign-in */
interface GatedResponse {
  gated: true
  claim_token: string
  checks: number
  duration_ms?: number
  safety_tip: string
}

export type ScanOutcome = AnalysisResult | GatedScan

export function isGated(outcome: ScanOutcome | null | undefined): outcome is GatedScan {
  return !!outcome && 'gated' in outcome && outcome.gated === true
}

function fromGated(g: GatedResponse): GatedScan {
  return { gated: true, claimToken: g.claim_token, checks: g.checks, durationMs: g.duration_ms, safetyTip: g.safety_tip }
}

// The AI signal can take a few seconds; the default 10 s timeout is too tight
const SCAN_TIMEOUT_MS = 30_000

function fromScan(scan: ScanResponse): AnalysisResult {
  return {
    score: Number(scan.score ?? 0),
    verdict: normalizeVerdict(scan.verdict),
    level: scan.level,
    indicators: (scan.evidence ?? []).map((label, index) => ({
      label,
      positive: scan.evidence_positive?.[index] ?? false,
    })),
    signals: scan.signals,
    weights: scan.weights,
    overrides: scan.overrides ?? [],
    recommendation: scan.recommendation,
    ai: scan.ai,
    analysisId: scan.analysis_id,
    sender: scan.message?.sender,
    subject: scan.message?.subject,
    urls: scan.urls,
    brand: scan.brand,
    official: scan.official,
    text: scan.text,
    feedback: scan.feedback ?? null,
    durationMs: scan.duration_ms,
    source: scan.source,
    origin: scan.origin ?? null,
    analyzedAt: new Date().toISOString(),
  }
}

function fromAny(response: ScanResponse | GatedResponse): ScanOutcome {
  return 'gated' in response && response.gated ? fromGated(response) : fromScan(response as ScanResponse)
}

function isUnreachable(error: unknown) {
  return error instanceof ApiError && (error.code === 'NETWORK' || error.code === 'TIMEOUT')
}

export { isUnreachable }

export const analysisService = {
  /**
   * Visitors get a GatedScan (result revealed after sign-in). When the backend is
   * unreachable, signed-in users get a browser estimate flagged `offline`
   * (`allowEstimate`); visitors' scans are queued by the store instead.
   */
  async analyzeMessage(text: string, opts: { source?: 'web' | 'share'; allowEstimate?: boolean } = {}): Promise<ScanOutcome> {
    try {
      const scan = await apiFetch<ScanResponse | GatedResponse>('/v2/scan', {
        method: 'POST',
        body: JSON.stringify({ text, lang: apiLanguage.value, source: opts.source ?? 'web' }),
        timeoutMs: SCAN_TIMEOUT_MS,
        silent: true,
      })
      return fromAny(scan)
    } catch (error) {
      // Only fall back when the backend is unreachable; real errors (e.g. a
      // too-short message) must reach the user. The UI flags offline results.
      if (opts.allowEstimate && isUnreachable(error)) return { ...heuristicAnalyze(text), offline: true, text }
      throw error
    }
  },

  async analyzeEmlFile(file: File): Promise<ScanOutcome> {
    const form = new FormData()
    form.append('file', file)
    form.append('lang', apiLanguage.value)
    const scan = await apiFetch<ScanResponse | GatedResponse>('/v2/scan', {
      method: 'POST',
      body: form,
      timeoutMs: SCAN_TIMEOUT_MS,
      silent: true,
    })
    return fromAny(scan)
  },

  /** After sign-in: attach a visitor scan to the account and get its result */
  async claim(token: string): Promise<AnalysisResult> {
    return fromScan(await apiFetch<ScanResponse>('/v2/scan/claim', {
      method: 'POST', body: JSON.stringify({ claim_token: token }), silent: true,
    }))
  },

  async getResult(id: number): Promise<AnalysisResult> {
    return fromScan(await apiFetch<ScanResponse>(`/v2/scan/${id}`, { silent: true }))
  },

  async sendFeedback(id: number, value: 1 | -1, note?: string) {
    return apiFetch<{ id: number; feedback: number }>(`/v2/scan/${id}/feedback`, {
      method: 'POST', body: JSON.stringify({ value, note }),
    })
  },

  async reportMessage(text: string, result: AnalysisResult): Promise<{ reported: boolean }> {
    try {
      return await api.post<{ reported: boolean }>('/analysis/report', { text, result })
    } catch {
      return { reported: false }
    }
  }
}
