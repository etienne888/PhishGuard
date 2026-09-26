<script setup lang="ts">
/**
 * Threat Radar (admin): where threats come from.
 *   layer "origins"  where dangerous emails were really sent from (Received-chain tracing)
 *   layer "links"    where the malicious links are hosted (DNS + IP geolocation)
 * Clustered or heat map, replay slider, searchable + paginated side panel,
 * detail card and the full origin investigation of any email.
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import GeoMap, { type MapPoint, type Tone } from './GeoMap.vue'
import OriginInvestigation from './OriginInvestigation.vue'
import { geoService, flag, type OriginMap } from '@/services/geo.service'
import { adminOpsService, type ThreatMapData } from '@/services/admin.service'
import { timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

const props = withDefaults(defineProps<{ height?: string; compact?: boolean }>(), { height: '560px', compact: false })
const emit = defineEmits<{ open: [analysisId: number] }>()
const { t } = useI18n()

type Layer = 'origins' | 'links'
interface Item {
  id: string; lat: number; lon: number; count: number; tone: Tone; title: string; subtitle: string
  country: string | null; cc: string | null; isp: string | null; flags: string[]; network: string | null
  accuracy: number | null; first: string | null; last: string | null
  analyses: Array<{ id: number; subject: string | null; verdict: string; created_at: string | null }>
  extra: Array<{ label: string; value: string }>
}

const layer = ref<Layer>('origins')
const days = ref(30)
const scope = ref<'threats' | 'all'>('threats')
const mode = ref<'cluster' | 'heat'>('cluster')
const basemap = ref<'map' | 'satellite'>('map')
const q = ref('')
const verdictFilter = ref<'' | 'phishing' | 'suspicious' | 'legitimate'>('')
const page = ref(1)
const PER_PAGE = 20
const selectedId = ref<string | null>(null)
const investigate = ref<number | null>(null)
const loading = ref(false)
const origins = ref<OriginMap | null>(null)
const links = ref<ThreatMapData | null>(null)
let timer: number | undefined

const toneOf = (v: string): Tone => (v === 'phishing' ? 'danger' : v === 'suspicious' ? 'warn' : 'safe')

async function load() {
  loading.value = true
  try {
    if (layer.value === 'origins') origins.value = await geoService.originMap(days.value, scope.value)
    else links.value = await adminOpsService.getThreatMap(days.value, scope.value)
  } catch { /* shown as empty state */ } finally { loading.value = false }
}
watch([layer, days, scope], () => { selectedId.value = null; page.value = 1; replay.value = 100; void load() })
onMounted(() => { void load(); timer = window.setInterval(load, 60_000) })
onBeforeUnmount(() => { window.clearInterval(timer); window.clearInterval(playTimer) })

const items = computed<Item[]>(() => {
  if (layer.value === 'origins') {
    return (origins.value?.points ?? []).map((p) => ({
      id: p.id, lat: p.lat, lon: p.lon, count: p.count, tone: toneOf(p.verdict),
      title: [p.district, p.city].filter(Boolean).join(', ') || p.region || p.country || '?',
      subtitle: [p.region, p.country].filter(Boolean).join(', '), country: p.country, cc: p.country_code,
      isp: p.isps[0]?.name ?? null, flags: p.flags.map((f) => f.name), network: p.network_types[0]?.name ?? null,
      accuracy: p.accuracy_km, first: p.first_seen, last: p.last_seen, analyses: p.analyses,
      extra: [
        { label: t('geo.radar.ips'), value: p.ips.map((i) => `${i.name} (${i.count})`).join(' · ') },
        { label: t('geo.radar.brands'), value: p.brands.map((b) => b.name).join(', ') || '—' },
        { label: t('geo.radar.isps'), value: p.isps.map((i) => i.name).join(', ') },
      ],
    }))
  }
  return (links.value?.points ?? []).filter((p) => p.lat != null).map((p) => ({
    id: p.host, lat: p.lat!, lon: p.lon!, count: p.count, tone: toneOf(p.status === 'safe' ? 'legitimate' : p.status),
    title: p.host, subtitle: [p.city, p.country].filter(Boolean).join(', '), country: p.country ?? null,
    cc: p.country_code ?? null, isp: p.isp ?? null, flags: [], network: 'hosting', accuracy: 5,
    first: p.last_seen, last: p.last_seen,
    analyses: p.analysis_ids.map((id) => ({ id, subject: `#${id}`, verdict: p.status === 'safe' ? 'legitimate' : p.status, created_at: null })),
    extra: [{ label: 'IP', value: p.ip ?? '—' }, { label: 'ASN', value: p.asn ?? '—' }],
  }))
})

