import type { IconName } from '@/components/ui/icons'

/**
 * "Real or fake?" awareness quiz. Texts live in the dictionaries
 * (ux.quiz.q<id>.text / .why) so they follow the interface language.
 * Examples are modelled on scams reported in Cameroon (mobile money, banks,
 * utilities, fake jobs, family emergencies) - fictitious numbers and domains.
 */
export interface QuizItem {
  id: number
  channel: 'sms' | 'whatsapp' | 'email'
  sender: string
  answer: 'fake' | 'real'
}

export const QUIZ: QuizItem[] = [
  { id: 1, channel: 'sms', sender: 'MTN-MoMo', answer: 'fake' },
  { id: 2, channel: 'sms', sender: 'OrangeMoney', answer: 'real' },
  { id: 3, channel: 'sms', sender: '+237 6XX XX XX 41', answer: 'fake' },
  { id: 4, channel: 'email', sender: 'securite@afriland-secure-login.com', answer: 'fake' },
  { id: 5, channel: 'email', sender: 'PhishGuard-AI', answer: 'real' },
  { id: 6, channel: 'whatsapp', sender: '+237 6XX XX XX 08', answer: 'fake' },
  { id: 7, channel: 'sms', sender: 'ENEO-INFO', answer: 'fake' },
  { id: 8, channel: 'sms', sender: 'MaBanque', answer: 'real' },
  { id: 9, channel: 'whatsapp', sender: 'Recrutement Pro', answer: 'fake' },
  { id: 10, channel: 'sms', sender: 'MTN Service', answer: 'fake' },
]

export const LEVELS: Array<{ key: 'novice' | 'vigilant' | 'guardian' | 'expert' | 'master'; icon: IconName; floor: number }> = [
  { key: 'novice', icon: 'user', floor: 0 },
  { key: 'vigilant', icon: 'eye', floor: 50 },
  { key: 'guardian', icon: 'shield', floor: 150 },
  { key: 'expert', icon: 'shieldCheck', floor: 400 },
  { key: 'master', icon: 'trophy', floor: 800 },
]

export const GOLDEN_RULES: Array<{ key: string; icon: IconName }> = [
  { key: 'pin', icon: 'key' },
  { key: 'links', icon: 'link' },
  { key: 'urgency', icon: 'clock' },
  { key: 'prize', icon: 'sparkles' },
  { key: 'official', icon: 'phone' },
  { key: 'check', icon: 'shieldCheck' },
]
