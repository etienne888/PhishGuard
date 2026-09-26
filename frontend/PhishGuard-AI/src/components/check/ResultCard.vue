<script setup lang="ts">
/**
 * The result, most important first: a clear verdict and one sentence, what to
 * do now, why (with icons), the message with its risky parts highlighted, then
 * technical details folded away, read-aloud and "was this helpful?".
 */
import { computed, ref } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import WhatToDo from './WhatToDo.vue'
import HighlightedMessage from './HighlightedMessage.vue'
import OriginCard from './OriginCard.vue'
import { useSpeech } from '@/composables/useSpeech'
import { useAuthStore } from '@/stores/auth'
import { useAnalysisStore } from '@/stores/analysis'
import { useNotificationsStore } from '@/stores'
import { userDashboardService } from '@/services/userDashboard.service'
import { useI18n } from '@/i18n'
import type { AnalysisResult, SignalKey } from '@/types'

const props = withDefaults(defineProps<{ result: AnalysisResult; compact?: boolean }>(), { compact: false })
const emit = defineEmits<{ again: [] }>()

const { t } = useI18n()
const auth = useAuthStore()
const store = useAnalysisStore()
const toast = useNotificationsStore()
const speech = useSpeech()

const VERDICT = {
  phishing: { icon: 'shieldAlert' as IconName, ring: '#ef4444', soft: 'rgba(239,68,68,0.10)', text: 'text-red-600 dark:text-red-400' },
  suspicious: { icon: 'alert' as IconName, ring: '#f59e0b', soft: 'rgba(245,158,11,0.12)', text: 'text-amber-600 dark:text-amber-400' },
  legitimate: { icon: 'shieldCheck' as IconName, ring: '#10b981', soft: 'rgba(16,185,129,0.10)', text: 'text-emerald-600 dark:text-emerald-400' },
}
const tone = computed(() => VERDICT[props.result.verdict])
const score = computed(() => Math.round(props.result.score))

const summary = computed(() => {
  const r = props.result
  if (r.verdict === 'phishing') return r.brand ? t('ux.summary.fakeBrand', { brand: r.brand }) : t('ux.summary.phishing')
  if (r.verdict === 'suspicious') return r.brand ? t('ux.summary.suspiciousBrand', { brand: r.brand }) : t('ux.summary.suspicious')
  return t('ux.summary.safe')
})

function reasonIcon(label: string, positive: boolean): IconName {
  if (positive) return 'checkCircle'
  const l = label.toLowerCase()
  if (/^(ia|ai)\s*:/.test(l)) return 'brain'
  if (/spf|dkim|dmarc|authenti/.test(l)) return 'fingerprint'
  if (/pièce jointe|attachment/.test(l)) return 'paperclip'
  if (/code|pin|mot de passe|password|confidenti|secret/.test(l)) return 'key'
  if (/urgen|pression|pressure|délai|deadline|bloc|suspen/.test(l)) return 'clock'
  if (/paiement|payment|advance|avance|frais|fee/.test(l)) return 'sparkles'
  if (/expéditeur|sender|imite|imitat|réponse|reply/.test(l)) return 'user'
  if (/lien|link|domaine|domain|url|http|liste noire|blocklist/.test(l)) return 'link'
  return 'alert'
}
const reasons = computed(() => props.result.indicators.map((i) => ({ ...i, icon: reasonIcon(i.label, i.positive) })))

const SIGNALS: Array<{ key: SignalKey; icon: IconName }> = [
  { key: 'ml', icon: 'cpu' }, { key: 'ai', icon: 'brain' }, { key: 'url', icon: 'link' }, { key: 'rules', icon: 'target' },
]
const signalRows = computed(() => {
  const s = props.result.signals
  if (!s) return []
  return SIGNALS.map(({ key, icon }) => ({ key, icon, value: s[key] ?? null, weight: props.result.weights?.[key] ?? 0 }))
})

const SOURCE_ICON: Record<string, IconName> = { web: 'search', mailbox: 'inbox', forward: 'mail', share: 'share' }

// ---- read aloud
const spoken = computed(() => [
  t(`analysis.verdict.${props.result.verdict}`) + '.',
  summary.value,
  props.result.recommendation ?? '',
].filter(Boolean).join(' '))

