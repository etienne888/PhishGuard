<script setup lang="ts">
/**
 * Live view of a mailbox scan: waiting emails, the email being analysed going
 * through the scanner (steps lighting up), and each result sliding into a feed.
 * Polls GET /api/mailbox/<id>/progress while the scan runs.
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import { mailboxService, type ScanProgress } from '@/services/mailbox.service'
import { useI18n } from '@/i18n'

const props = withDefaults(defineProps<{ mailboxId: number; email: string; compact?: boolean }>(), { compact: false })
const emit = defineEmits<{ finished: [progress: ScanProgress] }>()
const router = useRouter()
const { t } = useI18n()

const p = ref<ScanProgress>({ state: 'running', phase: 'listing', total: 0, done: 0, threats: 0, feed: [] })
let timer: number | undefined
let stepTimer: number | undefined

async function poll() {
  try {
    const next = await mailboxService.progress(props.mailboxId)
    const wasRunning = p.value.state === 'running'
    p.value = next
    if (wasRunning && next.state !== 'running') {
      stop()
      emit('finished', next)
    }
  } catch { /* keep the last state; the next poll retries */ }
}
function stop() { window.clearInterval(timer); timer = undefined }
onMounted(() => { void poll(); timer = window.setInterval(poll, 1200) })
onBeforeUnmount(() => { stop(); window.clearInterval(stepTimer) })

// Steps of the analysis, animated while one email is in the scanner
const STEPS: Array<{ key: string; icon: IconName }> = [
  { key: 'read', icon: 'file' }, { key: 'sender', icon: 'user' }, { key: 'links', icon: 'link' },
  { key: 'ai', icon: 'brain' }, { key: 'verdict', icon: 'gauge' },
]
const step = ref(0)
watch(() => p.value.current?.subject, () => {
  step.value = 0
  window.clearInterval(stepTimer)
  stepTimer = window.setInterval(() => { if (step.value < STEPS.length - 1) step.value += 1 }, 900)
})

const running = computed(() => p.value.state === 'running')
const total = computed(() => p.value.total ?? 0)
const done = computed(() => p.value.done ?? 0)
const pct = computed(() => (total.value ? Math.round((done.value / total.value) * 100) : 0))
const waiting = computed(() => Math.max(0, Math.min(4, total.value - done.value - (p.value.current ? 1 : 0))))
const feed = computed(() => (props.compact ? (p.value.feed ?? []).slice(0, 3) : p.value.feed ?? []))

const VERDICT: Record<string, { icon: IconName; cls: string }> = {
  phishing: { icon: 'shieldAlert', cls: 'danger' },
  suspicious: { icon: 'alert', cls: 'warn' },
  legitimate: { icon: 'shieldCheck', cls: 'safe' },
}

function senderName(from: string) {
  const m = from.match(/^"?([^"<]+?)"?\s*</)
  return (m?.[1] ?? from).trim() || t('ux.live.unknownSender')
}
</script>

