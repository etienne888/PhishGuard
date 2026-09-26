<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import ReviewDrawer from '@/components/admin/ReviewDrawer.vue'
import PageHeader from '@/components/admin/ui/PageHeader.vue'
import Panel from '@/components/admin/ui/Panel.vue'
import Pill from '@/components/admin/ui/Pill.vue'
import RingGauge from '@/components/admin/ui/RingGauge.vue'
import StatTile from '@/components/admin/ui/StatTile.vue'
import { adminOpsService, adminService, type ReviewItem, type ReviewView } from '@/services/admin.service'
import { socService, type TriageStats } from '@/services/soc.service'
import { useAdminOpsStore } from '@/stores/adminOps'
import { useNotificationsStore } from '@/stores/notifications'
import { STATUS_META, formatDate } from '@/utils/risk'
import { useI18n } from '@/i18n'

/**
 * Reports & review with automatic triage. The engine proposes a label + confidence for
 * every item; depending on the triage mode it closes confident items itself (default:
 * confidence >= 80 %) and leaves only the uncertain ones to humans.
 */
const { t } = useI18n()
const ops = useAdminOpsStore()
const toast = useNotificationsStore()

const VIEWS = computed<Array<{ id: ReviewView; label: string; help: string }>>(() => [
  { id: 'pending', label: t('queue.view.pending'), help: t('queue.help.pending') },
  { id: 'reported', label: `🚩 ${t('queue.view.reported')}`, help: t('queue.help.reported') },
  { id: 'borderline', label: `❓ ${t('queue.view.borderline')}`, help: t('queue.help.borderline') },
  { id: 'auto', label: `🤖 ${t('queue.view.auto')}`, help: t('queue.help.auto') },
  { id: 'reviewed', label: `✓ ${t('queue.view.reviewed')}`, help: t('queue.help.reviewed') },
])

const view = ref<ReviewView>('pending')
const items = ref<ReviewItem[]>([])
const total = ref(0)
const page = ref(1)
const perPage = 15
const loading = ref(false)
const selected = ref<number | null>(null)
const picked = ref<Set<number>>(new Set())
const triage = ref<TriageStats | null>(null)
const savingMode = ref(false)
const threshold = ref(80)

async function load() {
  loading.value = true
  try {
    const result = await adminOpsService.listReviewQueue(view.value, page.value)
    items.value = result.items
    total.value = result.total
    picked.value = new Set()
  } finally {
    loading.value = false
  }
}
async function loadTriage() {
  triage.value = await socService.getTriage()
  threshold.value = triage.value.threshold
}

function onDecided() {
  void load(); void loadTriage(); void ops.load()
}

watch(view, () => { page.value = 1; void load() })
watch(page, load)
onMounted(() => { void load(); void loadTriage() })

async function setMode(mode: TriageStats['mode'], newThreshold = threshold.value) {
  savingMode.value = true
  try {
    await adminService.updateSettings({ triage_mode: mode, triage_threshold: newThreshold })
    await loadTriage()
    await load()
    toast.push(t('triage.saved'), 'success')
  } catch { /* sudo prompt or toast */ } finally { savingMode.value = false }
}

async function runNow() {
  const result = await socService.runTriage()
  triage.value = result
  toast.push(t('triage.ran', { closed: result.auto_closed, left: result.left_for_humans }), 'success')
  await load()
}

const suggestable = computed(() => items.value.filter((i) => !i.review_label && i.triage_label))
function togglePick(id: number) {
  const next = new Set(picked.value)
  if (next.has(id)) next.delete(id); else next.add(id)
  picked.value = next
}
function pickAllSuggested() {
  picked.value = new Set(suggestable.value.filter((i) => (i.triage_confidence ?? 0) >= 60).map((i) => i.id))
}
async function acceptPicked() {
  const { decided } = await adminOpsService.bulkAccept([...picked.value])
  toast.push(t('triage.accepted', { n: decided }), 'success')
  onDecided()
}

const confTone = (c: number | null) => ((c ?? 0) >= 80 ? 'bg-emerald-500' : (c ?? 0) >= 60 ? 'bg-amber-500' : 'bg-slate-400')
const MODES: Array<TriageStats['mode']> = ['manual', 'assisted', 'auto']
</script>

