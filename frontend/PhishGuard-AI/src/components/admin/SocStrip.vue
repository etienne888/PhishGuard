<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import Pill from '@/components/admin/ui/Pill.vue'
import { socService, type SocSummary } from '@/services/soc.service'
import { timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

/** Command-centre band: system health, incidents, triage automation, approvals, blocklist (live, 15 s). */
const { t } = useI18n()
const router = useRouter()
const data = ref<SocSummary | null>(null)
const failed = ref(false)
let timer: number | undefined

async function load() {
  try {
    data.value = await socService.getSummary()
    failed.value = false
  } catch {
    // Shown (not hidden) so a stopped/outdated backend or a missing migration is noticed
    failed.value = true
  }
}
onMounted(() => { void load(); timer = window.setInterval(load, 15_000) })
onBeforeUnmount(() => window.clearInterval(timer))
defineExpose({ reload: load })

const STATUS_TONE = { healthy: 'green', degraded: 'amber', down: 'red' } as const
const SEV_DOT = { critical: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-amber-500', low: 'bg-blue-500' } as const
function incidentTitle(i: SocSummary['incidents']['latest'][number]) {
  if (i.source === 'manual' || !i.indicator) return i.title
  return i.indicator_type === 'brand' ? t('inc.autoTitle.brand', { v: i.indicator }) : t('inc.autoTitle.domain', { v: i.indicator })
}
</script>

<template>
  <section v-if="data" class="grid gap-3 lg:grid-cols-5">
    <!-- System -->
    <button class="tile" @click="router.push('/admin/health')">
      <div class="flex items-center justify-between"><span class="label">💚 {{ t('sys.title') }}</span><Pill :tone="STATUS_TONE[data.system.status]" dot pulse>{{ t(`sys.status.${data.system.status}`) }}</Pill></div>
      <div class="mt-3 grid grid-cols-3 gap-1 text-center">
        <div><b>{{ data.system.cpu ?? '—' }}<small>%</small></b><span>CPU</span></div>
        <div><b>{{ data.system.memory ?? '—' }}<small>%</small></b><span>RAM</span></div>
        <div><b>{{ data.system.p95_ms ?? '—' }}<small>ms</small></b><span>p95</span></div>
      </div>
    </button>

    <!-- Incidents -->
    <button class="tile lg:col-span-2" @click="router.push('/admin/incidents')">
      <div class="flex items-center justify-between"><span class="label">🚨 {{ t('admin.nav.incidents') }}</span>
        <span class="flex gap-1"><Pill tone="red" dot :pulse="data.incidents.critical > 0">{{ t('soc.critical', { n: data.incidents.critical }) }}</Pill><Pill>{{ t('soc.open', { n: data.incidents.open }) }}</Pill></span></div>
      <ul v-if="data.incidents.latest.length" class="mt-2 space-y-1 text-left">
        <li v-for="i in data.incidents.latest.slice(0, 3)" :key="i.id" class="flex items-center gap-2 text-xs">
          <span class="h-2 w-2 flex-shrink-0 rounded-full" :class="SEV_DOT[i.severity]"></span>
          <span class="truncate font-medium text-slate-700 dark:text-slate-200">{{ incidentTitle(i) }}</span>
          <span class="ml-auto whitespace-nowrap text-slate-400">{{ i.messages }} · {{ timeAgo(i.last_seen) }}</span>
        </li>
      </ul>
      <p v-else class="mt-3 text-left text-xs text-slate-400">🛡️ {{ t('soc.noIncident') }}</p>
    </button>

    <!-- Triage -->
    <button class="tile" @click="router.push('/admin/reports')">
      <div class="flex items-center justify-between"><span class="label">🤖 {{ t('triage.title') }}</span><Pill tone="violet">{{ t(`triage.mode.${data.triage.mode}`) }}</Pill></div>
      <div class="mt-3 grid grid-cols-2 gap-1 text-center">
        <div><b>{{ data.triage.automation_rate }}<small>%</small></b><span>{{ t('triage.automated') }}</span></div>
        <div><b class="text-amber-600">{{ data.triage.pending }}</b><span>{{ t('triage.waiting') }}</span></div>
      </div>
    </button>

    <!-- Access -->
    <div class="tile">
      <span class="label">🛂 {{ t('soc.access') }}</span>
      <div class="mt-3 grid grid-cols-2 gap-1 text-center">
        <button @click="router.push('/admin/users')"><b :class="data.pending_accounts ? 'text-amber-600' : ''">{{ data.pending_accounts }}</b><span>{{ t('soc.pendingAccounts') }}</span></button>
        <button @click="router.push('/admin/threat-intel')"><b class="text-red-600">{{ data.blocked_domains }}</b><span>{{ t('soc.blocked') }}</span></button>
      </div>
    </div>
  </section>
  <section v-else-if="failed" class="flex flex-wrap items-center gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200" role="alert">
    <span class="text-xl">🟠</span>
    <div class="flex-1">
      <p class="font-semibold">{{ t('soc.unavailable') }}</p>
      <p class="text-xs opacity-90">{{ t('soc.unavailableHint') }}</p>
    </div>
    <button class="rounded-lg border border-amber-300 px-3 py-1.5 text-xs font-semibold" @click="load">↻ {{ t('common.refresh') }}</button>
    <button class="rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-semibold text-white" @click="router.push('/admin/health')">{{ t('sys.title') }}</button>
  </section>
  <section v-else class="grid gap-3 lg:grid-cols-5" aria-hidden="true">
    <div v-for="i in 5" :key="i" class="h-28 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-800"></div>
  </section>
</template>

<style scoped>
.tile { border-radius: 1rem; border: 1px solid #e2e8f0; background: white; padding: 0.9rem 1rem; text-align: left; transition: all 0.15s; }
.tile:hover { border-color: #93c5fd; box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06); }
:global(.dark) .tile { border-color: #1e293b; background: #0f172a; }
.label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b; }
.tile b { display: block; font-size: 1.25rem; font-weight: 700; font-variant-numeric: tabular-nums; color: #0f172a; }
:global(.dark) .tile b { color: #f8fafc; }
.tile b small { font-size: 0.7rem; font-weight: 500; color: #94a3b8; margin-left: 1px; }
.tile span:not(.label) { font-size: 0.68rem; color: #94a3b8; }
</style>
