import { apiFetch } from './http'

/** Approximate origin shown to users (no IP, no headers) - see backend email_origin.public_view */
export interface OriginPublic {
  precision: 'high' | 'medium' | 'low' | 'hidden'
  provider: string | null
  city: string | null
  region: string | null
  country: string | null
  country_code: string | null
  lat: number | null
  lon: number | null
  accuracy_km: number | null
  isp: string | null
  network_type: 'mobile' | 'fixed' | 'hosting' | 'proxy' | null
  device: string | null
  flags: string[]
  hop_count: number
}

export interface OriginHop {
  from_host?: string
  from_ip?: string
  from_rdns?: string
  by_host?: string
  protocol?: string
  time?: string | null
  delay_s?: number | null
  provider?: string | null
  is_origin?: boolean
  raw: string
}

export interface OriginGeo {
  ip: string; country?: string; country_code?: string; region?: string; city?: string; district?: string | null
  zip?: string | null; lat?: number; lon?: number; timezone?: string; isp?: string; org?: string; asn?: string | null
  as_name?: string; reverse_dns?: string | null; mobile?: boolean; proxy?: boolean; hosting?: boolean
}

/** Full origin report (admin) */
export interface OriginReport {
  hops: OriginHop[]
  hop_count: number
  provider: string | null
  provider_server?: { ip: string; host: string | null }
  sender_ip: string | null
  found_by: string | null
  device: { agent: string | null; label: string | null; scripted: boolean }
  message_id_domain: string | null
  date_header: string | null
  sender_utc_offset: string | null
  return_path: string | null
  authentication: string | null
  geo: OriginGeo | null
  blacklists: string[]
  route: Array<{ lat: number; lon: number; label?: string; kind: 'sender' | 'relay'; ip: string; isp?: string }>
  flags: string[]
  precision: OriginPublic['precision']
  accuracy_km: number | null
  network_type: OriginPublic['network_type']
  claimed_brand: string | null
}

export interface AnalysisBrief {
  id: number; subject: string | null; sender: string | null; verdict: string; score: number
  source: string; created_at: string | null
}

export interface OriginInvestigation {
  analysis: AnalysisBrief & { owner: string | null }
  origin: OriginReport | null
  pivots: { same_ip: AnalysisBrief[]; same_network: AnalysisBrief[] }
}

type Ranked = Array<{ name: string; count: number }>

export interface OriginPlace {
  id: string
  lat: number
  lon: number
  city: string | null
  district: string | null
  region: string | null
  country: string | null
  country_code: string | null
  count: number
  verdict: 'phishing' | 'suspicious' | 'legitimate'
  max_score: number
  isps: Ranked
  ips: Ranked
  flags: Ranked
  network_types: Ranked
  brands: Ranked
  accuracy_km: number | null
  analyses: AnalysisBrief[]
  first_seen: string | null
  last_seen: string | null
  routes: OriginReport['route'][]
}

export interface OriginMap {
  days: number
  scope: 'threats' | 'all'
  points: OriginPlace[]
  traced: number
  hidden: number
  hidden_by: Array<{ provider: string; count: number }>
  countries: Array<{ country: string; count: number }>
  generated_at: string
}

export interface MyOriginPoint {
  lat: number; lon: number; city: string | null; country: string | null; country_code: string | null
  count: number; isp: string | null; accuracy_km: number | null
  analyses: Array<{ id: number; subject: string | null; verdict: string; created_at: string | null }>
}

export const geoService = {
  originMap: (days = 30, scope: 'threats' | 'all' = 'threats') =>
    apiFetch<OriginMap>(`/admin/origin-map?days=${days}&scope=${scope}`, { silent: true, timeoutMs: 25_000 }),
  investigate: (analysisId: number) => apiFetch<OriginInvestigation>(`/admin/analyses/${analysisId}/origin`),
  myOrigins: (days = 90) => apiFetch<{ points: MyOriginPoint[]; hidden: number }>(`/user/origins?days=${days}`, { silent: true }),
}

/** Country code -> flag emoji ("CM" -> 🇨🇲) */
export function flag(code?: string | null) {
  if (!code || code.length !== 2) return '🌐'
  return String.fromCodePoint(...[...code.toUpperCase()].map((c) => 0x1f1a5 + c.charCodeAt(0)))
}
