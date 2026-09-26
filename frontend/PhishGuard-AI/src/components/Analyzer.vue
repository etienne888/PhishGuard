<script setup lang="ts">
/**
 * The message checker: composer -> live analysis steps -> result.
 *
 * Visitors: the message is analysed straight away but the result stays locked
 * until they sign in (ResultGate); after sign-in the pending scan is claimed and
 * shown automatically. Offline: the message is queued and analysed as soon as
 * the connection is back.
 */
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useAnalysis } from '@/composables'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'
import type { AnalysisResult } from '@/types'
import AppIcon from '@/components/ui/AppIcon.vue'
import ScanComposer from '@/components/check/ScanComposer.vue'
import ScanProgress from '@/components/check/ScanProgress.vue'
import ResultGate from '@/components/check/ResultGate.vue'
import ResultCard from '@/components/check/ResultCard.vue'
import ThreatAlert from '@/components/scan/ThreatAlert.vue'

/** `embedded`: rendered inside another page (dashboard, /check) instead of as a landing section. */
const props = withDefaults(defineProps<{ embedded?: boolean }>(), { embedded: false })
const emit = defineEmits<{ analyzed: [result: AnalysisResult] }>()

const { result, gate, queued, isAnalyzing, isClaiming, error, examples, analyze, analyzeFile, flushQueue, cancelQueue,
        claim, pendingClaim, reset } = useAnalysis()
const auth = useAuthStore()
const { t } = useI18n()

const draft = ref('')
const showAlert = ref(false)
const output = ref<HTMLElement | null>(null)

async function reveal(value: AnalysisResult | null | undefined) {
  if (value && 'verdict' in value) {
    emit('analyzed', value)
    showAlert.value = !value.offline && value.verdict !== 'legitimate'
  }
  await nextTick()
  output.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function run(text?: string, source: 'web' | 'share' = 'web') {
  if (text !== undefined) draft.value = text
  const outcome = await analyze(draft.value, source)
  await reveal(outcome && 'verdict' in outcome ? outcome : null)
}

async function onFile(file: File) {
  draft.value = ''
  const outcome = await analyzeFile(file)
  await reveal(outcome && 'verdict' in outcome ? outcome : null)
}

function again() {
  draft.value = ''
  reset()
  document.getElementById('scan-input')?.focus()
}

function openExplanation() {
  showAlert.value = false
  output.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

// Signed in (here or in the auth modal) with a locked visitor scan: reveal it
async function claimIfPending() {
  if (!auth.user || !pendingClaim()) return
  await reveal(await claim())
}
watch(() => auth.user, (user) => { if (user) void claimIfPending() })

async function onOnline() {
  if (queued.value) await reveal(await flushQueue() as AnalysisResult | null)
}

onMounted(() => {
  window.addEventListener('online', onOnline)
  void claimIfPending()
  if (queued.value && navigator.onLine) void onOnline()
})
onBeforeUnmount(() => window.removeEventListener('online', onOnline))

defineExpose({ run })
</script>

<template>
  <section :id="props.embedded ? undefined : 'analyze'" :class="props.embedded ? '' : 'analyzer-section px-4 py-20'">
    <div :class="props.embedded ? '' : 'mx-auto max-w-4xl'">
      <div v-if="!props.embedded" class="mb-10 text-center">
        <span class="inline-flex items-center gap-2 rounded-full border border-blue-200 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700 dark:border-cyan-400/30 dark:bg-cyan-400/10 dark:text-cyan-300">
          <AppIcon name="sparkles" :size="14" /> {{ t('ux.analyzer.badge') }}
        </span>
        <h2 class="mt-3 text-3xl font-bold text-slate-800 dark:text-white sm:text-4xl font-display">{{ t('landing.analyzer.title') }}</h2>
        <p class="mt-2 text-slate-500">{{ t('landing.analyzer.subtitle') }}</p>
      </div>

      <div :class="props.embedded ? '' : 'shell'">
        <ScanComposer v-model="draft" :busy="isAnalyzing || isClaiming" :examples="examples"
                      @submit="run()" @file="onFile" @example="(text) => run(text)" />
      </div>

      <div ref="output" class="scroll-mt-24">
        <Transition name="rise" mode="out-in">
          <ScanProgress v-if="isAnalyzing || isClaiming" key="progress" class="mt-6" />

          <div v-else-if="queued" key="queued" class="queued mt-6" role="status">
            <AppIcon name="wifiOff" :size="22" class="text-amber-600" />
            <div class="flex-1">
              <p class="text-sm font-semibold text-slate-800 dark:text-white">{{ t('ux.offline.title') }}</p>
              <p class="text-xs text-slate-600 dark:text-slate-300">{{ t('ux.offline.text') }}</p>
            </div>
            <button class="text-xs font-semibold text-amber-700 underline" @click="cancelQueue">{{ t('common.cancel') }}</button>
          </div>

          <div v-else-if="error" key="error" class="mt-6 flex items-start gap-2 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800" role="alert">
            <AppIcon name="info" :size="18" class="mt-0.5" /> {{ error }}
          </div>

          <ResultGate v-else-if="gate" key="gate" :gate="gate" class="mt-6" />

          <ResultCard v-else-if="result" :key="`r-${result.analysisId ?? result.analyzedAt}`" :result="result" class="mt-6" @again="again" />
        </Transition>
      </div>

      <Teleport to="body">
        <ThreatAlert v-if="showAlert && result && !result.offline" :result="result"
                     @close="showAlert = false" @details="openExplanation" />
      </Teleport>
    </div>
  </section>
</template>

<style scoped>
.analyzer-section {
  background:
    radial-gradient(60% 50% at 50% 0%, rgba(37, 99, 235, 0.07), transparent 70%),
    white;
}
:global(.dark) .analyzer-section { background: radial-gradient(60% 50% at 50% 0%, rgba(34, 211, 238, 0.08), transparent 70%), #020617; }
.shell {
  padding: 1.25rem;
  border-radius: 1.75rem;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.25);
  box-shadow: 0 30px 60px -40px rgba(30, 64, 175, 0.45);
  backdrop-filter: blur(10px);
}
:global(.dark) .shell { background: rgba(15, 23, 42, 0.6); border-color: #1e293b; }
@media (min-width: 640px) { .shell { padding: 1.75rem; } }
.queued {
  display: flex; align-items: center; gap: 0.8rem;
  padding: 1rem 1.1rem; border-radius: 1.2rem;
  background: rgba(251, 191, 36, 0.1); border: 1px solid rgba(251, 191, 36, 0.35);
}
.rise-enter-active, .rise-leave-active { transition: opacity 0.25s ease, transform 0.25s ease; }
.rise-enter-from { opacity: 0; transform: translateY(8px); }
.rise-leave-to { opacity: 0; }
@media (prefers-reduced-motion: reduce) { .rise-enter-active, .rise-leave-active { transition: none; } }
</style>
