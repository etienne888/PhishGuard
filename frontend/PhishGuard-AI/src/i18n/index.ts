import { computed, ref } from 'vue'
import fr from './locales/fr'
import en from './locales/en'
import pcm from './locales/pcm'
import ewo from './locales/ewo'
import ff from './locales/ff'

export type Locale = 'fr' | 'en' | 'pcm' | 'ewo' | 'ff'
export type Messages = Record<string, string>
export type TranslateParams = Record<string, string | number>

export const localeOptions: Array<{ code: Locale; label: string; nativeLabel: string }> = [
  { code: 'fr', label: 'French', nativeLabel: 'Français' },
  { code: 'en', label: 'English', nativeLabel: 'English' },
  { code: 'pcm', label: 'Cameroonian Pidgin', nativeLabel: 'Pidgin Camerounais' },
  { code: 'ewo', label: 'Ewondo', nativeLabel: 'Ewondo' },
  { code: 'ff', label: 'Fulfulde', nativeLabel: 'Fulfulde' },
]

const messages: Record<Locale, Messages> = { fr, en, pcm, ewo, ff }

// Where a missing key is looked up next. Pidgin speakers read English more easily
// than French; Ewondo and Fulfulde are only partially translated and fall back to French.
const fallbacks: Record<Locale, Locale[]> = {
  fr: [],
  en: ['fr'],
  pcm: ['en', 'fr'],
  ewo: ['fr'],
  ff: ['fr'],
}

// BCP-47 tags for <html lang> and Intl formatting
const htmlLang: Record<Locale, string> = { fr: 'fr-CM', en: 'en-CM', pcm: 'en-CM', ewo: 'fr-CM', ff: 'fr-CM' }

function readSavedLocale(): Locale | null {
  try {
    const saved = window.localStorage.getItem('pg-locale') as Locale | null
    return saved && saved in messages ? saved : null
  } catch {
    return null
  }
}

const locale = ref<Locale>((typeof window !== 'undefined' && readSavedLocale()) || 'fr')

function applyHtmlLang() {
  if (typeof document !== 'undefined') document.documentElement.lang = htmlLang[locale.value]
}
applyHtmlLang()

function lookup(key: string): string | undefined {
  for (const code of [locale.value, ...fallbacks[locale.value]]) {
    const value = messages[code][key]
    if (value !== undefined) return value
  }
  return undefined
}

/** Translate `key`, replacing `{name}` placeholders with `params`. Unknown keys are returned as-is. */
export function translate(key: string, params?: TranslateParams): string {
  const value = lookup(key) ?? key
  if (!params) return value
  return value.replace(/\{(\w+)\}/g, (match, name) => (name in params ? String(params[name]) : match))
}

/**
 * Translate `key` if the current language (or its fallbacks, French excluded) has it,
 * otherwise return `fallback`. Used for content that arrives in French from the backend.
 */
export function translateOr(key: string, fallback: string): string {
  for (const code of [locale.value, ...fallbacks[locale.value]]) {
    if (code === 'fr') break
    const value = messages[code][key]
    if (value !== undefined) return value
  }
  return fallback
}

export function setLocale(next: Locale) {
  locale.value = next
  applyHtmlLang()
  try {
    window.localStorage.setItem('pg-locale', next)
  } catch {
    /* storage unavailable: the choice lasts for this visit only */
  }
}

/** Language code sent to the backend so AI explanations and indicators match the UI. */
export const apiLanguage = computed<'fr' | 'en'>(() => (locale.value === 'en' || locale.value === 'pcm' ? 'en' : 'fr'))

/** Locale tag for dates and numbers (toLocaleString, Intl). */
export const intlLocale = computed(() => htmlLang[locale.value])

export function useI18n() {
  return {
    locale,
    locales: computed(() => localeOptions),
    t: translate,
    tOr: translateOr,
    setLocale,
    intlLocale,
  }
}
