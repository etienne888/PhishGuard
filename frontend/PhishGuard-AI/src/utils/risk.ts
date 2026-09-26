import type { MessageStatus } from '@/services/userDashboard.service'
import { intlLocale, translate } from '@/i18n'

type StatusMeta = { label: string; emoji: string; chip: string; dot: string; text: string }

function status(key: MessageStatus, meta: Omit<StatusMeta, 'label'>): StatusMeta {
  // Getter so the label follows the current language when read during render
  return Object.defineProperty({ ...meta } as StatusMeta, 'label', {
    get: () => translate(`status.${key}`),
    enumerable: true,
  })
}

/** One visual language for risk everywhere in the app (doc §17.7). */
export const STATUS_META: Record<MessageStatus, StatusMeta> = {
  phishing: status('phishing', { emoji: '🔴', chip: 'bg-red-50 text-red-700 border-red-200', dot: 'bg-red-500', text: 'text-red-600' }),
  suspicious: status('suspicious', { emoji: '🟠', chip: 'bg-amber-50 text-amber-700 border-amber-200', dot: 'bg-amber-500', text: 'text-amber-600' }),
  safe: status('safe', { emoji: '🟢', chip: 'bg-emerald-50 text-emerald-700 border-emerald-200', dot: 'bg-emerald-500', text: 'text-emerald-600' }),
}

/** Translated labels looked up by key, e.g. LEVEL_LABEL.High or SIGNAL_LABEL.ml */
function translatedLookup(prefix: string, lower = false): Record<string, string> {
  return new Proxy({} as Record<string, string>, {
    get: (_, key) => (typeof key === 'string' ? translate(`${prefix}.${lower ? key.toLowerCase() : key}`) : undefined),
  })
}

export const LEVEL_LABEL = translatedLookup('level', true)
export const SIGNAL_LABEL = translatedLookup('analysis.signal')

export function formatDate(value: string | null | undefined) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(intlLocale.value, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function timeAgo(value: string | null | undefined) {
  if (!value) return ''
  const seconds = Math.round((Date.now() - new Date(value).getTime()) / 1000)
  if (seconds < 60) return translate('common.justNow')
  const minutes = Math.round(seconds / 60)
  if (minutes < 60) return translate('common.minutesAgo', { n: minutes })
  const hours = Math.round(minutes / 60)
  if (hours < 24) return translate('common.hoursAgo', { n: hours })
  return translate('common.daysAgo', { n: Math.round(hours / 24) })
}
