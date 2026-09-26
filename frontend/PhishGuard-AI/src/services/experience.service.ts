import { apiFetch } from './http'

export interface QuizLevel {
  key: 'novice' | 'vigilant' | 'guardian' | 'expert' | 'master'
  xp: number
  floor: number
  next: number | null
}

export interface MonthlySummary {
  month: string
  scans: number
  scans_previous_month: number
  threats_avoided: number
  suspicious: number
  safe: number
  reports: number
  top_brand: string | null
  sources: Record<string, number>
  quiz: { answered: number; correct: number; level: QuizLevel }
}

/** Monthly summary, awareness quiz progress, onboarding and privacy actions of the signed-in user. */
export const experienceService = {
  summary: () => apiFetch<MonthlySummary>('/user/summary', { silent: true }),
  answerQuiz: (correct: boolean) =>
    apiFetch<{ answered: number; correct: number; level: QuizLevel }>('/user/quiz/answer', {
      method: 'POST', body: JSON.stringify({ correct }), silent: true,
    }),
  markOnboarded: () => apiFetch<{ onboarded: boolean }>('/user/onboarded', { method: 'POST', silent: true }),
  deleteHistory: () => apiFetch<{ deleted: number }>('/user/analyses', { method: 'DELETE' }),
  deleteAnalysis: (id: number) => apiFetch<{ deleted: number }>(`/user/analyses/${id}`, { method: 'DELETE' }),
}
