<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { userAccountService, type AnalysisDetail } from '@/services/userAccount.service'
import { LEVEL_LABEL, SIGNAL_LABEL, STATUS_META, formatDate } from '@/utils/risk'
import { useI18n } from '@/i18n'

/** Side panel explaining one past analysis in plain language. */
const props = defineProps<{ analysisId: number | null }>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()

// Older analyses carry no `evidence_positive` flags: recognise the official-sender line in either language
function isPositive(index: number, text: string) {
  return detail.value?.evidence_positive?.[index] ?? (text.startsWith('Expéditeur officiel') || text.startsWith('Official sender'))
}
const UNKNOWN_SENDERS = ['Expéditeur inconnu', 'Unknown sender']

const detail = ref<AnalysisDetail | null>(null)
const loading = ref(false)
const error = ref('')

watch(() => props.analysisId, async (id) => {
  detail.value = null
  error.value = ''
  if (id === null) return
  loading.value = true
  try {
    detail.value = await userAccountService.getAnalysis(id)
  } catch {
    error.value = t('detail.loadFailed')
  } finally {
    loading.value = false
  }
}, { immediate: true })

const meta = computed(() => detail.value ? STATUS_META[detail.value.status] : null)
const signals = computed(() => {
  const d = detail.value
  if (!d?.signals) return []
  return Object.entries(d.signals).map(([key, value]) => ({
    key, label: SIGNAL_LABEL[key] ?? key, value, weight: d.weights?.[key as keyof typeof d.weights] ?? 0,
  }))
})
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="analysisId !== null" class="fixed inset-0 z-50 flex justify-end bg-slate-900/40" @click.self="emit('close')">
        <aside class="h-full w-full max-w-lg overflow-y-auto bg-white shadow-2xl" role="dialog" aria-modal="true" :aria-label="t('detail.title')">
          <header class="sticky top-0 z-10 flex items-center justify-between border-b border-slate-100 bg-white px-5 py-4">
            <h2 class="font-bold text-slate-800">{{ t('detail.title') }}</h2>
            <button class="rounded-lg px-2 py-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600" :aria-label="t('common.close')" @click="emit('close')">✕</button>
          </header>

          <div v-if="loading" class="p-6 text-sm text-slate-500">{{ t('common.loading') }}</div>
          <div v-else-if="error" class="p-6 text-sm text-red-600">{{ error }}</div>

          <div v-else-if="detail && meta" class="space-y-5 p-5">
            <!-- Verdict -->
            <div class="rounded-xl border p-4" :class="meta.chip">
              <div class="flex items-center justify-between">
                <span class="text-lg font-bold">{{ meta.emoji }} {{ meta.label }}</span>
                <span class="text-sm font-semibold">{{ Math.round(detail.score) }}/100</span>
              </div>
              <p class="mt-1 text-xs opacity-80">
                {{ t('detail.levelDate', { level: (detail.level && LEVEL_LABEL[detail.level]) || '—', date: formatDate(detail.received_at) }) }}
              </p>
            </div>

            <!-- What to do -->
            <section v-if="detail.recommendation">
              <h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ t('detail.whatToDo') }}</h3>
              <p class="mt-1.5 rounded-xl bg-blue-50 p-3 text-sm text-blue-900">👉 {{ detail.recommendation }}</p>
            </section>

            <!-- Why -->
            <section v-if="detail.evidence.length">
              <h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ t('detail.why') }}</h3>
              <ul class="mt-1.5 space-y-1.5">
                <li v-for="(item, index) in detail.evidence" :key="item" class="flex gap-2 text-sm text-slate-700">
                  <span class="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full" :class="isPositive(index, item) ? 'bg-emerald-500' : 'bg-red-400'"></span>
                  {{ item }}
                </li>
              </ul>
              <p v-for="o in detail.overrides" :key="o" class="mt-2 text-xs text-slate-500">⚖️ {{ o }}</p>
            </section>

            <!-- AI -->
            <section v-if="detail.ai" class="rounded-xl border border-violet-200 bg-violet-50/50 p-3">
              <p class="text-xs font-semibold text-violet-700">
                🤖 {{ t('detail.aiOpinion', { category: detail.ai.category.replace(/_/g, ' '), confidence: detail.ai.confidence }) }}
              </p>
            </section>

            <!-- How the score was built -->
            <section v-if="signals.length">
              <h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ t('analysis.howScored') }}</h3>
              <div class="mt-2 space-y-2">
                <div v-for="s in signals" :key="s.key" class="text-xs">
                  <div class="flex justify-between text-slate-600">
                    <span>{{ s.label }}</span>
                    <span class="tabular-nums">{{ s.value === null ? t('analysis.unavailable') : t('analysis.signalValue', { value: Math.round(s.value), weight: Math.round(s.weight * 100) }) }}</span>
                  </div>
                  <div class="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-100">
                    <div class="h-full rounded-full bg-slate-500" :style="{ width: (s.value ?? 0) + '%' }"></div>
                  </div>
                </div>
              </div>
            </section>

            <!-- Original message -->
            <section>
              <h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ t('detail.message') }}</h3>
              <p v-if="!UNKNOWN_SENDERS.includes(detail.sender)" class="mt-1 text-xs text-slate-500">{{ t('analysis.from') }} {{ detail.sender }}</p>
              <pre class="mt-1.5 whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-3 font-sans text-sm text-slate-700">{{ detail.text }}</pre>
            </section>

            <p class="rounded-xl bg-slate-50 p-3 text-xs text-slate-500">
              {{ t('detail.victim') }} <b>CIRT-CM</b> : {{ t('detail.hotline') }} <b>8202</b> · alerts@cirt.cm
            </p>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-enter-active aside, .drawer-leave-active aside { transition: transform 0.25s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from aside, .drawer-leave-to aside { transform: translateX(100%); }
</style>
