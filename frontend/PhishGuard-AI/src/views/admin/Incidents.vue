<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import PageHeader from '@/components/admin/ui/PageHeader.vue'
import Panel from '@/components/admin/ui/Panel.vue'
import Pill from '@/components/admin/ui/Pill.vue'
import StatTile from '@/components/admin/ui/StatTile.vue'
import { socService, type Incident, type IncidentDetail, type IncidentStats, type IncidentStatus, type Severity } from '@/services/soc.service'
import { useNotificationsStore } from '@/stores/notifications'
import { formatDate, timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

/**
 * Incident response. Incidents are opened automatically by the correlation engine
 * (several dangerous messages sharing a domain / impersonated brand) or manually.
 * Workflow: open → investigating → contained → resolved (or false positive).
 */
const { t } = useI18n()
const toast = useNotificationsStore()

const STATUSES: IncidentStatus[] = ['open', 'investigating', 'contained', 'resolved', 'false_positive']
const SEVERITIES: Severity[] = ['critical', 'high', 'medium', 'low']
const SEV_TONE: Record<Severity, 'red' | 'orange' | 'amber' | 'blue'> = { critical: 'red', high: 'orange', medium: 'amber', low: 'blue' }
const STATUS_TONE: Record<IncidentStatus, 'red' | 'amber' | 'violet' | 'green' | 'slate'> = {
  open: 'red', investigating: 'amber', contained: 'violet', resolved: 'green', false_positive: 'slate',
}

const filter = ref<'active' | IncidentStatus | 'all'>('active')
const incidents = ref<Incident[]>([])
const stats = ref<IncidentStats | null>(null)
const loading = ref(false)
const detail = ref<IncidentDetail | null>(null)
const note = ref('')
const busy = ref(false)
let timer: number | undefined

async function load() {
  loading.value = true
  try {
    const result = await socService.listIncidents(filter.value === 'all' ? '' : filter.value)
    incidents.value = result.items
    stats.value = result.stats
  } finally { loading.value = false }
}
watch(filter, load)
onMounted(() => { void load(); timer = window.setInterval(load, 30_000) })
onBeforeUnmount(() => window.clearInterval(timer))

async function open(incident: Incident) {
  detail.value = await socService.getIncident(incident.id)
  note.value = ''
}
async function refreshDetail() {
  if (detail.value) detail.value = await socService.getIncident(detail.value.id)
  await load()
}

async function correlate() {
  const r = await socService.correlate()
  toast.push(t('inc.correlated', { opened: r.opened, updated: r.updated }), 'success')
  await load()
}

async function act(fn: () => Promise<unknown>, success: string) {
  busy.value = true
  try { await fn(); toast.push(success, 'success'); await refreshDetail() } catch { /* shown */ } finally { busy.value = false }
}
const setStatus = (s: IncidentStatus) => detail.value && act(() => socService.updateIncident(detail.value!.id, { status: s }), t('inc.toast.status', { status: t(`inc.status.${s}`) }))
const setSeverity = (s: Severity) => detail.value && act(() => socService.updateIncident(detail.value!.id, { severity: s }), t('inc.toast.severity'))
const assign = (id: number | null) => detail.value && act(() => socService.updateIncident(detail.value!.id, { assigned_to: id }), t('inc.toast.assigned'))
const block = () => detail.value && act(() => socService.blockIncident(detail.value!.id), t('inc.toast.blocked', { domain: detail.value!.indicator ?? '' }))
function addNote() {
  if (!detail.value || !note.value.trim()) return
  void act(() => socService.addNote(detail.value!.id, note.value.trim()), t('inc.toast.note')).then(() => { note.value = '' })
}

// ---------- Manual incident ----------
const creating = ref(false)
const newIncident = ref({ title: '', severity: 'medium' as Severity, indicator: '', description: '' })
async function create() {
  busy.value = true
  try {
    const created = await socService.createIncident(newIncident.value)
    creating.value = false
    newIncident.value = { title: '', severity: 'medium', indicator: '', description: '' }
    await load()
    await open(created)
  } catch { /* shown */ } finally { busy.value = false }
}

/** Auto incidents get a translated title built from their indicator. */
function title(i: Incident) {
  if (i.source === 'manual' || !i.indicator) return i.title
  return i.indicator_type === 'brand' ? t('inc.autoTitle.brand', { v: i.indicator }) : t('inc.autoTitle.domain', { v: i.indicator })
}

const TIMELINE_ICON: Record<string, string> = { opened: '🚨', linked: '🔗', status: '🔁', severity: '📈', assigned: '👤', note: '📝', blocked: '🚫', escalated: '🔥' }
function timelineText(kind: string, text: string, count?: number) {
  if (kind === 'linked') return t('inc.tl.linked', { n: count ?? text })
  if (kind === 'escalated') return t('inc.tl.escalated')
  if (kind === 'blocked') return t('inc.tl.blocked', { v: text })
  if (kind === 'status') return t('inc.tl.status', { v: text.split(' → ').map((s) => t(`inc.status.${s}`)).join(' → ') })
  if (kind === 'severity') return t('inc.tl.severity', { v: text.split(' → ').map((s) => t(`level.${s}`)).join(' → ') })
  if (kind === 'assigned') return t('inc.tl.assigned', { v: text })
  if (kind === 'opened') return text ? `${t('inc.tl.opened')} — ${text}` : t('inc.tl.opened')
  return text
}

const board = computed(() => SEVERITIES.map((s) => ({ severity: s, items: incidents.value.filter((i) => i.severity === s) })).filter((c) => c.items.length))
</script>

<template>
  <div class="space-y-6">
    <PageHeader :title="t('admin.page.incidents')" :subtitle="t('inc.subtitle')" icon="🚨" live>
      <button class="btn-ghost" @click="correlate">🧬 {{ t('inc.correlate') }}</button>
      <button class="btn-primary" @click="creating = true">+ {{ t('inc.new') }}</button>
    </PageHeader>

    <section class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
      <StatTile :label="t('inc.status.open')" :value="stats?.open ?? 0" icon="🚨" tone="red" clickable @click="filter = 'open'" />
      <StatTile :label="t('inc.status.investigating')" :value="stats?.investigating ?? 0" icon="🔍" tone="amber" clickable @click="filter = 'investigating'" />
      <StatTile :label="t('inc.status.contained')" :value="stats?.contained ?? 0" icon="🛡️" tone="violet" clickable @click="filter = 'contained'" />
      <StatTile :label="t('inc.kpi.criticalActive')" :value="stats?.critical_active ?? 0" icon="🔥" tone="red" />
      <StatTile :label="t('inc.kpi.resolved7')" :value="stats?.resolved_7d ?? 0" icon="✅" tone="green" clickable @click="filter = 'resolved'" />
      <StatTile :label="t('inc.kpi.mttr')" :value="stats?.mttr_hours != null ? `${stats.mttr_hours} h` : '—'" icon="⏱️" :hint="t('inc.kpi.mttrHint')" />
    </section>

    <div class="flex flex-wrap gap-1.5">
      <button v-for="f in (['active', ...STATUSES, 'all'] as const)" :key="f" class="chip" :class="{ active: filter === f }" @click="filter = f">
        {{ f === 'active' ? t('inc.filter.active') : f === 'all' ? t('common.all') : t(`inc.status.${f}`) }}
      </button>
    </div>

    <p v-if="!loading && !incidents.length" class="rounded-2xl border border-dashed border-slate-300 p-12 text-center text-sm text-slate-400 dark:border-slate-700">
      🛡️ {{ t('inc.empty') }}
    </p>

    <!-- Board grouped by severity -->
    <div v-for="col in board" :key="col.severity" class="space-y-2">
      <h2 class="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-500"><Pill :tone="SEV_TONE[col.severity]" dot>{{ t(`level.${col.severity}`) }}</Pill> {{ col.items.length }}</h2>
      <div class="grid gap-3 lg:grid-cols-2">
        <button v-for="i in col.items" :key="i.id" class="group rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-md dark:border-slate-800 dark:bg-slate-900"
                @click="open(i)">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="font-mono text-[11px] text-slate-400">{{ i.ref }} · {{ i.source === 'auto' ? `🤖 ${t('inc.source.auto')}` : `👤 ${t('inc.source.manual')}` }}</p>
              <p class="mt-0.5 truncate font-semibold text-slate-900 dark:text-white">{{ title(i) }}</p>
            </div>
            <Pill :tone="STATUS_TONE[i.status]" dot :pulse="i.status === 'open'">{{ t(`inc.status.${i.status}`) }}</Pill>
          </div>
          <div class="mt-3 grid grid-cols-4 gap-2 text-center text-xs">
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ i.messages }}</b><span class="text-slate-400">{{ t('inc.messages') }}</span></div>
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ i.affected_users }}</b><span class="text-slate-400">{{ t('inc.users') }}</span></div>
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums text-red-600">{{ Math.round(i.max_score) }}</b><span class="text-slate-400">{{ t('inc.maxScore') }}</span></div>
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base">{{ i.blocked ? '🚫' : '—' }}</b><span class="text-slate-400">{{ t('inc.blocked') }}</span></div>
          </div>
          <p class="mt-2 text-[11px] text-slate-400">{{ t('inc.lastActivity', { when: timeAgo(i.last_seen ?? i.updated_at) }) }}<span v-if="i.assignee"> · 👤 {{ i.assignee }}</span></p>
        </button>
      </div>
    </div>

    <!-- ========== Detail drawer ========== -->
    <Teleport to="body">
      <Transition name="drawer">
        <div v-if="detail" class="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-[2px]" @click.self="detail = null">
          <aside class="h-full w-full max-w-2xl overflow-y-auto bg-slate-50 shadow-2xl dark:bg-slate-950">
            <header class="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-6 py-4 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="font-mono text-xs text-slate-400">{{ detail.ref }} · {{ formatDate(detail.created_at) }}</p>
                  <h2 class="mt-0.5 text-lg font-bold text-slate-900 dark:text-white">{{ title(detail) }}</h2>
                  <div class="mt-1.5 flex flex-wrap gap-1">
                    <Pill :tone="SEV_TONE[detail.severity]" dot>{{ t(`level.${detail.severity}`) }}</Pill>
                    <Pill :tone="STATUS_TONE[detail.status]">{{ t(`inc.status.${detail.status}`) }}</Pill>
                    <Pill v-if="detail.indicator" tone="cyan">{{ detail.indicator_type }}: {{ detail.indicator }}</Pill>
                    <Pill v-if="detail.blocked" tone="red">🚫 {{ t('inc.blocked') }}</Pill>
                  </div>
                </div>
                <button class="rounded-lg px-2 py-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" @click="detail = null">✕</button>
              </div>
            </header>

            <div class="space-y-5 p-6">
              <!-- Response actions -->
              <Panel :title="t('inc.response')">
                <p class="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">{{ t('audit.col.status') }}</p>
                <div class="flex flex-wrap gap-1.5">
                  <button v-for="s in STATUSES" :key="s" class="chip" :class="{ active: detail.status === s }" :disabled="busy" @click="setStatus(s)">{{ t(`inc.status.${s}`) }}</button>
                </div>
                <div class="mt-4 grid gap-3 sm:grid-cols-2">
                  <label class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ t('intelx.col.severity') }}
                    <select class="input mt-1" :value="detail.severity" @change="setSeverity(($event.target as HTMLSelectElement).value as Severity)">
                      <option v-for="s in SEVERITIES" :key="s" :value="s">{{ t(`level.${s}`) }}</option>
                    </select></label>
                  <label class="text-xs font-semibold uppercase tracking-wide text-slate-400">{{ t('inc.assignee') }}
                    <select class="input mt-1" :value="detail.assigned_to ?? ''" @change="assign(Number(($event.target as HTMLSelectElement).value) || null)">
                      <option value="">—</option>
                      <option v-for="a in detail.admins" :key="a.id" :value="a.id">{{ a.name }}</option>
                    </select></label>
                </div>
                <button v-if="detail.indicator_type === 'domain' && !detail.blocked" class="mt-4 w-full rounded-xl bg-red-600 py-2.5 text-sm font-bold text-white hover:bg-red-700 disabled:opacity-50" :disabled="busy" @click="block">
                  🚫 {{ t('inc.block', { domain: detail.indicator ?? '' }) }}
                </button>
                <p v-if="detail.indicator_type === 'domain'" class="mt-2 text-xs text-slate-500">{{ t('inc.blockHint') }}</p>
              </Panel>

              <!-- Playbook -->
              <Panel :title="`📋 ${t('inc.playbook.title')}`">
                <ol class="space-y-2 text-sm">
                  <li v-for="step in 5" :key="step" class="flex gap-3">
                    <span class="grid h-6 w-6 flex-shrink-0 place-items-center rounded-full bg-slate-900 text-xs font-bold text-white dark:bg-cyan-500 dark:text-slate-900">{{ step }}</span>
                    <span class="text-slate-700 dark:text-slate-200">{{ t(`inc.playbook.${step}`) }}</span>
                  </li>
                </ol>
              </Panel>

              <!-- Timeline -->
              <Panel :title="t('inc.timeline')">
                <form class="mb-4 flex gap-2" @submit.prevent="addNote">
                  <input v-model="note" class="input" :placeholder="t('inc.notePlaceholder')" maxlength="2000" />
                  <button class="btn-primary" :disabled="busy || !note.trim()">{{ t('common.add') }}</button>
                </form>
                <ol class="relative space-y-4 border-l border-slate-200 pl-5 dark:border-slate-700">
                  <li v-for="(e, idx) in [...detail.timeline].reverse()" :key="idx" class="relative">
                    <span class="absolute -left-[31px] grid h-6 w-6 place-items-center rounded-full bg-white text-xs ring-2 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700">{{ TIMELINE_ICON[e.kind] ?? '•' }}</span>
                    <p class="text-sm text-slate-800 dark:text-slate-100" :class="{ 'rounded-xl bg-amber-50 p-2.5 dark:bg-amber-500/10': e.kind === 'note' }">{{ timelineText(e.kind, e.text, e.count) }}</p>
                    <p class="text-[11px] text-slate-400">{{ formatDate(e.at) }}<span v-if="e.actor"> · {{ e.actor }}</span></p>
                  </li>
                </ol>
              </Panel>

              <!-- Evidence -->
              <Panel :title="t('inc.evidence', { n: detail.messages_detail.length })" flush>
                <ul class="divide-y divide-slate-100 dark:divide-slate-800">
                  <li v-if="!detail.messages_detail.length" class="px-5 py-6 text-center text-sm text-slate-400">{{ t('inc.noEvidence') }}</li>
                  <li v-for="m in detail.messages_detail" :key="m.id" class="px-5 py-3">
                    <div class="flex items-center justify-between gap-3">
                      <p class="truncate text-sm text-slate-800 dark:text-slate-100">{{ m.preview }}</p>
                      <b class="text-sm tabular-nums text-red-600">{{ Math.round(m.score) }}</b>
                    </div>
                    <p class="text-[11px] text-slate-400">#{{ m.id }} · {{ formatDate(m.created_at) }} · {{ m.user ?? t('inc.visitor') }}</p>
                    <p v-for="u in m.urls" :key="u" class="truncate font-mono text-[11px] text-red-500">{{ u }}</p>
                  </li>
                </ul>
              </Panel>
            </div>
          </aside>
        </div>
      </Transition>
    </Teleport>

    <!-- New incident -->
    <Teleport to="body">
      <div v-if="creating" class="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 p-4 backdrop-blur-sm" @click.self="creating = false">
        <form class="w-full max-w-lg space-y-3 rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900" @submit.prevent="create">
          <h2 class="text-lg font-bold text-slate-900 dark:text-white">🚨 {{ t('inc.new') }}</h2>
          <input v-model="newIncident.title" class="input" required minlength="4" :placeholder="t('inc.form.title')" />
          <div class="grid grid-cols-2 gap-2">
            <select v-model="newIncident.severity" class="input"><option v-for="s in SEVERITIES" :key="s" :value="s">{{ t(`level.${s}`) }}</option></select>
            <input v-model="newIncident.indicator" class="input" :placeholder="t('inc.form.indicator')" />
          </div>
          <textarea v-model="newIncident.description" class="input min-h-[90px]" :placeholder="t('inc.form.description')"></textarea>
          <div class="flex justify-end gap-2">
            <button type="button" class="btn-ghost" @click="creating = false">{{ t('common.cancel') }}</button>
            <button class="btn-primary" :disabled="busy">{{ t('intelx.create') }}</button>
          </div>
        </form>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.input { width: 100%; border-radius: 0.75rem; border: 1px solid #e2e8f0; background: white; padding: 0.55rem 0.85rem; font-size: 0.875rem; outline: none; }
:global(.dark) .input { background: #0f172a; border-color: #334155; color: #f1f5f9; }
.btn-primary { border-radius: 0.75rem; background: #0f172a; padding: 0.55rem 1.1rem; font-size: 0.85rem; font-weight: 600; color: white; white-space: nowrap; }
.btn-primary:disabled { opacity: 0.45; }
:global(.dark) .btn-primary { background: #22d3ee; color: #0f172a; }
.btn-ghost { border-radius: 0.75rem; border: 1px solid #e2e8f0; padding: 0.55rem 1rem; font-size: 0.85rem; font-weight: 500; }
:global(.dark) .btn-ghost { border-color: #334155; color: #e2e8f0; }
.chip { border-radius: 9999px; border: 1px solid #e2e8f0; padding: 0.35rem 0.8rem; font-size: 0.78rem; font-weight: 600; color: #475569; }
.chip.active { background: #0f172a; border-color: #0f172a; color: white; }
:global(.dark) .chip { border-color: #334155; color: #cbd5e1; }
:global(.dark) .chip.active { background: #22d3ee; border-color: #22d3ee; color: #0f172a; }
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-enter-active aside, .drawer-leave-active aside { transition: transform 0.25s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from aside, .drawer-leave-to aside { transform: translateX(100%); }
</style>
