export type AnalysisVerdict = 'phishing' | 'suspicious' | 'legitimate'

export interface AnalysisIndicator {
  label: string
  positive: boolean
}

export interface AnalysisResult {
  score: number
  verdict: AnalysisVerdict
  indicators: AnalysisIndicator[]
  analyzedAt: string
}

export interface AnalysisExample {
  id: number
  label: string
  text: string
}
