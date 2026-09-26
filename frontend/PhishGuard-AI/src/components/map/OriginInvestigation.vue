<script setup lang="ts">
/**
 * Admin investigation of where one email was really sent from:
 * route on a dark map, every server crossed, sender IP intelligence,
 * authentication, raw headers and pivots (other emails from the same IP / network).
 * Opening it is audited on the server (sender IPs are personal data).
 */
import { computed, ref, watch } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import CountryFlag from '@/components/ui/CountryFlag.vue'
import type { IconName } from '@/components/ui/icons'
import GeoMap from './GeoMap.vue'
import { geoService, type OriginInvestigation } from '@/services/geo.service'
import { timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

const props = defineProps<{ analysisId: number | null }>()
const emit = defineEmits<{ close: [] }>()
const { t } = useI18n()

type Tab = 'map' | 'path' | 'sender' | 'auth' | 'headers' | 'pivot'
const TABS: Array<{ id: Tab; icon: IconName }> = [
  { id: 'map', icon: 'mapPin' }, { id: 'path', icon: 'radar' }, { id: 'sender', icon: 'target' },
  { id: 'auth', icon: 'fingerprint' }, { id: 'headers', icon: 'file' }, { id: 'pivot', icon: 'users' },
]
const tab = ref<Tab>('map')
const current = ref<number | null>(null)
const data = ref<OriginInvestigation | null>(null)
const loading = ref(false)

async function load(id: number) {
  current.value = id
  loading.value = true
  data.value = null
  try { data.value = await geoService.investigate(id) } finally { loading.value = false }
}
watch(() => props.analysisId, (id) => { if (id) { tab.value = 'map'; void load(id) } }, { immediate: true })

const o = computed(() => data.value?.origin ?? null)
const geo = computed(() => o.value?.geo ?? null)
const place = computed(() => [geo.value?.district, geo.value?.city, geo.value?.region, geo.value?.country].filter(Boolean).join(', '))
const circles = computed(() => (geo.value?.lat != null ? [{ lat: geo.value.lat, lon: geo.value.lon!, radiusKm: o.value?.accuracy_km ?? 15, tone: 'danger' as const }] : []))
const routes = computed(() => (o.value?.route?.length ?? 0) > 1 ? [o.value!.route] : [])
const points = computed(() => (o.value?.route ?? []).map((r, i) => ({ id: `r${i}`, lat: r.lat, lon: r.lon, tone: i === 0 ? 'danger' as const : 'info' as const, label: `${r.kind} · ${r.ip}` })))

const authLines = computed(() => {
  const raw = o.value?.authentication ?? ''
  return ['spf', 'dkim', 'dmarc'].map((k) => {
    const m = raw.match(new RegExp(`${k}=(\\w+)`, 'i'))
    return { key: k.toUpperCase(), value: m?.[1]?.toLowerCase() ?? null }
  })
})
const authTone = (v: string | null) => (v === 'pass' ? 'text-emerald-400' : v ? 'text-red-400' : 'text-slate-500')
const verdictTone = (v: string) => (v === 'phishing' ? 'bg-red-500' : v === 'suspicious' ? 'bg-amber-500' : 'bg-emerald-500')
</script>

<template>
  <Teleport to="body">
    <div v-if="analysisId" class="fixed inset-0 z-[80] flex justify-end bg-slate-950/60 backdrop-blur-sm" @click.self="emit('close')" @keydown.esc="emit('close')">
      <aside class="panel" role="dialog" aria-modal="true" :aria-label="t('geo.inv.title')">
        <header class="flex items-start gap-3 border-b border-slate-800 p-5">
          <span class="grid h-10 w-10 place-items-center rounded-xl bg-cyan-400/10 text-cyan-300"><AppIcon name="radar" :size="20" /></span>
          <div class="min-w-0 flex-1">
            <p class="text-[11px] font-semibold uppercase tracking-[0.16em] text-cyan-300">{{ t('geo.inv.title') }}</p>
            <h2 class="truncate text-lg font-bold text-white">{{ data?.analysis.subject || t('ux.live.noSubject') }}</h2>
            <p v-if="data" class="truncate text-xs text-slate-400">{{ data.analysis.sender }} · #{{ data.analysis.id }} · {{ timeAgo(data.analysis.created_at) }}</p>
          </div>
          <button class="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white" :aria-label="t('common.close')" @click="emit('close')"><AppIcon name="x" :size="18" /></button>
        </header>

        <div v-if="loading" class="p-10 text-center text-sm text-slate-400"><span class="mx-auto mb-3 block h-6 w-6 animate-spin rounded-full border-2 border-cyan-400/30 border-t-cyan-400"></span>{{ t('geo.inv.loading') }}</div>

        <div v-else-if="data && !o" class="p-8 text-center text-sm text-slate-400">
          <AppIcon name="info" :size="28" class="mx-auto mb-2" />{{ t('geo.inv.none') }}
        </div>

        <template v-else-if="data && o">
          <!-- Verdict strip -->
          <div class="flex flex-wrap items-center gap-2 px-5 pt-4 text-xs">
            <span class="chip"><span class="h-2 w-2 rounded-full" :class="verdictTone(data.analysis.verdict)"></span>{{ t(`analysis.verdict.${data.analysis.verdict}`) }} · {{ data.analysis.score }}</span>
            <span class="chip">{{ t(`geo.prec.${o.precision}`) }}</span>
            <span v-if="o.provider" class="chip"><AppIcon name="mail" :size="12" /> {{ o.provider }}</span>
            <span v-if="o.claimed_brand" class="chip"><AppIcon name="target" :size="12" /> {{ t('geo.inv.claims', { brand: o.claimed_brand }) }}</span>
            <span v-for="f in o.flags" :key="f" class="chip chip-red"><AppIcon name="alert" :size="12" /> {{ t(`geo.flagShort.${f}`) }}</span>
          </div>

          <nav class="mt-4 flex gap-1 overflow-x-auto px-5">
            <button v-for="x in TABS" :key="x.id" class="tabbtn" :class="{ on: tab === x.id }" @click="tab = x.id">
              <AppIcon :name="x.icon" :size="14" /> {{ t(`geo.inv.tab.${x.id}`) }}
              <span v-if="x.id === 'pivot' && (data.pivots.same_ip.length + data.pivots.same_network.length)" class="ml-1 rounded-full bg-red-500 px-1.5 text-[10px] text-white">{{ data.pivots.same_ip.length + data.pivots.same_network.length }}</span>
            </button>
          </nav>

          <div class="flex-1 overflow-y-auto p-5">
            <!-- MAP -->
            <section v-if="tab === 'map'" class="space-y-4">
              <GeoMap v-if="points.length" :points="points" :routes="routes" :circles="circles" mode="plain" theme="dark" height="320px" />
              <div v-else class="rounded-xl border border-dashed border-slate-700 p-6 text-center text-sm text-slate-400">
                {{ o.provider ? t('geo.hiddenBy', { provider: o.provider }) : t('geo.hiddenUnknown') }}
                <p v-if="o.provider_server" class="mt-1 font-mono text-xs text-slate-500">{{ t('geo.inv.providerServer') }} {{ o.provider_server.host }} ({{ o.provider_server.ip }})</p>
              </div>
              <div v-if="geo" class="grid gap-3 sm:grid-cols-2">
                <div class="fact"><span>{{ t('geo.inv.place') }}</span><b class="flex items-center gap-1.5"><CountryFlag :code="geo.country_code" :size="16" /> {{ place }}</b></div>
                <div class="fact"><span>{{ t('geo.inv.accuracy') }}</span><b>± {{ o.accuracy_km }} km</b></div>
                <div class="fact"><span>{{ t('geo.inv.isp') }}</span><b>{{ geo.isp }} <small class="text-slate-500">{{ geo.asn }}</small></b></div>
                <div class="fact"><span>{{ t('geo.inv.network') }}</span><b>{{ t(`geo.net.${o.network_type ?? 'unknown'}`) }}</b></div>
                <div class="fact"><span>{{ t('geo.inv.coords') }}</span><b class="font-mono">{{ geo.lat?.toFixed(4) }}, {{ geo.lon?.toFixed(4) }}</b></div>
                <div class="fact"><span>{{ t('geo.inv.tz') }}</span><b>{{ geo.timezone }} · {{ t('geo.inv.headerTz') }} {{ o.sender_utc_offset ?? '—' }}</b></div>
              </div>
              <p class="text-[11px] text-slate-500">{{ t('geo.inv.limits') }}</p>
            </section>

            <!-- PATH -->
            <section v-else-if="tab === 'path'">
              <ol class="relative space-y-3 border-l border-slate-700 pl-5">
                <li v-for="(h, i) in o.hops" :key="i" class="relative">
                  <span class="absolute -left-[27px] top-1 grid h-4 w-4 place-items-center rounded-full" :class="h.is_origin ? 'bg-red-500' : 'bg-cyan-500'"></span>
                  <div class="rounded-xl bg-slate-900 p-3">
                    <p class="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                      <b class="text-white">{{ t('geo.inv.hop', { n: i + 1 }) }}</b>
                      <span v-if="h.is_origin" class="rounded bg-red-500/20 px-1.5 text-red-300">{{ t('geo.inv.origin') }}</span>
                      <span v-if="h.provider" class="rounded bg-slate-800 px-1.5">{{ h.provider }}</span>
                      <span v-if="h.delay_s != null" class="ml-auto" :class="h.delay_s > 3600 ? 'text-amber-400' : ''">+{{ h.delay_s }} s</span>
                    </p>
                    <p class="mt-1 font-mono text-xs text-slate-200">{{ h.from_host ?? '—' }} <span class="text-cyan-300">{{ h.from_ip ? `[${h.from_ip}]` : '' }}</span></p>
                    <p class="font-mono text-[11px] text-slate-500">→ {{ h.by_host ?? '—' }} · {{ h.protocol ?? '' }} · {{ h.time ? new Date(h.time).toLocaleString() : '' }}</p>
                  </div>
                </li>
              </ol>
            </section>

            <!-- SENDER -->
            <section v-else-if="tab === 'sender'" class="space-y-3">
              <div class="grid gap-3 sm:grid-cols-2">
                <div class="fact"><span>{{ t('geo.inv.ip') }}</span><b class="font-mono">{{ o.sender_ip ?? '—' }}</b><small class="text-slate-500">{{ o.found_by }}</small></div>
                <div class="fact"><span>{{ t('geo.inv.rdns') }}</span><b class="font-mono break-all">{{ geo?.reverse_dns ?? '—' }}</b></div>
                <div class="fact"><span>{{ t('geo.inv.org') }}</span><b>{{ geo?.org ?? '—' }}</b><small class="text-slate-500">{{ geo?.as_name }}</small></div>
                <div class="fact"><span>{{ t('geo.inv.flags') }}</span>
                  <b class="flex flex-wrap gap-1.5">
                    <span :class="geo?.mobile ? 'on' : ''" class="mini">{{ t('geo.net.mobile') }}</span>
                    <span :class="geo?.hosting ? 'on-red' : ''" class="mini">{{ t('geo.net.hosting') }}</span>
                    <span :class="geo?.proxy ? 'on-red' : ''" class="mini">{{ t('geo.net.proxy') }}</span>
                  </b></div>
                <div class="fact"><span>{{ t('geo.inv.blacklists') }}</span><b :class="o.blacklists.length ? 'text-red-400' : 'text-emerald-400'">{{ o.blacklists.length ? o.blacklists.join(', ') : t('geo.inv.clean') }}</b></div>
                <div class="fact"><span>{{ t('geo.inv.device') }}</span><b>{{ o.device.label ?? '—' }}</b><small class="font-mono text-slate-500 break-all">{{ o.device.agent }}</small></div>
                <div class="fact"><span>Message-ID</span><b class="font-mono">{{ o.message_id_domain ?? '—' }}</b></div>
                <div class="fact"><span>Return-Path</span><b class="font-mono break-all">{{ o.return_path ?? '—' }}</b></div>
              </div>
            </section>

            <!-- AUTH -->
            <section v-else-if="tab === 'auth'" class="space-y-3">
              <div class="grid grid-cols-3 gap-3">
                <div v-for="a in authLines" :key="a.key" class="rounded-xl bg-slate-900 p-4 text-center">
                  <p class="text-xs text-slate-400">{{ a.key }}</p>
                  <p class="mt-1 text-lg font-bold uppercase" :class="authTone(a.value)">{{ a.value ?? t('geo.inv.absent') }}</p>
                </div>
              </div>
              <p class="text-xs text-slate-400">{{ t('geo.inv.authHelp') }}</p>
              <pre v-if="o.authentication" class="raw">{{ o.authentication }}</pre>
            </section>

            <!-- HEADERS -->
            <section v-else-if="tab === 'headers'" class="space-y-2">
              <p class="text-xs text-slate-400">{{ t('geo.inv.headersHelp') }}</p>
              <pre v-for="(h, i) in [...o.hops].reverse()" :key="i" class="raw">Received: {{ h.raw }}</pre>
              <pre v-if="o.date_header" class="raw">Date: {{ o.date_header }}</pre>
            </section>

            <!-- PIVOT -->
            <section v-else class="space-y-5">
              <div v-for="group in (['same_ip', 'same_network'] as const)" :key="group">
                <h3 class="mb-2 text-sm font-semibold text-white">{{ t(`geo.inv.${group}`) }} <span class="text-slate-500">({{ data.pivots[group].length }})</span></h3>
                <p v-if="!data.pivots[group].length" class="text-xs text-slate-500">{{ t('geo.inv.noPivot') }}</p>
                <ul class="space-y-1.5">
                  <li v-for="a in data.pivots[group]" :key="a.id">
                    <button class="flex w-full items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-left text-xs hover:bg-slate-800" @click="load(a.id)">
                      <span class="h-2 w-2 shrink-0 rounded-full" :class="verdictTone(a.verdict)"></span>
                      <span class="min-w-0 flex-1 truncate text-slate-200">{{ a.subject || t('ux.live.noSubject') }}</span>
                      <span class="text-slate-500">{{ timeAgo(a.created_at) }}</span>
                    </button>
                  </li>
                </ul>
              </div>
              <p class="text-xs text-slate-500">{{ t('geo.inv.pivotHelp') }}</p>
            </section>
          </div>
        </template>
      </aside>
    </div>
  </Teleport>
</template>

<style scoped>
.panel { display: flex; width: 100%; max-width: 46rem; height: 100%; flex-direction: column; background: #020617; color: #e2e8f0; box-shadow: -20px 0 60px -20px rgba(0, 0, 0, 0.8); animation: slidein 0.25s ease; }
@keyframes slidein { from { transform: translateX(30px); opacity: 0; } }
.chip { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.2rem 0.55rem; border-radius: 9999px; background: #0f172a; border: 1px solid #1e293b; color: #cbd5e1; }
.chip-red { color: #fca5a5; border-color: rgba(239, 68, 68, 0.35); background: rgba(127, 29, 29, 0.25); }
.tabbtn { display: inline-flex; flex-shrink: 0; align-items: center; gap: 0.35rem; padding: 0.45rem 0.75rem; border-radius: 0.7rem; font-size: 0.78rem; font-weight: 600; color: #94a3b8; }
.tabbtn.on { color: #0f172a; background: #22d3ee; }
.fact { display: flex; flex-direction: column; gap: 0.15rem; padding: 0.7rem 0.85rem; border-radius: 0.9rem; background: #0f172a; font-size: 0.82rem; }
.fact > span { font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; }
.fact b { color: #f1f5f9; font-weight: 600; }
.mini { padding: 0.1rem 0.45rem; border-radius: 9999px; font-size: 0.7rem; color: #64748b; background: #1e293b; }
.mini.on { color: #0f172a; background: #22d3ee; }
.mini.on-red { color: white; background: #dc2626; }
.raw { white-space: pre-wrap; word-break: break-all; padding: 0.7rem; border-radius: 0.7rem; background: #0f172a; font: 11px/1.5 ui-monospace, monospace; color: #94a3b8; }
</style>
