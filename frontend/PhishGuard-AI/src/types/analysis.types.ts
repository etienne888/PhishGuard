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
}

export interface AnalysisExample {
  id: number
  label: string
  text: string
}