<template>
  <div class="space-y-6">
    <PageHeader :title="t('admin.page.reports')" :subtitle="t('queue.subtitle')" icon="🚩">
      <a :href="adminOpsService.exportUrl" class="btn-ghost">📥 {{ t('queue.export') }}</a>
    </PageHeader>

    <!-- Triage control centre -->
    <section class="grid gap-4 lg:grid-cols-3">
      <div class="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 to-indigo-950 p-5 text-white shadow-lg lg:col-span-2">
        <div class="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p class="text-[11px] font-semibold uppercase tracking-widest text-cyan-300">🤖 {{ t('triage.title') }}</p>
            <p class="mt-1 max-w-xl text-sm text-slate-300">{{ t('triage.intro') }}</p>
          </div>
          <button class="rounded-xl bg-white/10 px-3 py-2 text-xs font-semibold hover:bg-white/20" @click="runNow">▶ {{ t('triage.runNow') }}</button>
        </div>
        <div class="mt-4 grid gap-2 sm:grid-cols-3">
          <button v-for="m in MODES" :key="m" :disabled="savingMode"
                  class="rounded-xl border p-3 text-left transition"
                  :class="triage?.mode === m ? 'border-cyan-400 bg-cyan-400/10' : 'border-white/10 hover:border-white/30'"
                  @click="setMode(m)">
            <p class="text-sm font-bold">{{ t(`triage.mode.${m}`) }} <span v-if="triage?.mode === m" class="text-cyan-300">●</span></p>
            <p class="mt-0.5 text-[11px] leading-snug text-slate-400">{{ t(`triage.mode.${m}.hint`) }}</p>
          </button>
        </div>
        <div v-if="triage?.mode === 'assisted'" class="mt-4">
          <div class="flex items-center justify-between text-xs text-slate-300"><span>{{ t('triage.threshold') }}</span><b class="text-base text-white">{{ threshold }} %</b></div>
          <input v-model.number="threshold" type="range" min="50" max="99" class="mt-1 w-full accent-cyan-400" @change="setMode('assisted', threshold)" />
          <p class="text-[11px] text-slate-400">{{ t('triage.thresholdHint', { n: threshold }) }}</p>
        </div>
      </div>

      <Panel :title="t('triage.performance')">
        <div class="flex items-center gap-4">
          <RingGauge :value="triage?.automation_rate" unit="%" :label="t('triage.automated')" />
          <div class="space-y-1.5 text-sm">
            <p><b class="tabular-nums">{{ triage?.auto_closed ?? 0 }}</b> <span class="text-slate-500">{{ t('triage.byEngine') }}</span></p>
            <p><b class="tabular-nums">{{ triage?.human_closed ?? 0 }}</b> <span class="text-slate-500">{{ t('triage.byHumans') }}</span></p>
            <p><b class="tabular-nums text-amber-600">{{ triage?.pending ?? 0 }}</b> <span class="text-slate-500">{{ t('triage.waiting') }}</span></p>
          </div>
        </div>
        <p class="mt-4 rounded-xl bg-slate-50 p-3 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-300">
          🎯 {{ triage?.engine_accuracy != null ? t('triage.accuracy', { n: triage.engine_accuracy, judged: triage.judged }) : t('triage.noAccuracy') }}
        </p>
      </Panel>
    </section>

    <!-- Views -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex flex-wrap gap-1.5">
        <button v-for="v in VIEWS" :key="v.id" class="chip" :class="{ active: view === v.id }" @click="view = v.id">{{ v.label }}</button>
      </div>
      <div v-if="suggestable.length" class="flex items-center gap-2">
        <button class="text-xs font-semibold text-blue-600 hover:underline dark:text-cyan-400" @click="pickAllSuggested">{{ t('triage.pickConfident') }}</button>
        <button class="btn-primary" :disabled="!picked.size" @click="acceptPicked">✓ {{ t('triage.acceptSelected', { n: picked.size }) }}</button>
      </div>
    </div>
    <p class="-mt-3 text-xs text-slate-500">{{ VIEWS.find((v) => v.id === view)?.help }}</p>

    <Panel flush>
      <div v-if="!loading && !items.length" class="p-12 text-center">
        <p class="text-4xl">✅</p>
        <p class="mt-2 text-sm text-slate-500">{{ t('queue.empty') }}</p>
      </div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm" :class="{ 'opacity-60': loading }">
          <thead class="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500 dark:bg-slate-800/50">
            <tr>
              <th class="w-10 px-4 py-3"></th>
              <th class="px-3">{{ t('review.message') }}</th>
              <th class="hidden px-3 md:table-cell">{{ t('queue.col.source') }}</th>
              <th class="px-3">{{ t('queue.col.engine') }}</th>
              <th class="px-3">{{ t('triage.suggestion') }}</th>
              <th class="hidden px-3 sm:table-cell">{{ view === 'reviewed' || view === 'auto' ? t('queue.col.decision') : t('queue.col.reason') }}</th>
              <th class="px-4"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr v-for="i in items" :key="i.id" class="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/40" @click="selected = i.id">
              <td class="px-4" @click.stop>
                <input v-if="!i.review_label && i.triage_label" type="checkbox" :checked="picked.has(i.id)" @change="togglePick(i.id)" />
              </td>
              <td class="max-w-xs px-3 py-3">
                <p class="truncate text-slate-800 dark:text-slate-100">{{ i.preview }}</p>
                <p class="text-[11px] text-slate-400">#{{ i.id }} · {{ formatDate(i.received_at) }}</p>
              </td>
              <td class="hidden max-w-[11rem] truncate px-3 text-xs text-slate-500 md:table-cell">{{ i.source }}</td>
              <td class="px-3"><span class="rounded-full border px-2 py-0.5 text-xs" :class="STATUS_META[i.status].chip">{{ STATUS_META[i.status].label }} · {{ Math.round(i.score) }}</span></td>
              <td class="px-3">
                <div v-if="i.triage_label" class="w-32">
                  <p class="text-xs font-semibold" :class="i.triage_label === 'phishing' ? 'text-red-600' : 'text-emerald-600'">
                    {{ i.triage_label === 'phishing' ? `🔴 ${t('verdict.phishing')}` : `🟢 ${t('status.safe')}` }}
                    <span class="text-slate-400">{{ Math.round(i.triage_confidence ?? 0) }} %</span></p>
                  <div class="mt-1 h-1.5 rounded-full bg-slate-100 dark:bg-slate-800"><div class="h-full rounded-full" :class="confTone(i.triage_confidence)" :style="{ width: `${i.triage_confidence ?? 0}%` }"></div></div>
                </div>
                <span v-else class="text-xs text-slate-400">—</span>
              </td>
              <td class="hidden px-3 text-xs sm:table-cell">
                <template v-if="i.review_label">
                  {{ i.review_label === 'phishing' ? `🔴 ${t('verdict.phishing')}` : `🟢 ${t('status.safe')}` }}
                  <Pill :tone="i.review_source === 'auto' ? 'violet' : 'blue'" class="ml-1">{{ i.review_source === 'auto' ? `🤖 ${t('triage.auto')}` : `👤 ${i.reviewer ?? t('triage.human')}` }}</Pill>
                </template>
                <template v-else>{{ i.reason === 'reported' ? `🚩 ${t('queue.reported')}` : `❓ ${t('queue.uncertain')}` }}</template>
              </td>
              <td class="px-4 text-right text-xs font-semibold text-blue-600 dark:text-cyan-400">{{ t('queue.examine') }} →</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="total > perPage" class="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-xs text-slate-500 dark:border-slate-800">
        <span>{{ t('history.range', { from: (page - 1) * perPage + 1, to: Math.min(page * perPage, total), total }) }}</span>
        <div class="flex gap-2">
          <button class="rounded-lg border px-3 py-1.5 disabled:opacity-40 dark:border-slate-700" :disabled="page === 1" @click="page--">← {{ t('common.previous') }}</button>
          <button class="rounded-lg border px-3 py-1.5 disabled:opacity-40 dark:border-slate-700" :disabled="page * perPage >= total" @click="page++">{{ t('common.next') }} →</button>
        </div>
      </div>
    </Panel>

    <section class="grid gap-3 sm:grid-cols-3">
      <StatTile :label="t('triage.kpi.total')" :value="triage?.total ?? 0" icon="📨" />
      <StatTile :label="t('triage.kpi.threshold')" :value="`${triage?.threshold ?? 80} %`" icon="🎚️" tone="cyan" />
      <StatTile :label="t('triage.kpi.mode')" :value="triage ? t(`triage.mode.${triage.mode}`) : '—'" icon="🤖" tone="violet" />
    </section>

    <ReviewDrawer :analysis-id="selected" @close="selected = null" @decided="onDecided" />
  </div>
</template>

<style scoped>
.btn-primary { border-radius: 0.75rem; background: #0f172a; padding: 0.5rem 1rem; font-size: 0.8rem; font-weight: 600; color: white; }
.btn-primary:disabled { opacity: 0.45; }
:global(.dark) .btn-primary { background: #22d3ee; color: #0f172a; }
.btn-ghost { border-radius: 0.75rem; border: 1px solid #e2e8f0; padding: 0.5rem 1rem; font-size: 0.85rem; font-weight: 500; }
:global(.dark) .btn-ghost { border-color: #334155; color: #e2e8f0; }
.chip { border-radius: 9999px; border: 1px solid #e2e8f0; padding: 0.4rem 0.9rem; font-size: 0.8rem; font-weight: 600; color: #475569; }
.chip.active { background: #0f172a; border-color: #0f172a; color: white; }
:global(.dark) .chip { border-color: #334155; color: #cbd5e1; }
:global(.dark) .chip.active { background: #22d3ee; border-color: #22d3ee; color: #0f172a; }
</style>
