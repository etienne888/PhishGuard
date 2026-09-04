export function formatDate(iso: string, locale = 'fr-FR'): string {
  return new Intl.DateTimeFormat(locale, { day: '2-digit', month: 'short', year: 'numeric' }).format(new Date(iso))
}

export function formatFcfa(amount: number): string {
  return new Intl.NumberFormat('fr-FR').format(amount) + ' FCFA'
}

export function truncate(text: string, max = 120): string {
  return text.length > max ? `${text.slice(0, max).trim()}…` : text
}
