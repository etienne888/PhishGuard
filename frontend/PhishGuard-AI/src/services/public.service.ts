import { apiFetch } from './http'

export interface CommunityAlert {
  id: number
  kind: 'domain' | 'brand' | 'sender'
  /** Brand name, or a defanged domain ("mtn-bonus[.]tk") */
  label: string
  category: string | null
  severity: 'low' | 'medium' | 'high' | 'critical'
  messages: number
  regions: string[]
  last_seen: string | null
}

export const publicService = {
  alerts: () => apiFetch<{ items: CommunityAlert[] }>('/public/alerts', { silent: true }),
}
