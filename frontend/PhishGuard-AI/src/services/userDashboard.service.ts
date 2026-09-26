import { apiFetch } from './http'

export type MessageStatus = 'phishing' | 'suspicious' | 'safe'

export interface DashboardOverview {
  protection_status: 'active' | 'degraded' | 'inactive'
  last_sync_at: string | null
  vigilance_score: number
  emails_analyzed_today: number
  safe_today: number
  suspicious_today: number
  threats_today: number
  quarantined_today: number
}

export interface DashboardMessage {
  id: number
  sender: string
  subject: string
  received_at: string | null
  status: MessageStatus
  score: number
  threat_type: string
  preview: string
  reported_at: string | null
  review_label?: string | null
  /** Where the message came from */
  origin?: 'web' | 'mailbox' | 'forward' | 'share'
}

export interface DashboardActivity {
  id: number
  type: 'threat' | 'report' | 'analysis'
  action: string
  details: string
  occurred_at: string | null
}

export interface DashboardTimelineItem {
  id: number
  time: string
  title: string
  risk: number
  action: string
  tone: 'critical' | 'high' | 'safe'
}

export interface ScoreReason {
  label: string
  delta: number
}

export interface SecurityCheck {
  mfa_active: boolean
  last_login: string | null
  account_locked: boolean
}

export const userDashboardService = {
  getOverview: () => apiFetch<DashboardOverview>('/user/dashboard/overview'),
  getRecentMessages: (limit = 20) =>
    apiFetch<{ items: DashboardMessage[]; total: number }>(`/user/dashboard/recent-messages?limit=${limit}`),
  getActivity: (limit = 10) =>
    apiFetch<{ items: DashboardActivity[] }>(`/user/dashboard/activity?limit=${limit}`),
  getTimeline: (range: string) =>
    apiFetch<{ items: DashboardTimelineItem[] }>(`/user/dashboard/timeline?range=${encodeURIComponent(range)}`),
  getScoreBreakdown: () => apiFetch<{ score: number | null; reasons: ScoreReason[] }>('/user/dashboard/score-breakdown'),
  reportMessage: (id: number) => apiFetch<{ id: number; reported_at: string }>(`/user/messages/${id}/report`, { method: 'POST' }),
  checkSecurity: () => apiFetch<SecurityCheck>('/user/dashboard/security-check', { method: 'POST' }),
}
