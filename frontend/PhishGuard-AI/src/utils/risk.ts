import type { MessageStatus } from '@/services/userDashboard.service'

/** One visual language for risk everywhere in the app (doc §17.7). */
export const STATUS_META: Record<MessageStatus, { label: string; emoji: string; chip: string; dot: string; text: string }> = {
  phishing: { label: 'Dangereux', emoji: '🔴', chip: 'bg-red-50 text-red-700 border-red-200', dot: 'bg-red-500', text: 'text-red-600' },
  suspicious: { label: 'Suspect', emoji: '🟠', chip: 'bg-amber-50 text-amber-700 border-amber-200', dot: 'bg-amber-500', text: 'text-amber-600' },
  safe: { label: 'Sans danger', emoji: '🟢', chip: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500', text: 'text-emerald-600' },
}

export const LEVEL_LABEL: Record<string, string> = {
  Critical: 'Critique', High: 'Élevé', Medium: 'Modéré', Low: 'Faible',
}

export const SIGNAL_LABEL: Record<string, string> = {
  ml: 'Modèle anti-phishing', ai: 'Analyse IA', url: 'Liens', rules: 'Règles & expéditeur',
}

export function formatDate(value: string | null | undefined) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function timeAgo(value: string | null | undefined) {
  if (!value) return ''
  const seconds = Math.round((Date.now() - new Date(value).getTime()) / 1000)
  if (seconds < 60) return "à l'instant"
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return `il y a ${minutes} min`
  const hours = Math.round(minutes / 60)
  if (hours < 24) return `il y a ${hours} h`
  const days = Math.round(hours / 24)
  return `il y a ${days} j`
}
