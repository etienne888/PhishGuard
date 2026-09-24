<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAnalysis } from '@/composables'
import { useNotificationsStore } from '@/stores'
import { useI18n } from '@/i18n'
import type { AnalysisResult, SignalKey } from '@/types'
import ScanAnimation from '@/components/scan/ScanAnimation.vue'
import ThreatAlert from '@/components/scan/ThreatAlert.vue'

/** `embedded`: rendered inside the user dashboard instead of the landing page. */
const props = withDefaults(defineProps<{ embedded?: boolean }>(), { embedded: false })
const emit = defineEmits<{ analyzed: [result: AnalysisResult] }>()

const showAlert = ref(false)
const resultPanel = ref<HTMLElement | null>(null)

function openExplanation() {
  showAlert.value = false
  resultPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const { result, isAnalyzing, error, examples, analyze, analyzeFile, reset, report } = useAnalysis()
const notifications = useNotificationsStore()
const { t } = useI18n()

const draft = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

function done(value: AnalysisResult | null) {
  if (!value) return
  showAlert.value = true
  emit('analyzed', value)
}

async function runAnalysis(text?: string) {
  const value = text ?? draft.value
  draft.value = value
  done(await analyze(value))
}

async function onFileChosen(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = '' // allow re-selecting the same file
  if (!file) return
  draft.value = ''
  done(await analyzeFile(file))
}

const SIGNAL_LABELS: Record<SignalKey, string> = {
  ml: 'Modèle ML',
  ai: 'Analyse IA',
  url: 'Liens',
  rules: 'Règles & expéditeur',
}

const signalRows = computed(() => {
  const signals = result.value?.signals
  if (!signals) return []
  return (Object.keys(SIGNAL_LABELS) as SignalKey[]).map((key) => ({
    key,
    label: SIGNAL_LABELS[key],
    value: signals[key] ?? null,
    weight: result.value?.weights?.[key] ?? 0,
  }))
})

const levelLabel = computed(() => {
  const level = result.value?.level
  return level ? { Critical: 'Critique', High: 'Élevé', Medium: 'Modéré', Low: 'Faible' }[level] : ''
})

function loadExample(text: string) {
  draft.value = text
  runAnalysis(text)
}

function clearAll() {
  draft.value = ''
  reset()
}

async function handleReport() {
  await report()
  notifications.push('Message signalé au CIRT-CM (démo).', 'success')
}

const verdictLabel = computed(() => {
  if (!result.value) return ''
  return { phishing: 'Phishing probable', suspicious: 'Suspect', legitimate: 'Légitime' }[result.value.verdict]
})

const verdictTone = computed(() => {
  if (!result.value) return { text: '', bar: '', chip: '' }
  return {
    phishing: { text: 'text-red-600', bar: 'bg-red-500', chip: 'text-red-400' },
    suspicious: { text: 'text-amber-600', bar: 'bg-amber-500', chip: 'text-amber-400' },
    legitimate: { text: 'text-emerald-600', bar: 'bg-emerald-500', chip: 'text-emerald-400' }
  }[result.value.verdict]
})
</script>

<template>
  <section :id="props.embedded ? undefined : 'analyze'" :class="props.embedded ? '' : 'py-20 px-4 bg-white'">
    <div :class="props.embedded ? '' : 'max-w-4xl mx-auto'">
      <div v-if="!props.embedded" class="text-center mb-12">
        <h2 class="text-3xl sm:text-4xl font-bold text-slate-800 font-display">{{ t('landing.analyzer.title') }}</h2>
        <p class="text-slate-500 mt-2">{{ t('landing.analyzer.subtitle') }}</p>
      </div>

      <div class="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
        <div class="p-6 sm:p-8">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 font-semibold">Aa</div>
            <div>
              <span class="text-sm font-semibold text-slate-700">{{ t('landing.analyzer.label') }}</span>
              <p class="text-xs text-slate-400">{{ t('landing.analyzer.subLabel') }}</p>
            </div>
          </div>

          <textarea
            v-model="draft"
            rows="5"
            class="w-full p-4 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition resize-none text-sm text-slate-700 placeholder:text-slate-400"
            :placeholder="t('landing.analyzer.placeholder')"
          ></textarea>

          <p v-if="error" class="mt-2 text-sm text-amber-600">{{ error }}</p>

          <ScanAnimation v-if="isAnalyzing" class="mt-4" />

          <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <button
                :disabled="isAnalyzing"
                class="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 disabled:hover:scale-100 flex items-center gap-2"
                @click="runAnalysis()"
              >
                <span v-if="isAnalyzing" class="h-3.5 w-3.5 rounded-full border-2 border-white/60 border-t-white animate-spin"></span>
                {{ isAnalyzing ? t('landing.analyzer.analyzing') : t('landing.analyzer.analyze') }}
              </button>
              <button
                :disabled="isAnalyzing"
                class="px-4 py-2.5 text-sm text-slate-600 border border-slate-200 hover:border-blue-400 hover:text-blue-600 rounded-xl transition disabled:opacity-60"
                title="Analyser un e-mail enregistré (.eml)"
                @click="fileInput?.click()"
              >
                📎 Fichier .eml
              </button>
              <input ref="fileInput" type="file" accept=".eml,message/rfc822" class="hidden" @change="onFileChosen" />
              <button class="px-4 py-2.5 text-sm text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition" @click="clearAll">
                {{ t('landing.analyzer.clear') }}
              </button>
            </div>
            <span class="text-xs text-slate-400">{{ t('landing.analyzer.privacy') }}</span>
          </div>
        </div>

        <Transition name="fade">
          <div v-if="result && !isAnalyzing" ref="resultPanel" class="border-t border-slate-100 p-6 sm:p-8 bg-slate-50/80 scroll-mt-24">
            <p v-if="result.offline" class="mb-4 text-xs px-3 py-2 rounded-lg bg-amber-50 border border-amber-200 text-amber-700">
              ⚠️ Serveur injoignable : ce résultat est une estimation simplifiée faite dans votre navigateur.
            </p>
            <p v-if="result.subject || result.sender" class="mb-3 text-xs text-slate-500">
              <span v-if="result.sender">De : <b>{{ result.sender }}</b></span>
              <span v-if="result.subject"> · Objet : <b>{{ result.subject }}</b></span>
            </p>
            <div class="flex items-start gap-4">
              <div class="flex-1">
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <span class="text-xl font-bold font-display" :class="verdictTone.text">{{ verdictLabel }}</span>
                  <span class="text-sm font-semibold" :class="verdictTone.text">
                    {{ result.score }}% de risque<span v-if="levelLabel"> · niveau {{ levelLabel }}</span>
                  </span>
                </div>
                <div class="mt-2 h-2.5 w-full bg-slate-200 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500" :class="verdictTone.bar" :style="{ width: result.score + '%' }"></div>
                </div>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span
                    v-for="indicator in result.indicators"
                    :key="indicator.label"
                    class="text-xs px-3 py-1 bg-white/70 rounded-full border border-slate-200 text-slate-600 inline-flex items-center gap-1.5"
                  >
                    <span class="h-1.5 w-1.5 rounded-full" :class="indicator.positive ? 'bg-emerald-400' : 'bg-red-400'"></span>
                    {{ indicator.label }}
                  </span>
                </div>

                <p v-for="override in result.overrides ?? []" :key="override" class="mt-3 text-xs text-slate-600">
                  ⚖️ {{ override }}
                </p>

                <div v-if="result.ai" class="mt-4 p-3 rounded-xl bg-white border border-violet-200">
                  <div class="text-xs font-semibold text-violet-700">
                    🤖 Analyse IA — {{ result.ai.category.replace(/_/g, ' ') }} ({{ result.ai.confidence }}% de confiance)
                  </div>
                </div>

                <div v-if="result.recommendation" class="mt-4 p-3 rounded-xl bg-blue-50 border border-blue-200 text-sm text-blue-900">
                  👉 {{ result.recommendation }}
                </div>

                <details v-if="signalRows.length" class="mt-4">
                  <summary class="text-xs text-slate-500 cursor-pointer select-none">Comment ce score a été calculé</summary>
                  <div class="mt-2 space-y-1.5">
                    <div v-for="row in signalRows" :key="row.key" class="flex items-center gap-3 text-xs">
                      <span class="w-36 text-slate-600">{{ row.label }}</span>
                      <div class="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                        <div class="h-full bg-slate-500 rounded-full" :style="{ width: (row.value ?? 0) + '%' }"></div>
                      </div>
                      <span class="w-28 text-right tabular-nums text-slate-500">
                        {{ row.value === null ? 'indisponible' : `${Math.round(row.value)} · poids ${Math.round(row.weight * 100)}%` }}
                      </span>
                    </div>
                  </div>
                </details>
              </div>
            </div>
            <div class="mt-4 flex gap-2">
              <button
                class="text-xs px-4 py-1.5 bg-red-100 text-red-700 rounded-full hover:bg-red-200 transition font-medium border border-red-200"
                @click="handleReport"
              >
                {{ t('landing.analyzer.report') }}
              </button>
              <a
                href="#education"
                class="text-xs px-4 py-1.5 bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition font-medium border border-blue-200"
              >
                {{ t('landing.analyzer.learnMore') }}
              </a>
            </div>
          </div>
        </Transition>
      </div>

      <Teleport to="body">
        <ThreatAlert v-if="showAlert && result && !result.offline" :result="result"
                     @close="showAlert = false" @details="openExplanation" />
      </Teleport>

      <div v-if="!props.embedded" class="mt-6 flex flex-wrap gap-2 justify-center">
        <span class="text-xs text-slate-400 mr-1">{{ t('landing.analyzer.tryWith') }}</span>
        <button
          v-for="example in examples"
          :key="example.id"
          class="text-xs px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-full transition text-slate-600"
          @click="loadExample(example.text)"
        >
          {{ example.label }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