// Replay: show only what had appeared by the chosen moment of the period
const replay = ref(100)
const playing = ref(false)
let playTimer: number | undefined
function togglePlay() {
  playing.value = !playing.value
  window.clearInterval(playTimer)
  if (!playing.value) return
  if (replay.value >= 100) replay.value = 0
  playTimer = window.setInterval(() => {
    replay.value = Math.min(100, replay.value + 2)
    if (replay.value >= 100) { playing.value = false; window.clearInterval(playTimer) }
  }, 120)
}
const cutoff = computed(() => Date.now() - days.value * 86400_000 * (1 - replay.value / 100))
const cutoffLabel = computed(() => new Date(cutoff.value).toLocaleDateString())

const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  return items.value.filter((i) => {
    if (verdictFilter.value && i.tone !== toneOf(verdictFilter.value)) return false
    if (replay.value < 100 && i.first && new Date(i.first + (i.first.endsWith('Z') ? '' : 'Z')).getTime() > cutoff.value) return false
    if (!needle) return true
    return [i.title, i.subtitle, i.isp, ...i.flags].some((v) => v?.toLowerCase().includes(needle))
  })
})
const visible = computed(() => filtered.value.slice(0, page.value * PER_PAGE))
watch([q, verdictFilter], () => { page.value = 1 })

const mapPoints = computed<MapPoint[]>(() => filtered.value.map((i) => ({ id: i.id, lat: i.lat, lon: i.lon, count: i.count, tone: i.tone, label: `${i.title} · ${i.count}` })))
const selected = computed(() => items.value.find((i) => i.id === selectedId.value) ?? null)
const routes = computed(() => (layer.value === 'origins' && selectedId.value
  ? (origins.value?.points.find((p) => p.id === selectedId.value)?.routes ?? []) : []))
const circles = computed(() => (selected.value && layer.value === 'origins' && selected.value.accuracy
  ? [{ lat: selected.value.lat, lon: selected.value.lon, radiusKm: selected.value.accuracy, tone: selected.value.tone }] : []))

const stats = computed(() => {
  const list = items.value
  return {
    places: list.length,
    messages: list.reduce((n, i) => n + i.count, 0),
    countries: new Set(list.map((i) => i.country).filter(Boolean)).size,
    hidden: layer.value === 'origins' ? origins.value?.hidden ?? 0 : links.value?.unlocated.length ?? 0,
  }
})

function openAnalysis(id: number) {
  if (layer.value === 'origins') investigate.value = id
  else emit('open', id)
}
const FLAG_ICON: Record<string, IconName> = {
  datacenter: 'cpu', proxy: 'lock', blacklisted: 'ban', scripted: 'zap', foreign_for_local_brand: 'globe', timezone_mismatch: 'clock', long_delay: 'clock',
}
</script>