// ---- report (signed-in users: to the review queue with automatic triage)
const reported = ref(false)
async function reportIt() {
  try {
    if (auth.user && props.result.analysisId) await userDashboardService.reportMessage(props.result.analysisId)
    else await store.report()
    reported.value = true
    toast.push(t('analysis.reported'), 'success')
  } catch { /* error toast shown by apiFetch */ }
}

// ---- feedback
const feedbackNote = ref('')
const askNote = ref(false)
const feedbackSent = ref(props.result.feedback != null)
async function feedback(value: 1 | -1) {
  if (value === -1 && !askNote.value) {
    askNote.value = true
    return
  }
  try {
    await store.sendFeedback(value, feedbackNote.value || undefined)
    feedbackSent.value = true
    askNote.value = false
  } catch { /* toast */ }
}
</script>

<template>
  <article class="result" :style="{ '--ring': tone.ring, '--soft': tone.soft }" aria-live="polite">
    <p v-if="result.offline" class="mb-4 flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-700">
      <AppIcon name="wifiOff" :size="16" /> {{ t('analysis.offline') }}
    </p>

    <!-- 1. Verdict -->
    <header class="hero">
      <div class="emblem" role="img" :aria-label="t('analysis.riskScore', { score })">
        <div class="emblem-ring" :style="{ '--value': score }"></div>
        <span class="emblem-core" :class="tone.text"><AppIcon :name="tone.icon" :size="34" :stroke="1.8" /></span>
      </div>
      <div class="min-w-0 flex-1">
        <p class="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{{ t('ux.result.eyebrow') }}</p>
        <h3 class="mt-0.5 text-2xl font-extrabold font-display sm:text-3xl" :class="tone.text">{{ t(`analysis.verdict.${result.verdict}`) }}</h3>
        <p class="mt-1 text-[0.95rem] text-slate-700 dark:text-slate-200">{{ summary }}</p>
        <div class="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <span class="meta"><AppIcon name="gauge" :size="14" /> {{ t('ux.result.score', { score }) }}</span>
          <span v-if="result.level" class="meta"><AppIcon name="target" :size="14" /> {{ t(`level.${result.level.toLowerCase()}`) }}</span>
          <span v-if="result.source" class="meta"><AppIcon :name="SOURCE_ICON[result.source] ?? 'search'" :size="14" /> {{ t(`ux.source.${result.source}`) }}</span>
          <span v-if="result.durationMs" class="meta"><AppIcon name="zap" :size="14" /> {{ t('ux.result.duration', { s: (result.durationMs / 1000).toFixed(1) }) }}</span>
        </div>
        <p v-if="result.sender || result.subject" class="mt-2 truncate text-xs text-slate-500">
          <span v-if="result.sender">{{ t('analysis.from') }} <b class="text-slate-700 dark:text-slate-300">{{ result.sender }}</b></span>
          <span v-if="result.subject"> · {{ t('analysis.subject') }} <b class="text-slate-700 dark:text-slate-300">{{ result.subject }}</b></span>
        </p>
      </div>
    </header>

    <div class="toolbar">
      <button v-if="speech.supported" class="tool" :aria-pressed="speech.speaking.value" @click="speech.toggle(spoken)">
        <AppIcon :name="speech.speaking.value ? 'stop' : 'volume'" :size="16" />
        {{ speech.speaking.value ? t('ux.result.stopReading') : t('ux.result.read') }}
      </button>
      <button v-if="result.verdict !== 'legitimate' || !reported" class="tool" :disabled="reported" @click="reportIt">
        <AppIcon :name="reported ? 'check' : 'shieldAlert'" :size="16" /> {{ reported ? t('ux.result.reported') : t('landing.analyzer.report') }}
      </button>
      <button class="tool" @click="emit('again')"><AppIcon name="refresh" :size="16" /> {{ t('ux.result.again') }}</button>
    </div>
    <p v-if="speech.supported && speech.fallbackToFrench()" class="-mt-2 mb-3 text-[11px] text-slate-400">{{ t('ux.result.readFrench') }}</p>

    <!-- 2. What to do -->
    <section class="block">
      <h4 class="block-title"><span class="block-icon"><AppIcon name="hand" :size="16" /></span>{{ t('ux.result.todo') }}</h4>
      <WhatToDo :result="result" />
    </section>

    <!-- 2b. Where the email came from (real emails only) -->
    <section v-if="result.origin" class="block">
      <h4 class="block-title"><span class="block-icon"><AppIcon name="mapPin" :size="16" /></span>{{ t('geo.title') }}</h4>
      <OriginCard :origin="result.origin" />
    </section>

    <!-- 3. Why -->
    <section v-if="reasons.length" class="block">
      <h4 class="block-title"><span class="block-icon"><AppIcon name="search" :size="16" /></span>{{ t('ux.result.why') }}</h4>
      <ul class="grid gap-2 sm:grid-cols-2">
        <li v-for="r in reasons" :key="r.label" class="reason" :class="r.positive ? 'good' : 'bad'">
          <AppIcon :name="r.icon" :size="16" class="mt-0.5" />
          <span>{{ r.label }}</span>
        </li>
      </ul>
      <p v-if="result.recommendation" class="advice"><AppIcon name="sparkles" :size="16" class="mt-0.5 text-blue-600" /> {{ result.recommendation }}</p>
    </section>

    <!-- 4. The message, highlighted -->
    <section v-if="result.text && !result.text.endsWith('.eml') && !compact" class="block">
      <h4 class="block-title"><span class="block-icon"><AppIcon name="eye" :size="16" /></span>{{ t('ux.result.message') }}</h4>
      <HighlightedMessage :text="result.text" :urls="result.urls" />
    </section>

    <!-- 5. Technical details (folded) -->
    <details v-if="signalRows.length || result.ai || result.overrides?.length" class="tech">
      <summary class="flex cursor-pointer items-center gap-2 text-sm font-semibold text-slate-600 dark:text-slate-300">
        <AppIcon name="cpu" :size="16" /> {{ t('ux.result.technical') }}
        <AppIcon name="chevronDown" :size="16" class="ml-auto opacity-60" />
      </summary>
      <div class="mt-3 space-y-2">
        <div v-for="row in signalRows" :key="row.key" class="flex items-center gap-3 text-xs">
          <AppIcon :name="row.icon" :size="15" class="text-slate-400" />
          <span class="w-32 text-slate-600 dark:text-slate-300">{{ t(`analysis.signal.${row.key}`) }}</span>
          <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
            <div class="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400" :style="{ width: (row.value ?? 0) + '%' }"></div>
          </div>
          <span class="w-28 text-right tabular-nums text-slate-500">
            {{ row.value === null ? t('analysis.unavailable') : t('analysis.signalValue', { value: Math.round(row.value), weight: Math.round(row.weight * 100) }) }}
          </span>
        </div>
        <p v-if="result.ai" class="flex items-center gap-2 text-xs text-violet-700 dark:text-violet-300">
          <AppIcon name="brain" :size="15" /> {{ t('analysis.aiHeading', { category: result.ai.category.replace(/_/g, ' '), confidence: result.ai.confidence }) }}
        </p>
        <p v-for="o in result.overrides ?? []" :key="o" class="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300">
          <AppIcon name="info" :size="15" class="mt-0.5" /> {{ o }}
        </p>
      </div>
    </details>

    <!-- 6. Was this helpful? -->
    <footer v-if="result.analysisId && auth.user" class="feedback">
      <template v-if="!feedbackSent">
        <span class="text-sm text-slate-600 dark:text-slate-300">{{ t('ux.feedback.question') }}</span>
        <div class="flex gap-2">
          <button class="fb" :aria-label="t('ux.feedback.yes')" @click="feedback(1)"><AppIcon name="thumbUp" :size="16" /> {{ t('ux.feedback.yes') }}</button>
          <button class="fb" :aria-label="t('ux.feedback.no')" @click="feedback(-1)"><AppIcon name="thumbDown" :size="16" /> {{ t('ux.feedback.no') }}</button>
        </div>
        <div v-if="askNote" class="mt-2 flex w-full flex-col gap-2 sm:flex-row">
          <input v-model="feedbackNote" maxlength="300" class="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm dark:border-slate-700" :placeholder="t('ux.feedback.placeholder')" />
          <button class="fb" @click="feedback(-1)">{{ t('ux.feedback.send') }}</button>
        </div>
      </template>
      <span v-else class="flex items-center gap-2 text-sm text-emerald-600"><AppIcon name="checkCircle" :size="16" /> {{ t('ux.feedback.thanks') }}</span>
    </footer>
  </article>