<template>
  <section class="live" :class="{ compact }" aria-live="polite">
    <!-- Header -->
    <header class="flex flex-wrap items-center gap-3">
      <span class="radar" :class="{ on: running }"><AppIcon :name="running ? 'radar' : p.state === 'error' ? 'alert' : 'checkCircle'" :size="20" /></span>
      <div class="min-w-0 flex-1">
        <p class="text-sm font-bold text-slate-800 dark:text-white">
          {{ running ? (p.phase === 'listing' ? t('ux.live.listing') : t('ux.live.scanning')) : p.state === 'error' ? t('ux.live.failed') : t('ux.live.done') }}
        </p>
        <p class="truncate text-xs text-slate-500">{{ email }}</p>
      </div>
      <div class="flex items-center gap-2 text-xs">
        <span class="chip"><AppIcon name="mail" :size="13" /> {{ done }} / {{ total }}</span>
        <span class="chip" :class="(p.threats ?? 0) ? 'chip-red' : ''"><AppIcon name="shieldAlert" :size="13" /> {{ t('ux.live.threats', { n: p.threats ?? 0 }) }}</span>
      </div>
    </header>

    <div class="bar mt-3" role="progressbar" :aria-valuenow="pct" aria-valuemin="0" aria-valuemax="100">
      <div class="bar-fill" :class="{ indeterminate: running && !total }" :style="{ width: (total ? pct : 30) + '%' }"></div>
    </div>

    <!-- Stage: queue -> scanner -->
    <div v-if="running && !compact" class="stage">
      <div class="queue" aria-hidden="true">
        <span v-for="i in waiting" :key="i" class="env" :style="{ animationDelay: `${i * 0.25}s`, transform: `translateY(${(i - 1) * -6}px) rotate(${(i % 2 ? -1 : 1) * 3}deg)` }">
          <AppIcon name="mail" :size="22" />
        </span>
        <p v-if="total - done > 1" class="mt-2 text-[11px] text-slate-500">{{ t('ux.live.waiting', { n: Math.max(0, total - done - 1) }) }}</p>
      </div>

      <AppIcon name="arrowRight" :size="18" class="hidden text-slate-300 sm:block" />

      <div class="scanner">
        <div class="beam" aria-hidden="true"></div>
        <template v-if="p.current && p.current.step === 'analyse'">
          <p class="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-blue-600 dark:text-cyan-300"><AppIcon name="scan" :size="13" /> {{ t('ux.live.analysing') }}</p>
          <p class="mt-1 truncate text-sm font-semibold text-slate-800 dark:text-white">{{ p.current.subject || t('ux.live.noSubject') }}</p>
          <p class="truncate text-xs text-slate-500">{{ senderName(p.current.sender) }}</p>
          <ol class="mt-3 flex flex-wrap gap-1.5">
            <li v-for="(s, i) in STEPS" :key="s.key" class="step" :class="i < step ? 'ok' : i === step ? 'now' : ''">
              <AppIcon :name="i < step ? 'check' : s.icon" :size="12" /> {{ t(`ux.progress.${s.key}`) }}
            </li>
          </ol>
        </template>
        <template v-else>
          <p class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
            <span class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-blue-200 border-t-blue-600"></span>
            {{ p.phase === 'listing' ? t('ux.live.lookingNew') : t('ux.live.fetching') }}
          </p>
        </template>
      </div>
    </div>

    <!-- Compact (dashboard widget): current email on one line -->
    <p v-else-if="running && compact && p.current?.subject" class="mt-3 flex items-center gap-2 truncate text-xs text-slate-600 dark:text-slate-300">
      <AppIcon name="scan" :size="14" class="shrink-0 text-blue-600" /> {{ t('ux.live.analysing') }} <b class="truncate">{{ p.current.subject }}</b>
    </p>

    <!-- Results feed -->
    <TransitionGroup v-if="feed.length" name="slide" tag="ul" class="feed">
      <li v-for="item in feed" :key="item.analysis_id">
        <button class="row" :class="VERDICT[item.verdict]?.cls" @click="router.push(`/check?analysis=${item.analysis_id}`)">
          <span class="row-icon"><AppIcon :name="VERDICT[item.verdict]?.icon ?? 'mail'" :size="16" /></span>
          <span class="min-w-0 flex-1 text-left">
            <span class="block truncate text-sm font-medium text-slate-800 dark:text-white">{{ item.subject || t('ux.live.noSubject') }}</span>
            <span class="block truncate text-[11px] text-slate-500">{{ senderName(item.sender) }}<template v-if="item.brand"> · {{ t('ux.live.imitates', { brand: item.brand }) }}</template></span>
          </span>
          <span class="verdict">{{ t(`analysis.verdict.${item.verdict}`) }} · {{ item.score }}</span>
        </button>
      </li>
    </TransitionGroup>

    <!-- End -->
    <div v-if="!running && !compact" class="end" :class="p.state === 'error' ? 'err' : ''">
      <AppIcon :name="p.state === 'error' ? 'info' : (p.threats ?? 0) ? 'shieldAlert' : 'shieldCheck'" :size="20" />
      <p class="flex-1 text-sm">
        {{ p.state === 'error' ? t(`ux.mailbox.error.${p.error ?? 'provider'}`) : !done ? t('ux.live.nothingNew') : (p.threats ?? 0) ? t('ux.live.summaryThreats', { n: done, threats: p.threats ?? 0 }) : t('ux.live.summaryClean', { n: done }) }}
      </p>
      <RouterLink v-if="done" to="/dashboard?tab=history" class="text-xs font-semibold text-blue-600 hover:underline">{{ t('ux.mailbox.seeResults') }}</RouterLink>
    </div>
  </section>
</template>

