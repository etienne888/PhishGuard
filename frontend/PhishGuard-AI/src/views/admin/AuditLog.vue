<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import PageHeader from '@/components/admin/ui/PageHeader.vue'
import Panel from '@/components/admin/ui/Panel.vue'
import Pill from '@/components/admin/ui/Pill.vue'
import StatTile from '@/components/admin/ui/StatTile.vue'
import type { SecurityEvent } from '@/services/admin.service'
import { socService, type EventFilters, type EventPage } from '@/services/soc.service'
import { formatDate } from '@/utils/risk'
import { useI18n } from '@/i18n'

/** Immutable audit trail: every login, security change and admin action with IP, place and device. */
const { t } = useI18n()

const filters = ref<EventFilters>({ scope: 'all', severity: '', q: '', days: 30, page: 1 })
const data = ref<EventPage | null>(null)
const loading = ref(false)
const expanded = ref<number | null>(null)
let timer: number | undefined
let searchTimer: number | undefined

async function load() {
  loading.value = true
  try { data.value = await socService.listEvents(filters.value) } finally { loading.value = false }
}
watch(() => [filters.value.scope, filters.value.severity, filters.value.days], () => { filters.value.page = 1; void load() })
watch(() => filters.value.q, () => { window.clearTimeout(searchTimer); searchTimer = window.setTimeout(() => { filters.value.page = 1; void load() }, 350) })
watch(() => filters.value.page, load)
onMounted(() => { void load(); timer = window.setInterval(load, 20_000) })
onBeforeUnmount(() => window.clearInterval(timer))

const SEV_TONE = { info: 'slate', warning: 'amber', critical: 'red' } as const
const SCOPES = ['all', 'auth', 'admin', 'registration'] as const
function detailText(e: SecurityEvent) {
  const entries = Object.entries(e.details).filter(([, v]) => v !== null && v !== '')
  return entries.map(([k, v]) => `${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`).join(' · ')
}
</script>