</template>

<style scoped>
.result { display: flex; flex-direction: column; gap: 1rem; }
.hero {
  display: flex;
  gap: 1.1rem;
  align-items: center;
  padding: 1.2rem;
  border-radius: 1.4rem;
  background: linear-gradient(135deg, var(--soft), transparent 70%);
  border: 1px solid color-mix(in srgb, var(--ring) 22%, transparent);
}
.emblem { position: relative; width: 5.5rem; height: 5.5rem; flex-shrink: 0; display: grid; place-items: center; }
.emblem-ring {
  position: absolute;
  inset: 0;
  border-radius: 9999px;
  background: conic-gradient(var(--ring) calc(var(--value) * 1%), rgba(148, 163, 184, 0.2) 0);
  -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 7px), #000 calc(100% - 6px));
  mask: radial-gradient(farthest-side, transparent calc(100% - 7px), #000 calc(100% - 6px));
  transition: background 0.6s ease;
}
.emblem-core { display: grid; place-items: center; width: 4rem; height: 4rem; border-radius: 9999px; background: var(--soft); }
.meta { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.2rem 0.55rem; border-radius: 9999px; background: rgba(148, 163, 184, 0.12); }
.toolbar { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.tool {
  display: inline-flex; align-items: center; gap: 0.4rem;
  padding: 0.5rem 0.85rem; border-radius: 0.8rem;
  font-size: 0.8rem; font-weight: 600; color: #334155;
  background: white; border: 1px solid rgba(148, 163, 184, 0.35);
  transition: all 0.15s ease;
}
.tool:hover:not(:disabled) { border-color: #2563eb; color: #2563eb; }
.tool:disabled { opacity: 0.7; }
:global(.dark) .tool { background: #0f172a; color: #cbd5e1; border-color: #1e293b; }
.block { padding: 1rem 1.1rem; border-radius: 1.2rem; background: white; border: 1px solid rgba(148, 163, 184, 0.22); }
:global(.dark) .block { background: #0b1224; border-color: #1e293b; }
.block-title { display: flex; align-items: center; gap: 0.55rem; margin-bottom: 0.8rem; font-size: 0.95rem; font-weight: 700; color: #1e293b; }
:global(.dark) .block-title { color: #e2e8f0; }
.block-icon { display: grid; place-items: center; width: 1.8rem; height: 1.8rem; border-radius: 0.6rem; color: #2563eb; background: rgba(37, 99, 235, 0.1); }
.reason { display: flex; gap: 0.5rem; padding: 0.55rem 0.7rem; border-radius: 0.8rem; font-size: 0.82rem; line-height: 1.4; }
.reason.bad { color: #9f1239; background: rgba(244, 63, 94, 0.06); }
.reason.good { color: #047857; background: rgba(16, 185, 129, 0.08); }
:global(.dark) .reason.bad { color: #fda4af; }
:global(.dark) .reason.good { color: #6ee7b7; }
.advice { margin-top: 0.8rem; display: flex; gap: 0.5rem; padding: 0.7rem 0.85rem; border-radius: 0.9rem; font-size: 0.85rem; color: #1e3a8a; background: rgba(37, 99, 235, 0.06); }
:global(.dark) .advice { color: #bfdbfe; }
.tech { padding: 0.85rem 1.1rem; border-radius: 1.2rem; border: 1px dashed rgba(148, 163, 184, 0.45); }
.tech summary::-webkit-details-marker { display: none; }
.feedback { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.6rem; padding: 0.85rem 1.1rem; border-radius: 1.2rem; background: rgba(148, 163, 184, 0.08); }
.fb { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.45rem 0.8rem; border-radius: 0.75rem; font-size: 0.8rem; font-weight: 600; color: #334155; background: white; border: 1px solid rgba(148, 163, 184, 0.35); }
.fb:hover { border-color: #2563eb; color: #2563eb; }
:global(.dark) .fb { background: #0f172a; color: #cbd5e1; border-color: #1e293b; }
@media (max-width: 480px) {
  .hero { flex-direction: column; text-align: center; }
  .hero .flex-wrap { justify-content: center; }
}
</style>