<style scoped>
.live { padding: 1.1rem; border-radius: 1.3rem; background: linear-gradient(135deg, rgba(37, 99, 235, 0.07), rgba(6, 182, 212, 0.06)); border: 1px solid rgba(37, 99, 235, 0.16); }
:global(.dark) .live { background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), rgba(6, 182, 212, 0.08)); border-color: rgba(34, 211, 238, 0.2); }
.radar { display: grid; place-items: center; width: 2.4rem; height: 2.4rem; border-radius: 9999px; color: #2563eb; background: rgba(37, 99, 235, 0.12); }
.radar.on { animation: ping 1.6s ease-in-out infinite; }
@keyframes ping { 50% { box-shadow: 0 0 0 8px rgba(37, 99, 235, 0.12); } }
.chip { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.2rem 0.55rem; border-radius: 9999px; font-weight: 600; color: #334155; background: rgba(255, 255, 255, 0.8); }
:global(.dark) .chip { background: rgba(15, 23, 42, 0.7); color: #cbd5e1; }
.chip-red { color: #b91c1c; background: rgba(254, 226, 226, 0.9); }
.bar { height: 0.45rem; border-radius: 9999px; overflow: hidden; background: rgba(148, 163, 184, 0.2); }
.bar-fill { height: 100%; border-radius: 9999px; background: linear-gradient(90deg, #2563eb, #06b6d4); transition: width 0.6s ease; }
.bar-fill.indeterminate { animation: slidebar 1.4s ease-in-out infinite; }
@keyframes slidebar { 0% { transform: translateX(-100%); } 100% { transform: translateX(330%); } }
.stage { margin-top: 1rem; display: flex; align-items: center; gap: 1rem; }
.queue { position: relative; display: flex; flex-direction: column; align-items: center; min-width: 4.5rem; }
.queue .env { display: grid; place-items: center; width: 3rem; height: 2.3rem; margin-top: -1.2rem; border-radius: 0.6rem; color: #2563eb; background: white; border: 1px solid rgba(37, 99, 235, 0.2); box-shadow: 0 6px 14px -10px rgba(37, 99, 235, 0.8); animation: float 2.4s ease-in-out infinite; }
.queue .env:first-child { margin-top: 0; }
:global(.dark) .queue .env { background: #0f172a; }
@keyframes float { 50% { translate: 0 -3px; } }
.scanner { position: relative; overflow: hidden; flex: 1; min-width: 0; padding: 0.9rem 1rem; border-radius: 1rem; background: white; border: 1px solid rgba(37, 99, 235, 0.2); box-shadow: 0 16px 30px -24px rgba(37, 99, 235, 0.8); }
:global(.dark) .scanner { background: #0b1224; }
.beam { position: absolute; left: 0; right: 0; top: 0; height: 40%; background: linear-gradient(180deg, transparent, rgba(6, 182, 212, 0.18), transparent); animation: beam 1.8s linear infinite; pointer-events: none; }
@keyframes beam { from { transform: translateY(-100%); } to { transform: translateY(260%); } }
.step { display: inline-flex; align-items: center; gap: 0.25rem; padding: 0.2rem 0.5rem; border-radius: 9999px; font-size: 0.68rem; font-weight: 600; color: #94a3b8; background: rgba(148, 163, 184, 0.12); transition: all 0.3s ease; }
.step.now { color: white; background: #2563eb; }
.step.ok { color: #047857; background: rgba(16, 185, 129, 0.14); }
.feed { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.4rem; }
.row { display: flex; width: 100%; align-items: center; gap: 0.7rem; padding: 0.55rem 0.7rem; border-radius: 0.9rem; background: white; border: 1px solid rgba(148, 163, 184, 0.2); transition: transform 0.15s ease; }
.row:hover { transform: translateX(2px); }
:global(.dark) .row { background: #0b1224; border-color: #1e293b; }
.row-icon { display: grid; place-items: center; width: 2rem; height: 2rem; border-radius: 0.7rem; flex-shrink: 0; }
.verdict { flex-shrink: 0; font-size: 0.7rem; font-weight: 700; }
.danger .row-icon { color: #dc2626; background: rgba(239, 68, 68, 0.1); } .danger .verdict { color: #dc2626; }
.warn .row-icon { color: #d97706; background: rgba(245, 158, 11, 0.12); } .warn .verdict { color: #d97706; }
.safe .row-icon { color: #059669; background: rgba(16, 185, 129, 0.1); } .safe .verdict { color: #059669; }
.end { margin-top: 1rem; display: flex; align-items: center; gap: 0.6rem; padding: 0.7rem 0.9rem; border-radius: 0.9rem; color: #065f46; background: rgba(16, 185, 129, 0.08); }
.end.err { color: #92400e; background: rgba(245, 158, 11, 0.1); }
:global(.dark) .end { color: #6ee7b7; }
.slide-enter-active { transition: all 0.45s cubic-bezier(0.2, 0.8, 0.2, 1); }
.slide-enter-from { opacity: 0; transform: translateY(-10px) scale(0.98); }
.slide-move { transition: transform 0.45s ease; }
@media (prefers-reduced-motion: reduce) { .radar.on, .beam, .queue .env, .bar-fill.indeterminate { animation: none; } }
</style>