<template>
  <section class="radar-shell">
    <!-- Header + controls -->
    <header class="flex flex-wrap items-center gap-3 p-4">
      <div class="flex items-center gap-2.5">
        <span class="relative flex h-2.5 w-2.5"><span class="absolute h-full w-full animate-ping rounded-full bg-cyan-400 opacity-60"></span><span class="relative h-2.5 w-2.5 rounded-full bg-cyan-400"></span></span>
        <div>
          <h2 class="font-semibold text-white">{{ t('geo.radar.title') }}</h2>
          <p class="text-[11px] text-slate-400">{{ t(`geo.radar.sub.${layer}`) }}</p>
        </div>
      </div>
      <div class="seg ml-auto">
        <button v-for="l in (['origins', 'links'] as const)" :key="l" :class="{ on: layer === l }" @click="layer = l">
          <AppIcon :name="l === 'origins' ? 'mail' : 'link'" :size="13" /> {{ t(`geo.radar.layer.${l}`) }}
        </button>
      </div>
      <div class="seg">
        <button v-for="d in [7, 30, 90]" :key="d" :class="{ on: days === d }" @click="days = d">{{ d }} {{ t('geo.radar.d') }}</button>
      </div>
      <div class="seg">
        <button :class="{ on: mode === 'cluster' }" :title="t('geo.radar.cluster')" @click="mode = 'cluster'"><AppIcon name="target" :size="13" /></button>
        <button :class="{ on: mode === 'heat' }" :title="t('geo.radar.heat')" @click="mode = 'heat'"><AppIcon name="zap" :size="13" /></button>
        <button :class="{ on: basemap === 'satellite' }" :title="t('geo.radar.satellite')" @click="basemap = basemap === 'map' ? 'satellite' : 'map'"><AppIcon name="globe" :size="13" /></button>
      </div>
    </header>

    <!-- Stats -->
    <div class="grid grid-cols-2 gap-2 px-4 sm:grid-cols-4">
      <div class="stat"><b>{{ stats.places }}</b><span>{{ t('geo.radar.places') }}</span></div>
      <div class="stat"><b>{{ stats.messages }}</b><span>{{ layer === 'origins' ? t('geo.radar.emails') : t('geo.radar.hits') }}</span></div>
      <div class="stat"><b>{{ stats.countries }}</b><span>{{ t('geo.radar.countries') }}</span></div>
      <div class="stat"><b>{{ stats.hidden }}</b><span>{{ layer === 'origins' ? t('geo.radar.hidden') : t('geo.radar.unlocated') }}</span></div>
    </div>

    <div class="grid gap-4 p-4" :class="compact ? '' : 'lg:grid-cols-[1fr_22rem]'">
      <!-- Map + replay -->
      <div class="relative">
        <GeoMap :points="mapPoints" :routes="routes" :circles="circles" :mode="mode" theme="dark" :basemap="basemap"
                :selected-id="selectedId" :height="height" @select="(id) => (selectedId = id)" />
        <div v-if="loading" class="absolute right-3 top-3 z-[500] flex items-center gap-2 rounded-full bg-slate-900/90 px-3 py-1 text-xs text-slate-300"><span class="h-3 w-3 animate-spin rounded-full border-2 border-cyan-400/30 border-t-cyan-400"></span>{{ t('common.loading') }}</div>
        <div v-if="!loading && !items.length" class="absolute inset-0 z-[400] grid place-items-center">
          <p class="max-w-xs rounded-2xl bg-slate-900/90 p-4 text-center text-sm text-slate-300">{{ t(`geo.radar.empty.${layer}`) }}</p>
        </div>
        <div class="replay">
          <button class="grid h-8 w-8 place-items-center rounded-full bg-cyan-400 text-slate-900" :aria-label="t('geo.radar.play')" @click="togglePlay">
            <AppIcon :name="playing ? 'pause' : 'play'" :size="14" />
          </button>
          <input v-model.number="replay" type="range" min="0" max="100" class="flex-1 accent-cyan-400" :aria-label="t('geo.radar.replay')" />
          <span class="w-24 text-right text-[11px] tabular-nums text-slate-300">{{ replay >= 100 ? t('geo.radar.now') : cutoffLabel }}</span>
        </div>
      </div>

      <!-- Side panel -->
      <aside v-if="!compact" class="flex min-h-0 flex-col gap-3">
        <!-- Detail card -->
        <div v-if="selected" class="detail">
          <div class="flex items-start gap-2">
            <span class="text-2xl leading-none">{{ flag(selected.cc) }}</span>
            <div class="min-w-0 flex-1">
              <p class="truncate font-semibold text-white">{{ selected.title }}</p>
              <p class="truncate text-xs text-slate-400">{{ selected.subtitle }}</p>
            </div>
            <button class="text-slate-500 hover:text-white" :aria-label="t('common.close')" @click="selectedId = null"><AppIcon name="x" :size="16" /></button>
          </div>
          <div class="mt-3 grid grid-cols-3 gap-1.5 text-center text-[11px]">
            <div class="cell"><b>{{ selected.count }}</b>{{ layer === 'origins' ? t('geo.radar.emails') : t('geo.radar.hits') }}</div>
            <div class="cell"><b>± {{ selected.accuracy ?? '?' }}</b>km</div>
            <div class="cell"><b>{{ t(`geo.net.${selected.network ?? 'unknown'}`) }}</b>{{ t('geo.radar.network') }}</div>
          </div>
          <div v-if="selected.flags.length" class="mt-2 flex flex-wrap gap-1">
            <span v-for="f in selected.flags" :key="f" class="flagchip"><AppIcon :name="FLAG_ICON[f] ?? 'alert'" :size="11" /> {{ t(`geo.flagShort.${f}`) }}</span>
          </div>
          <dl class="mt-2 space-y-1 text-[11px]">
            <div v-for="e in selected.extra" :key="e.label"><dt class="text-slate-500">{{ e.label }}</dt><dd class="break-all font-mono text-slate-300">{{ e.value }}</dd></div>
          </dl>
          <p class="mt-3 text-[11px] font-semibold uppercase tracking-wide text-slate-500">{{ t('geo.radar.messages') }}</p>
          <ul class="mt-1 max-h-44 space-y-1 overflow-y-auto">
            <li v-for="a in selected.analyses" :key="a.id">
              <button class="flex w-full items-center gap-2 rounded-lg bg-slate-900 px-2.5 py-1.5 text-left text-xs hover:bg-slate-800" @click="openAnalysis(a.id)">
                <span class="h-2 w-2 shrink-0 rounded-full" :class="a.verdict === 'phishing' ? 'bg-red-500' : a.verdict === 'suspicious' ? 'bg-amber-500' : 'bg-emerald-500'"></span>
                <span class="min-w-0 flex-1 truncate text-slate-200">{{ a.subject || t('ux.live.noSubject') }}</span>
                <AppIcon :name="layer === 'origins' ? 'radar' : 'arrowRight'" :size="12" class="text-cyan-400" />
              </button>
            </li>
          </ul>
        </div>

        <!-- List -->
        <div class="flex items-center gap-2">
          <label class="search flex-1">
            <AppIcon name="search" :size="14" class="text-slate-500" />
            <input v-model="q" :placeholder="t('geo.radar.search')" class="w-full bg-transparent text-xs text-white outline-none placeholder:text-slate-500" />
          </label>
          <select v-model="verdictFilter" class="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-300" :aria-label="t('geo.radar.verdict')">
            <option value="">{{ t('common.all') }}</option>
            <option value="phishing">{{ t('analysis.verdict.phishing') }}</option>
            <option value="suspicious">{{ t('analysis.verdict.suspicious') }}</option>
            <option value="legitimate">{{ t('analysis.verdict.legitimate') }}</option>
          </select>
        </div>
        <ul class="list">
          <li v-for="i in visible" :key="i.id">
            <button class="row" :class="{ on: i.id === selectedId }" @click="selectedId = i.id">
              <span class="dot" :class="`tone-${i.tone}`"></span>
              <span class="min-w-0 flex-1 text-left">
                <span class="block truncate text-xs font-semibold text-slate-100">{{ flag(i.cc) }} {{ i.title }}</span>
                <span class="block truncate text-[11px] text-slate-500">{{ i.isp ?? i.subtitle }} · {{ timeAgo(i.last) }}</span>
              </span>
              <span class="count">{{ i.count }}</span>
            </button>
          </li>
          <li v-if="!filtered.length && items.length" class="p-3 text-center text-xs text-slate-500">{{ t('history.noResults') }}</li>
        </ul>
        <button v-if="visible.length < filtered.length" class="more" @click="page++">
          {{ t('geo.radar.more', { n: Math.min(PER_PAGE, filtered.length - visible.length), total: filtered.length }) }}
        </button>
        <p v-if="layer === 'origins' && origins?.hidden_by?.length" class="text-[11px] text-slate-500">
          <AppIcon name="eye" :size="12" class="inline" /> {{ t('geo.radar.hiddenBy', { list: origins.hidden_by.map((h) => `${h.provider} (${h.count})`).join(', ') }) }}
        </p>
      </aside>
    </div>

    <OriginInvestigation :analysis-id="investigate" @close="investigate = null" />
  </section>
