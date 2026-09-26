export type AnalysisVerdict = 'phishing' | 'suspicious' | 'legitimate'
export type RiskLevel = 'Critical' | 'High' | 'Medium' | 'Low'
export type SignalKey = 'ml' | 'ai' | 'url' | 'rules'

export interface AnalysisIndicator {
  label: string
  positive: boolean
}

export interface AiVerdict {
  classification: 'phishing' | 'suspicious' | 'legitimate'
  category: string
  confidence: number
  reasons: string[]
  recommendation: string
}

export interface AnalysisResult {
  score: number
  verdict: AnalysisVerdict
  indicators: AnalysisIndicator[]
  analyzedAt: string
  // v2 pipeline fields (absent on the offline fallback)
  level?: RiskLevel
  signals?: Partial<Record<SignalKey, number | null>>
  weights?: Partial<Record<SignalKey, number>>
  overrides?: string[]
  recommendation?: string
  ai?: AiVerdict | null
  analysisId?: number
  sender?: string | null
  subject?: string | null
  /** True when the backend was unreachable and the browser estimated the result */
  offline?: boolean
  /** Links found in the message with their own verdict (for highlighting) */
  urls?: AnalysisUrl[]
  /** Institution the message pretends to be, and its official contact */
  brand?: string | null
  official?: OfficialContact | null
  /** Analysed text (as stored), used to highlight the dangerous parts */
  text?: string
  feedback?: 1 | -1 | null
  durationMs?: number
  source?: 'web' | 'mailbox' | 'forward' | 'share'
  /** Approximate place the email was sent from (real emails only) */
  origin?: import('@/services/geo.service').OriginPublic | null
}

export interface AnalysisUrl {
  url: string
  host?: string
  score?: number
  blocklisted?: boolean
  reasons?: string[]
  domain?: { status: string; institution?: string; imitates?: string }
}

export interface OfficialContact {
  institution: string
  domain?: string
  website?: string
  support_contact?: string | null
  logo_url?: string | null
}

/** Visitor scan: analysed on the server, result revealed after sign-in */
export interface GatedScan {
  gated: true
  claimToken: string
  checks: number
  durationMs?: number
  safetyTip: string
}

export interface AnalysisExample {
  id: number
  label: string
  text: string
}
