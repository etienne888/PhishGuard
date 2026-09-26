<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import PageHeader from '@/components/admin/ui/PageHeader.vue'
import Panel from '@/components/admin/ui/Panel.vue'
import Pill from '@/components/admin/ui/Pill.vue'
import RingGauge from '@/components/admin/ui/RingGauge.vue'
import Sparkline from '@/components/admin/ui/Sparkline.vue'
import StatTile from '@/components/admin/ui/StatTile.vue'
import { socService, type SystemSnapshot } from '@/services/soc.service'
import { timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

/** Live system analysis: API traffic, host resources, database, detection engine. Refreshes every 10 s. */
const { t } = useI18n()
const data = ref<SystemSnapshot | null>(null)
const live = ref(true)
const error = ref(false)
const cpuHistory = ref<number[]>([])
const memHistory = ref<number[]>([])
let timer: number | undefined

async function load() {
  try {
    data.value = await socService.getSystem()
    error.value = false
    cpuHistory.value = [...cpuHistory.value, data.value.host.cpu_percent ?? 0].slice(-30)
    memHistory.value = [...memHistory.value, data.value.host.memory_percent ?? 0].slice(-30)
  } catch { error.value = true }
}
function schedule() {
  window.clearInterval(timer)
  if (live.value) timer = window.setInterval(load, 10_000)
}
onMounted(() => { void load(); schedule() })
onBeforeUnmount(() => window.clearInterval(timer))

// Job timestamps are naive UTC ISO strings from the server
const timeAgoSafe = (iso?: string) => (iso ? timeAgo(iso.endsWith('Z') ? iso : `${iso}Z`) : '—')

const STATUS_TONE = { healthy: 'green', degraded: 'amber', down: 'red' } as const
function uptime(seconds?: number) {
  if (!seconds) return '—'
  const d = Math.floor(seconds / 86400), h = Math.floor((seconds % 86400) / 3600), m = Math.floor((seconds % 3600) / 60)
  return d ? `${d} j ${h} h` : h ? `${h} h ${m} min` : `${m} min`
}
const components = computed(() => data.value ? [
  { key: 'database', ok: data.value.database.status === 'up', detail: data.value.database.latency_ms != null ? `${data.value.database.latency_ms} ms` : '' },
  { key: 'text_model', ok: data.value.engine.components.text_model, detail: 'Naive Bayes' },
  { key: 'ai', ok: data.value.engine.components.ai, detail: data.value.engine.ai_coverage != null ? t('sys.aiCoverage', { n: data.value.engine.ai_coverage }) : '' },
  { key: 'url_model', ok: data.value.engine.components.url_model, detail: 'XGBoost' },
  { key: 'smtp', ok: data.value.engine.components.smtp, detail: 'OTP e-mail' },
] : [])
</script>

<template>
  <div class="space-y-6">
    <PageHeader :title="t('sys.title')" :subtitle="t('sys.subtitle')" icon="💚" :live="live">
      <button class="btn-ghost" @click="live = !live; schedule()">{{ live ? `⏸ ${t('overview.pause')}` : `▶ ${t('overview.resume')}` }}</button>
      <button class="btn-primary" @click="load">↻ {{ t('common.refresh') }}</button>
    </PageHeader>

    <p v-if="error" class="rounded-xl bg-red-50 p-4 text-sm text-red-700 dark:bg-red-500/10 dark:text-red-300">{{ t('health.loadFailed') }}</p>

    <!-- Overall status -->
    <section v-if="data" class="relative overflow-hidden rounded-2xl bg-slate-900 p-6 text-white shadow-lg">
      <div class="scan" aria-hidden="true"></div>
      <div class="relative flex flex-wrap items-center gap-6">
        <div class="grid h-20 w-20 place-items-center rounded-3xl text-4xl" :class="{ 'bg-emerald-500/20': data.status === 'healthy', 'bg-amber-500/20': data.status === 'degraded', 'bg-red-500/20': data.status === 'down' }">
          {{ data.status === 'healthy' ? '💚' : data.status === 'degraded' ? '🟠' : '🔴' }}
        </div>
        <div class="flex-1">
          <Pill :tone="STATUS_TONE[data.status]" dot pulse>{{ t(`sys.status.${data.status}`) }}</Pill>
          <p class="mt-2 text-2xl font-bold">{{ t(`sys.headline.${data.status}`) }}</p>
          <p v-if="data.problems.length" class="text-sm text-amber-300">{{ data.problems.map((p) => t(`sys.problem.${p}`)).join(' · ') }}</p>
          <p v-else class="text-sm text-slate-400">{{ t('sys.allGood') }}</p>
        </div>
        <div class="grid grid-cols-3 gap-4 text-center">
          <div><p class="text-2xl font-bold tabular-nums">{{ data.traffic.rpm }}</p><p class="text-[11px] text-slate-400">{{ t('sys.rpm') }}</p></div>
          <div><p class="text-2xl font-bold tabular-nums">{{ data.traffic.p95_ms ?? '—' }}<small class="text-xs"> ms</small></p><p class="text-[11px] text-slate-400">p95</p></div>
          <div><p class="text-2xl font-bold tabular-nums" :class="data.traffic.error_rate > 1 ? 'text-red-400' : ''">{{ data.traffic.error_rate }}%</p><p class="text-[11px] text-slate-400">{{ t('sys.errors') }}</p></div>
        </div>
      </div>
    </section>

    <!-- Components -->
    <section v-if="data" class="grid grid-cols-2 gap-3 md:grid-cols-5">
      <div v-for="c in components" :key="c.key" class="rounded-2xl border bg-white p-4 dark:bg-slate-900"
           :class="c.ok ? 'border-emerald-200 dark:border-emerald-500/30' : 'border-slate-200 dark:border-slate-800'">
        <div class="flex items-center justify-between"><p class="text-xs font-semibold text-slate-500">{{ t(`sys.comp.${c.key}`) }}</p><Pill :tone="c.ok ? 'green' : 'slate'" dot :pulse="c.ok">{{ c.ok ? 'OK' : 'OFF' }}</Pill></div>
        <p class="mt-2 truncate text-xs text-slate-400">{{ c.detail }}</p>
      </div>
    </section>

    <div v-if="data" class="grid gap-6 lg:grid-cols-3">
      <!-- Host -->
      <Panel :title="`🖥️ ${t('sys.host')}`" :hint="data.host.available ? `${data.host.os} · Python ${data.host.python}${data.host.partial ? ' · ' + t('sys.partial') : ''}` : t('sys.noPsutil')">
        <div v-if="data.host.available" class="space-y-4">
          <div class="flex justify-around">
            <RingGauge :value="Math.round(data.host.cpu_percent ?? 0)" unit="%" label="CPU" invert :size="92" />
            <RingGauge :value="Math.round(data.host.memory_percent ?? 0)" unit="%" :label="t('sys.memory')" invert :size="92" />
            <RingGauge :value="Math.round(data.host.disk_percent ?? 0)" unit="%" :label="t('sys.disk')" invert :size="92" />
          </div>
          <div><p class="text-[11px] text-slate-400">CPU · {{ t('sys.last5') }}</p><Sparkline :values="cpuHistory" color="#06b6d4" /></div>
          <div><p class="text-[11px] text-slate-400">{{ t('sys.memory') }} · {{ t('sys.last5') }}</p><Sparkline :values="memHistory" color="#8b5cf6" /></div>
          <dl class="grid grid-cols-2 gap-2 text-xs">
            <div><dt class="text-slate-400">{{ t('sys.uptime') }}</dt><dd class="font-semibold">{{ uptime(data.host.uptime_seconds) }}</dd></div>
            <div><dt class="text-slate-400">{{ t('sys.processMem') }}</dt><dd class="font-semibold">{{ data.host.process_memory_mb }} MB</dd></div>
            <div><dt class="text-slate-400">RAM</dt><dd class="font-semibold">{{ data.host.memory_used_gb }} / {{ data.host.memory_total_gb }} GB</dd></div>
            <div><dt class="text-slate-400">{{ t('sys.diskFree') }}</dt><dd class="font-semibold">{{ data.host.disk_free_gb }} GB</dd></div>
          </dl>
        </div>
      </Panel>

      <!-- API traffic -->
      <Panel :title="`📡 ${t('sys.traffic')}`" :hint="t('sys.trafficHint', { n: data.traffic.window_minutes, total: data.traffic.requests })">
        <Sparkline :values="data.traffic.sparkline" :height="60" color="#2563eb" :label="t('sys.traffic')" />
        <div class="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
          <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.traffic.p50_ms ?? '—' }}</b><span class="text-slate-400">p50 ms</span></div>
          <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.traffic.p95_ms ?? '—' }}</b><span class="text-slate-400">p95 ms</span></div>
          <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.traffic.client_error_rate }}%</b><span class="text-slate-400">4xx</span></div>
        </div>
        <p class="mt-4 text-[11px] font-semibold uppercase tracking-wide text-slate-400">{{ t('sys.topEndpoints') }}</p>
        <ul class="mt-1 space-y-1 font-mono text-[11px]">
          <li v-for="e in data.traffic.top_endpoints" :key="e.endpoint" class="flex justify-between gap-2"><span class="truncate text-slate-600 dark:text-slate-300">{{ e.endpoint }}</span><b>{{ e.count }}</b></li>
        </ul>
        <p v-if="data.traffic.slow_endpoints.length" class="mt-3 text-[11px] text-amber-600">🐢 {{ t('sys.slow') }}: {{ data.traffic.slow_endpoints.map((e) => e.endpoint).join(', ') }}</p>
      </Panel>

      <!-- Database + engine -->
      <div class="space-y-6">
        <Panel :title="`🗄️ PostgreSQL ${data.database.version ?? ''}`">
          <div class="grid grid-cols-3 gap-2 text-center text-xs">
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.database.latency_ms ?? '—' }}</b><span class="text-slate-400">ms</span></div>
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.database.size_mb ?? '—' }}</b><span class="text-slate-400">MB</span></div>
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.database.connections ?? '—' }}</b><span class="text-slate-400">{{ t('sys.connections') }}</span></div>
          </div>
          <ul class="mt-3 space-y-1 text-xs">
            <li v-for="(n, table) in data.database.tables ?? {}" :key="table" class="flex justify-between"><span class="font-mono text-slate-500">{{ table }}</span><b class="tabular-nums">{{ n }}</b></li>
          </ul>
        </Panel>
        <Panel :title="`🧠 ${t('sys.engine')}`" :hint="t('sys.engineHint', { n: data.engine.analyses_24h })">
          <Sparkline :values="data.engine.hourly" color="#ef4444" :height="44" :label="t('sys.engine')" />
          <div class="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.engine.pipeline_p50_ms ?? '—' }}</b><span class="text-slate-400">p50 ms</span></div>
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.engine.pipeline_p95_ms ?? '—' }}</b><span class="text-slate-400">p95 ms</span></div>
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.engine.ai_coverage ?? '—' }}%</b><span class="text-slate-400">IA</span></div>
          </div>
        </Panel>
      </div>
    </div>

    <div v-if="data" class="grid gap-6 lg:grid-cols-2">
      <!-- User experience -->
      <Panel :title="`✨ ${t('sys.ux.title')}`" :hint="t('sys.ux.hint')">
        <p v-if="data.experience.error" class="text-xs text-amber-600">{{ t('sys.sectionError') }}</p>
        <template v-else>
          <div class="grid grid-cols-3 gap-2 text-center text-xs">
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.experience.visitor_scans_7d ?? 0 }}</b><span class="text-slate-400">{{ t('sys.ux.visitorScans') }}</span></div>
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.experience.conversion_rate ?? '—' }}<small v-if="data.experience.conversion_rate != null">%</small></b><span class="text-slate-400">{{ t('sys.ux.conversion') }}</span></div>
            <div class="rounded-lg bg-slate-50 p-2 dark:bg-slate-800"><b class="block text-base tabular-nums">{{ data.experience.feedback_30d?.helpful_rate ?? '—' }}<small v-if="data.experience.feedback_30d?.helpful_rate != null">%</small></b><span class="text-slate-400">{{ t('sys.ux.helpful') }}</span></div>
          </div>
          <p class="mt-3 text-[11px] font-semibold uppercase tracking-wide text-slate-400">{{ t('sys.ux.sources') }}</p>
          <ul class="mt-1 grid grid-cols-2 gap-1 text-xs">
            <li v-for="s in (['web', 'mailbox', 'forward', 'share'] as const)" :key="s" class="flex justify-between rounded-md bg-slate-50 px-2 py-1 dark:bg-slate-800">
              <span class="text-slate-500">{{ t(`ux.source.${s}`) }}</span><b class="tabular-nums">{{ data.experience.sources_7d?.[s] ?? 0 }}</b>
            </li>
          </ul>
          <p class="mt-3 text-[11px] font-semibold uppercase tracking-wide text-slate-400">{{ t('sys.ux.mailboxes') }}</p>
          <div class="mt-1 flex flex-wrap items-center gap-2 text-xs">
            <Pill :tone="data.experience.providers?.gmail ? 'green' : 'slate'" dot>Gmail {{ data.experience.providers?.gmail ? 'OK' : 'OFF' }}</Pill>
            <Pill :tone="data.experience.providers?.outlook ? 'green' : 'slate'" dot>Outlook {{ data.experience.providers?.outlook ? 'OK' : 'OFF' }}</Pill>
            <Pill :tone="data.experience.forwarding ? 'green' : 'slate'" dot>{{ t('sys.ux.forwarding') }} {{ data.experience.forwarding ? 'OK' : 'OFF' }}</Pill>
            <span class="text-slate-500">{{ t('sys.ux.connected', { n: data.experience.mailboxes?.active ?? 0 }) }}</span>
          </div>
        </template>
      </Panel>

      <!-- Background jobs -->
      <Panel :title="`⚙️ ${t('sys.jobs.title')}`" :hint="t('sys.jobs.hint')">
        <p v-if="!Object.keys(data.jobs ?? {}).length" class="text-xs text-slate-500">{{ t('sys.jobs.none') }}</p>
        <ul v-else class="space-y-1.5 text-xs">
          <li v-for="(job, name) in data.jobs" :key="name" class="flex items-center justify-between gap-2 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800">
            <span class="flex items-center gap-2"><span class="h-2 w-2 rounded-full" :class="job.ok ? 'bg-emerald-500' : 'bg-red-500'"></span><b>{{ t(`sys.jobs.${name}`) }}</b></span>
            <span class="text-slate-500">{{ timeAgoSafe(job.last_run) }} · {{ job.ok ? `${job.duration_ms} ms` : job.error }}</span>
          </li>
        </ul>
      </Panel>
    </div>

    <section v-if="data" class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <StatTile :label="t('sys.kpi.requests')" :value="data.traffic.requests" :hint="t('sys.kpi.window', { n: data.traffic.window_minutes })" icon="📡" />
      <StatTile :label="t('sys.kpi.analyses')" :value="data.engine.analyses_24h" icon="🔍" tone="blue" />
      <StatTile :label="t('sys.kpi.avg')" :value="data.engine.pipeline_avg_ms != null ? `${data.engine.pipeline_avg_ms} ms` : '—'" icon="⏱️" />
      <StatTile :label="t('sys.kpi.generated')" :value="new Date(data.generated_at + 'Z').toLocaleTimeString()" icon="🕒" />
    </section>
  </div>
</template>

<style scoped>
.btn-primary { border-radius: 0.75rem; background: #0f172a; padding: 0.5rem 1rem; font-size: 0.85rem; font-weight: 600; color: white; }
:global(.dark) .btn-primary { background: #22d3ee; color: #0f172a; }
.btn-ghost { border-radius: 0.75rem; border: 1px solid #e2e8f0; padding: 0.5rem 1rem; font-size: 0.85rem; font-weight: 500; }
:global(.dark) .btn-ghost { border-color: #334155; color: #e2e8f0; }
.scan { position: absolute; inset: 0; transform: translateX(-100%); background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.12), transparent); animation: scan 5s linear infinite; }
@keyframes scan { to { transform: translateX(100%); } }
@media (prefers-reduced-motion: reduce) { .scan { animation: none; } }
</style>