</template>

<style scoped>
.radar-shell { border-radius: 1.4rem; background: radial-gradient(120% 60% at 0% 0%, rgba(34, 211, 238, 0.08), transparent 60%), #020617; border: 1px solid #1e293b; color: #e2e8f0; }
.seg { display: flex; gap: 2px; padding: 3px; border-radius: 0.8rem; background: #0f172a; border: 1px solid #1e293b; }
.seg button { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.3rem 0.6rem; border-radius: 0.6rem; font-size: 0.72rem; font-weight: 600; color: #94a3b8; }
.seg button.on { color: #0f172a; background: #22d3ee; }
.stat { display: flex; flex-direction: column; padding: 0.6rem 0.8rem; border-radius: 0.9rem; background: #0f172a; border: 1px solid #1e293b; }
.stat b { font-size: 1.25rem; color: white; font-variant-numeric: tabular-nums; }
.stat span { font-size: 0.68rem; color: #64748b; }
.replay { display: flex; align-items: center; gap: 0.6rem; margin-top: 0.6rem; padding: 0.45rem 0.6rem; border-radius: 9999px; background: #0f172a; border: 1px solid #1e293b; }
.detail { padding: 0.9rem; border-radius: 1rem; background: linear-gradient(160deg, rgba(34, 211, 238, 0.08), #0f172a 60%); border: 1px solid rgba(34, 211, 238, 0.25); }
.cell { display: flex; flex-direction: column; padding: 0.4rem; border-radius: 0.6rem; background: #020617; color: #64748b; }
.cell b { color: white; font-size: 0.8rem; }
.flagchip { display: inline-flex; align-items: center; gap: 0.2rem; padding: 0.1rem 0.45rem; border-radius: 9999px; font-size: 0.65rem; color: #fca5a5; background: rgba(127, 29, 29, 0.35); }
.search { display: flex; align-items: center; gap: 0.4rem; padding: 0.4rem 0.6rem; border-radius: 0.7rem; background: #0f172a; border: 1px solid #1e293b; }
.list { max-height: 22rem; overflow-y: auto; display: flex; flex-direction: column; gap: 0.25rem; }
.row { display: flex; width: 100%; align-items: center; gap: 0.55rem; padding: 0.45rem 0.55rem; border-radius: 0.7rem; transition: background 0.15s ease; }
.row:hover, .row.on { background: #0f172a; }
.row.on { box-shadow: inset 2px 0 0 #22d3ee; }
.dot { width: 0.55rem; height: 0.55rem; border-radius: 9999px; flex-shrink: 0; }
.tone-danger { background: #ef4444; box-shadow: 0 0 8px #ef4444; } .tone-warn { background: #f59e0b; } .tone-safe { background: #10b981; } .tone-info { background: #3b82f6; }
.count { min-width: 1.6rem; padding: 0.05rem 0.4rem; border-radius: 9999px; text-align: center; font-size: 0.7rem; font-weight: 700; color: #0f172a; background: #22d3ee; }
.more { padding: 0.45rem; border-radius: 0.7rem; font-size: 0.75rem; font-weight: 600; color: #22d3ee; border: 1px dashed rgba(34, 211, 238, 0.4); }
</style>
