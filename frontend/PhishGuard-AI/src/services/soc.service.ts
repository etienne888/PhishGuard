/**
 * Security Operations Centre API (backend/app/api/admin_soc.py + admin_security.py):
 * system telemetry, incidents, threat intelligence, blocklist, admin security centre, triage.
 */
import { apiFetch } from './http'
import type { SecurityEvent } from './admin.service'

// ---------- System ----------
export interface SystemSnapshot {
  generated_at: string
  status: 'healthy' | 'degraded' | 'down'
  problems: string[]
  traffic: {
    window_minutes: number; requests: number; rpm: number
    error_rate: number; client_error_rate: number
    p50_ms: number | null; p95_ms: number | null
    sparkline: number[]
    top_endpoints: Array<{ endpoint: string; count: number }>
    slow_endpoints: Array<{ endpoint: string; count: number }>
  }
  host: {
    available: boolean; cpu_percent?: number; cpu_count?: number
    memory_percent?: number; memory_used_gb?: number; memory_total_gb?: number
    disk_percent?: number; disk_free_gb?: number; process_memory_mb?: number
    threads?: number; python?: string; os?: string; uptime_seconds?: number
    /** true: standard-library figures (psutil not installed) */
    partial?: boolean; error?: string
  }
  database: {
    status: 'up' | 'down'; latency_ms?: number; size_mb?: number; connections?: number
    version?: string; error?: string; tables?: Record<string, number>
  }
  engine: {
    components: { text_model: boolean; url_model: boolean; ai: boolean; smtp: boolean }
    analyses_24h: number; ai_coverage: number | null
    pipeline_p50_ms: number | null; pipeline_p95_ms: number | null; pipeline_avg_ms: number | null
    hourly: number[]
  }
  experience: {
    error?: string
    visitor_scans_7d?: number; visitor_claimed_7d?: number; conversion_rate?: number | null
    feedback_30d?: { helpful: number; not_helpful: number; helpful_rate: number | null }
    sources_7d?: Partial<Record<'web' | 'mailbox' | 'forward' | 'share', number>>
    mailboxes?: Partial<Record<'active' | 'paused' | 'error' | 'revoked', number>>
    providers?: { gmail: boolean; outlook: boolean }
    forwarding?: boolean
  }
  /** Background scheduler: last run of each job */
  jobs: Record<string, { last_run: string; ok: boolean; duration_ms?: number; error?: string; every_seconds: number }>
}

export interface TriageStats {
  mode: 'manual' | 'assisted' | 'auto'
  threshold: number
  auto_closed: number; human_closed: number; pending: number; total: number
  automation_rate: number
  engine_accuracy: number | null
  judged: number
}

export interface SocSummary {
  incidents: { open: number; critical: number; latest: Incident[] }
  triage: TriageStats
  blocked_domains: number
  pending_accounts: number
  system: {
    status: SystemSnapshot['status']; problems: string[]
    db_latency_ms: number | null; p95_ms: number | null; rpm: number; error_rate: number
    cpu: number | null; memory: number | null; pipeline_p50_ms: number | null; ai_coverage: number | null
  }
}

// ---------- Incidents ----------
export type IncidentStatus = 'open' | 'investigating' | 'contained' | 'resolved' | 'false_positive'
export type Severity = 'critical' | 'high' | 'medium' | 'low'

export interface TimelineEvent {
  at: string
  kind: 'opened' | 'linked' | 'status' | 'severity' | 'assigned' | 'note' | 'blocked' | 'escalated'
  text: string
  actor: string | null
  count?: number
}

