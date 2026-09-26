import type { AnalysisUrl } from '@/types'

/**
 * Split a message into plain text and highlighted parts: links (dangerous,
 * unknown or official), requests for secrets, pressure words, money bait and
 * phone numbers. Used by HighlightedMessage.vue.
 */
export type MarkKind = 'danger-link' | 'link' | 'official-link' | 'secret' | 'urgency' | 'money' | 'phone'

export interface Segment {
  text: string
  kind?: MarkKind
}

const PATTERNS: Array<{ kind: MarkKind | 'url'; re: RegExp }> = [
  { kind: 'url', re: /\b(?:https?:\/\/|www\.)[^\s<>"'()]+|(?<![@\w.-])[a-z0-9][a-z0-9-]*(?:\.[a-z0-9-]+)*\.(?:tk|ml|ga|cf|gq|xyz|top|click|online|site|link|info|live|cm|com|net|org|me|ly|co)\b(?:\/[^\s<>"'()]*)?/gi },
  { kind: 'secret', re: /\b(?:code\s+(?:secret|pin|otp|de\s+(?:confirmation|validation|retrait|s[ée]curit[ée]))|mot\s+de\s+passe|password|pin|otp|cvv|secret\s+code|verification\s+code|num[ée]ro\s+de\s+(?:carte|compte)|card\s+number)\b/gi },
  { kind: 'urgency', re: /\b(?:urgent(?:e|ly)?|imm[ée]diatement|immediately|dernier\s+(?:d[ée]lai|avertissement)|final\s+(?:notice|warning)|expir(?:e|era|é|ed|es)|bloqu[ée]e?s?|suspendue?s?|suspended|blocked|d[ée]sactiv[ée]e?|deactivated|sous\s+24\s*h|within\s+24\s*h(?:ours)?|24\s*h(?:eures)?|dans\s+l'heure|aujourd'hui\s+seulement|today\s+only|act\s+now|agissez\s+maintenant)\b/gi },
  { kind: 'money', re: /\b\d[\d\s.,]*\s?(?:fcfa|f\s?cfa|xaf|frs?)\b|\b(?:gagn[ée]e?s?|gagnant|winner|won|prize|loterie|lottery|jackpot|bonus|cadeau|gift|remboursement|refund|h[ée]ritage|inheritance)\b/gi },
  { kind: 'phone', re: /(?:\+?237[\s.-]?)?\b6\d{2}(?:[\s.-]?\d{2,3}){2,3}\b/g },
]

function classifyUrl(match: string, urls: AnalysisUrl[]): MarkKind {
  const needle = match.toLowerCase().replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0] ?? ''
  const info = urls.find((u) => {
    const host = (u.host ?? u.url).toLowerCase().replace(/^www\./, '')
    return host === needle || host.endsWith(needle) || needle.endsWith(host) || u.url.toLowerCase().includes(needle)
  })
  if (!info) return 'link'
  if (info.blocklisted || (info.score ?? 0) >= 50) return 'danger-link'
  if (info.domain?.status === 'whitelisted') return 'official-link'
  return 'link'
}

export function highlight(text: string, urls: AnalysisUrl[] = []): Segment[] {
  const marks: Array<{ start: number; end: number; kind: MarkKind }> = []
  for (const { kind, re } of PATTERNS) {
    for (const m of text.matchAll(re)) {
      if (m.index === undefined || !m[0].trim()) continue
      const value = m[0].replace(/[.,;:!?)]+$/, '')
      marks.push({ start: m.index, end: m.index + value.length, kind: kind === 'url' ? classifyUrl(value, urls) : kind })
    }
  }
  // First pattern wins on overlaps (links before words inside links)
  marks.sort((a, b) => a.start - b.start || b.end - a.end)
  const kept: typeof marks = []
  for (const mark of marks) {
    const last = kept[kept.length - 1]
    if (!last || mark.start >= last.end) kept.push(mark)
  }
  const segments: Segment[] = []
  let cursor = 0
  for (const mark of kept) {
    if (mark.start > cursor) segments.push({ text: text.slice(cursor, mark.start) })
    segments.push({ text: text.slice(mark.start, mark.end), kind: mark.kind })
    cursor = mark.end
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor) })
  return segments
}