<template>
  <div class="space-y-6">
    <PageHeader :title="t('admin.page.audit')" :subtitle="t('audit.subtitle')" icon="📜" live>
      <a :href="socService.eventsExportUrl(filters)" class="btn-ghost">⬇ {{ t('admin.audit.export') }}</a>
    </PageHeader>

    <section class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <StatTile :label="t('audit2.kpi.total')" :value="data?.counters.total_24h ?? 0" icon="📊" />
      <StatTile :label="t('audit2.kpi.warning')" :value="data?.counters.warning_24h ?? 0" icon="⚠️" tone="amber" clickable @click="filters.severity = 'warning'" />
      <StatTile :label="t('audit2.kpi.critical')" :value="data?.counters.critical_24h ?? 0" icon="🔥" tone="red" clickable @click="filters.severity = 'critical'" />
      <StatTile :label="t('audit2.kpi.admin')" :value="data?.counters.admin_actions_24h ?? 0" icon="👑" tone="violet" clickable @click="filters.scope = 'admin'" />
    </section>

    <div class="flex flex-col gap-2 lg:flex-row lg:items-center">
      <div class="flex flex-wrap gap-1.5">
        <button v-for="s in SCOPES" :key="s" class="chip" :class="{ active: filters.scope === s }" @click="filters.scope = s">{{ t(`audit2.scope.${s}`) }}</button>
      </div>
      <div class="flex flex-1 gap-2 lg:justify-end">
        <input v-model="filters.q" type="search" class="input lg:w-72" :placeholder="t('audit2.search')" />
        <select v-model="filters.severity" class="input w-auto"><option value="">{{ t('audit2.allSeverities') }}</option>
          <option value="info">Info</option><option value="warning">{{ t('audit2.warning') }}</option><option value="critical">{{ t('level.critical') }}</option></select>
        <select v-model.number="filters.days" class="input w-auto"><option :value="1">24 h</option><option :value="7">{{ t('map.days', { n: 7 }) }}</option>
          <option :value="30">{{ t('map.days', { n: 30 }) }}</option><option :value="365">{{ t('map.days', { n: 365 }) }}</option></select>
      </div>
    </div>

    <Panel flush>
      <div class="overflow-x-auto">
        <table class="w-full text-sm" :class="{ 'opacity-60': loading }">
          <thead class="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500 dark:bg-slate-800/50">
            <tr><th class="px-5 py-3">{{ t('audit.col.timestamp') }}</th><th class="px-3">{{ t('audit.col.action') }}</th><th class="px-3">{{ t('audit2.col.account') }}</th>
              <th class="hidden px-3 md:table-cell">{{ t('audit.col.actor') }}</th><th class="px-3">IP · {{ t('map.col.location') }}</th><th class="hidden px-3 lg:table-cell">{{ t('as.logins.device') }}</th></tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr v-if="data && !data.items.length"><td colspan="6" class="px-5 py-10 text-center text-slate-400">{{ t('audit.noMatch') }}</td></tr>
            <template v-for="e in data?.items ?? []" :key="e.id">
              <tr class="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/40" @click="expanded = expanded === e.id ? null : e.id">
                <td class="whitespace-nowrap px-5 py-2.5 font-mono text-[11px] text-slate-500">{{ formatDate(e.created_at) }}</td>
                <td class="px-3"><Pill :tone="SEV_TONE[e.severity]" dot>{{ t(`event.${e.type}`) }}</Pill></td>
                <td class="max-w-[12rem] truncate px-3 text-xs">{{ e.user ?? (e.details.email as string) ?? '—' }}</td>
                <td class="hidden max-w-[12rem] truncate px-3 text-xs text-slate-500 md:table-cell">{{ e.actor && e.actor !== e.user ? e.actor : '—' }}</td>
                <td class="px-3 text-xs"><span class="font-mono">{{ e.ip ?? '—' }}</span>
                  <span class="text-slate-400"> · {{ e.location === 'local' ? t('as.logins.local') : e.location ?? '—' }}</span>
                  <Pill v-if="e.network.proxy" tone="red" class="ml-1">VPN</Pill></td>
                <td class="hidden px-3 text-xs text-slate-500 lg:table-cell">{{ e.device }}</td>
              </tr>
              <tr v-if="expanded === e.id" class="bg-slate-50/70 dark:bg-slate-800/30">
                <td colspan="6" class="px-5 py-3 font-mono text-[11px] text-slate-600 dark:text-slate-300">
                  {{ detailText(e) || t('audit2.noDetails') }}<span v-if="e.network.isp"> · ISP: {{ e.network.isp }}</span>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
      <div v-if="data && data.total > data.per_page" class="flex items-center justify-between border-t border-slate-100 px-5 py-3 text-xs text-slate-500 dark:border-slate-800">
        <span>{{ t('history.range', { from: (data.page - 1) * data.per_page + 1, to: Math.min(data.page * data.per_page, data.total), total: data.total }) }}</span>
        <div class="flex gap-2">
          <button class="rounded-lg border px-3 py-1.5 disabled:opacity-40 dark:border-slate-700" :disabled="data.page === 1" @click="filters.page = data.page - 1">← {{ t('common.previous') }}</button>
          <button class="rounded-lg border px-3 py-1.5 disabled:opacity-40 dark:border-slate-700" :disabled="data.page * data.per_page >= data.total" @click="filters.page = data.page + 1">{{ t('common.next') }} →</button>
        </div>
      </div>
    </Panel>
  </div>
</template>

<style scoped>
.input { border-radius: 0.75rem; border: 1px solid #e2e8f0; background: white; padding: 0.5rem 0.85rem; font-size: 0.85rem; outline: none; }
:global(.dark) .input { background: #0f172a; border-color: #334155; color: #f1f5f9; }
.btn-ghost { border-radius: 0.75rem; border: 1px solid #e2e8f0; padding: 0.5rem 1rem; font-size: 0.85rem; font-weight: 500; }
:global(.dark) .btn-ghost { border-color: #334155; color: #e2e8f0; }
.chip { border-radius: 9999px; border: 1px solid #e2e8f0; padding: 0.35rem 0.8rem; font-size: 0.78rem; font-weight: 600; color: #475569; }
.chip.active { background: #0f172a; border-color: #0f172a; color: white; }
:global(.dark) .chip { border-color: #334155; color: #cbd5e1; }
:global(.dark) .chip.active { background: #22d3ee; border-color: #22d3ee; color: #0f172a; }
</style>
