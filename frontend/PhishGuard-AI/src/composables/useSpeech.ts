import { onBeforeUnmount, ref } from 'vue'
import { useI18n } from '@/i18n'

/**
 * Read a text aloud with the browser's speech engine (no network, no cost).
 * Pidgin is read with an English voice; Ewondo and Fulfulde have no voices
 * available, so their users hear the French version (see the UI hint).
 */
const VOICE_LANG: Record<string, string> = { fr: 'fr', en: 'en', pcm: 'en', ewo: 'fr', ff: 'fr' }

export function useSpeech() {
  const { locale } = useI18n()
  const speaking = ref(false)
  const supported = typeof window !== 'undefined' && 'speechSynthesis' in window

  function pickVoice(lang: string) {
    const voices = window.speechSynthesis.getVoices()
    return voices.find((v) => v.lang.toLowerCase().startsWith(lang) && /natural|google|microsoft/i.test(v.name))
      ?? voices.find((v) => v.lang.toLowerCase().startsWith(lang))
  }

  function stop() {
    if (!supported) return
    window.speechSynthesis.cancel()
    speaking.value = false
  }

  function speak(text: string) {
    if (!supported || !text) return
    stop()
    const lang = VOICE_LANG[locale.value] ?? 'fr'
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = lang === 'fr' ? 'fr-FR' : 'en-GB'
    const voice = pickVoice(lang)
    if (voice) utterance.voice = voice
    utterance.rate = 0.95
    utterance.onend = () => (speaking.value = false)
    utterance.onerror = () => (speaking.value = false)
    speaking.value = true
    window.speechSynthesis.speak(utterance)
  }

  function toggle(text: string) {
    if (speaking.value) stop()
    else speak(text)
  }

  onBeforeUnmount(stop)
  return { supported, speaking, speak, stop, toggle, fallbackToFrench: () => ['ewo', 'ff'].includes(locale.value) }
}