export interface Incident {
  id: number
  ref: string
  title: string
  indicator: string | null
  indicator_type: 'domain' | 'brand' | 'sender' | null
  category: string | null
  severity: Severity
  status: IncidentStatus
  source: 'auto' | 'manual'
  analysis_ids: number[]
  messages: number
  affected_users: number
  max_score: number
  assigned_to: number | null
  assignee: string | null
  blocked: boolean
  timeline: TimelineEvent[]
  first_seen: string | null
  last_seen: string | null
  resolved_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface IncidentDetail extends Incident {
  messages_detail: Array<{ id: number; preview: string; score: number; verdict: string; user: string | null; created_at: string; urls: string[] }>
  admins: Array<{ id: number; name: string }>
}

export interface IncidentStats {
  open: number; investigating: number; contained: number; resolved_7d: number
  critical_active: number; mttr_hours: number | null
}

// ---------- Threat intelligence ----------
export interface Ioc {
  id: string
  type: 'domain' | 'url' | 'sender' | 'brand'
  value: string
  hits: number
  max_score: number
  confidence: number
  severity: 'critical' | 'high' | 'medium'
  users: number
  active: boolean
  openphish: boolean
  blocked: boolean
  country: string | null
  isp: string | null
  first_seen: string
  last_seen: string
  analysis_ids: number[]
}

export interface FeedStatus { ok: boolean; size: number; fetched_at: string | null }

export interface IntelSummary {
  days: number
  dangerous_messages: number
  brands: Array<{ name: string; count: number }>
  categories: Array<{ name: string; count: number }>
  daily: Array<{ date: string; count: number }>
  feed: FeedStatus & { name: string; sample: string[] }
}

export interface BlockedDomain {
  id: number; domain: string; reason: string | null; incident_id: number | null
  created_by: string | null; is_active: boolean; created_at: string | null
}

// ---------- Admin security centre ----------
export interface SecurityCheck { key: string; ok: boolean; weight: number; value?: number | null }

export interface SecurityOverview {
  profile: {
    id: number; email: string; full_name: string | null; phone: string | null
    email_verified: boolean; mfa_active: boolean; created_at: string | null; last_login: string | null
    avatar_url: string | null; job_title: string | null; organization: string | null; city: string | null
    password_changed_at: string | null
  }
  posture: { score: number; grade: 'A' | 'B' | 'C' | 'D'; checks: SecurityCheck[] }
  logins: SecurityEvent[]
  sudo: { active: boolean; until: number | null; minutes: number }
  platform: {
    failed_logins_24h: number; locked_accounts: number; admins: number; admins_without_mfa: number
    pending_accounts: number; warnings_24h: number
  }
}

export interface EventPage {
  items: SecurityEvent[]; total: number; page: number; per_page: number
  counters: { total_24h: number; warning_24h: number; critical_24h: number; admin_actions_24h: number }
}

export interface EventFilters { scope?: 'all' | 'auth' | 'admin' | 'registration'; severity?: string; q?: string; days?: number; page?: number }

function query(params: Record<string, string | number | undefined>) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== '') search.set(key, String(value))
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

const json = (body: unknown) => ({ body: JSON.stringify(body) })

export const socService = {
  getSystem: () => apiFetch<SystemSnapshot>('/admin/system', { silent: true }),
  getSummary: () => apiFetch<SocSummary>('/admin/soc/summary', { silent: true }),

  listIncidents: (status = 'active', severity = '') =>
    apiFetch<{ items: Incident[]; stats: IncidentStats }>(`/admin/incidents${query({ status, severity })}`),
  getIncident: (id: number) => apiFetch<IncidentDetail>(`/admin/incidents/${id}`),
  createIncident: (data: { title: string; severity: Severity; indicator?: string; description?: string }) =>
    apiFetch<Incident>('/admin/incidents', { method: 'POST', ...json(data) }),
  updateIncident: (id: number, patch: Partial<{ status: IncidentStatus; severity: Severity; assigned_to: number | null; title: string }>) =>
    apiFetch<Incident>(`/admin/incidents/${id}`, { method: 'PATCH', ...json(patch) }),
  addNote: (id: number, text: string) => apiFetch<Incident>(`/admin/incidents/${id}/notes`, { method: 'POST', ...json({ text }) }),
  blockIncident: (id: number) => apiFetch<Incident>(`/admin/incidents/${id}/block`, { method: 'POST' }),
  correlate: () => apiFetch<{ opened: number; updated: number; indicators_checked: number }>('/admin/incidents/correlate', { method: 'POST' }),

  listIocs: (days = 30) =>
    apiFetch<{ items: Ioc[]; total: number; days: number; analyses_scanned: number; feed: FeedStatus }>(
      `/admin/intel/iocs?days=${days}`, { timeoutMs: 30_000 }),
  getIntelSummary: (days = 30) => apiFetch<IntelSummary>(`/admin/intel/summary?days=${days}`, { timeoutMs: 30_000 }),
  refreshFeed: () => apiFetch<{ ok: boolean; size: number }>('/admin/intel/feed/refresh', { method: 'POST', timeoutMs: 30_000 }),

  listBlocklist: () => apiFetch<{ items: BlockedDomain[]; total: number }>('/admin/blocklist'),
  block: (domain: string, reason = '') => apiFetch<BlockedDomain>('/admin/blocklist', { method: 'POST', ...json({ domain, reason }) }),
  unblock: (id: number) => apiFetch<{ deleted: boolean }>(`/admin/blocklist/${id}`, { method: 'DELETE' }),

  getSecurityOverview: () => apiFetch<SecurityOverview>('/admin/security/overview'),
  sudo: (password: string, code?: string) =>
    apiFetch<{ active: boolean; until: string; mfa_required: boolean }>('/admin/security/sudo', { method: 'POST', silent: true, ...json({ password, code }) }),
  signOutOthers: () => apiFetch<{ ok: boolean }>('/admin/security/sign-out-others', { method: 'POST' }),
  listEvents: (filters: EventFilters = {}) =>
    apiFetch<EventPage>(`/admin/security/events${query({ ...filters, per_page: 25 })}`),
  eventsExportUrl: (filters: EventFilters = {}) => `/api/admin/security/events/export${query({ ...filters })}`,
  getAlerts: () => apiFetch<{ items: SecurityEvent[] }>('/admin/security/alerts', { silent: true }),

  getTriage: () => apiFetch<TriageStats>('/admin/triage', { silent: true }),
  runTriage: () => apiFetch<TriageStats & { processed: number; left_for_humans: number }>('/admin/triage/run', { method: 'POST' }),
}
