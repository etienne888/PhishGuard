import { apiFetch } from './http'

export type MailProvider = 'gmail' | 'outlook'

export interface MailboxConnection {
  id: number
  provider: MailProvider
  email: string
  status: 'active' | 'paused' | 'error' | 'revoked'
  auto_label: boolean
  read_only: boolean
  scanned_count: number
  threat_count: number
  last_sync_at: string | null
  last_error: string | null
  created_at: string | null
  progress: ScanProgress
}

export interface ScanFeedItem {
  analysis_id: number
  subject: string
  sender: string
  verdict: 'phishing' | 'suspicious' | 'legitimate'
  score: number
  brand: string | null
}

/** Live state of a mailbox scan (GET /api/mailbox/<id>/progress) */
export interface ScanProgress {
  state: 'idle' | 'running' | 'done' | 'error'
  phase?: 'listing' | 'scanning' | 'done' | 'error'
  total?: number
  done?: number
  threats?: number
  current?: { subject: string; sender: string; step: 'download' | 'analyse' } | null
  feed?: ScanFeedItem[]
  started_at?: string
  finished_at?: string
  error?: string | null
}

export interface MailboxOverview {
  items: MailboxConnection[]
  /** Which providers the administrator configured (OAuth app keys in .env) */
  providers: Record<MailProvider, boolean>
  /** "Forward to PhishGuard" address, when the inbound inbox is configured */
  forward_address: string | null
}

export const mailboxService = {
  list: (silent = false) => apiFetch<MailboxOverview>('/mailbox', { silent }),
  /** Returns the provider consent URL; the browser is then sent there. */
  connect: (provider: MailProvider, label: boolean) =>
    apiFetch<{ url: string }>(`/mailbox/connect/${provider}`, { method: 'POST', body: JSON.stringify({ label }) }),
  /** Starts a background scan; follow it with progress() */
  sync: (id: number) => apiFetch<{ started: boolean; progress: ScanProgress }>(`/mailbox/${id}/sync`, { method: 'POST' }),
  progress: (id: number) =>
    apiFetch<ScanProgress & { mailbox: MailboxConnection }>(`/mailbox/${id}/progress`, { silent: true }),
  setPaused: (id: number, paused: boolean) =>
    apiFetch<MailboxConnection>(`/mailbox/${id}`, { method: 'PATCH', body: JSON.stringify({ status: paused ? 'paused' : 'active' }) }),
  disconnect: (id: number) => apiFetch<{ deleted: boolean }>(`/mailbox/${id}`, { method: 'DELETE' }),
}
