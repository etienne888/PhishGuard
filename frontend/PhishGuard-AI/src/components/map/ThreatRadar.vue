<script setup lang="ts">
/**
 * Threat Radar (admin): a live cyber-threat map.
 *   layer "origins"  where dangerous emails were really sent from (Received-chain tracing)
 *   layer "links"    where the malicious links are hosted (DNS + IP geolocation)
 * Attack arcs towards Yaoundé with travelling particles, radar sweep, glass HUD
 * (KPIs, live feed, country leaderboard), auto tour of hotspots, full screen,
 * replay slider, searchable + paginated side panel and the origin investigation.
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import CountryFlag from '@/components/ui/CountryFlag.vue'
import type { IconName } from '@/components/ui/icons'
import GeoMap, { type MapPoint, type Tone } from './GeoMap.vue'
import OriginInvestigation from './OriginInvestigation.vue'
import { geoService, flagHtml, type OriginMap } from '@/services/geo.service'
import { adminOpsService, type ThreatMapData } from '@/services/admin.service'
import { timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

const props = withDefaults(defineProps<{ height?: string; compact?: boolean }>(), { height: '600px', compact: false })
const emit = defineEmits<{ open: [analysisId: number] }>()
const { t } = useI18n()

type Layer = 'origins' | 'links'
interface Event { id: number; subject: string | null; verdict: string; created_at: string | null; place: string; cc: string | null; itemId: string }
interface Item {
  id: string; lat: number; lon: number; count: number; tone: Tone; title: string; subtitle: string
  country: string | null; cc: string | null; isp: string | null; flags: string[]; network: string | null
  accuracy: number | null; first: string | null; last: string | null
  analyses: Array<{ id: number; subject: string | null; verdict: string; created_at: string | null }>
  extra: Array<{ label: string; value: string }>
}

const shell = ref<HTMLElement | null>(null)
const mapRef = ref<InstanceType<typeof GeoMap> | null>(null)
const layer = ref<Layer>('origins')
const days = ref(30)
const scope = ref<'threats' | 'all'>('threats')
const mode = ref<'cluster' | 'heat'>('cluster')
const basemap = ref<'map' | 'satellite'>('map')
const arcs = ref(true)
const hud = ref(true)  // floating panels (hide for a clean map)
const q = ref('')
const verdictFilter = ref<'' | 'phishing' | 'suspicious' | 'legitimate'>('')
const page = ref(1)
const PER_PAGE = 20
const selectedId = ref<string | null>(null)
const investigate = ref<number | null>(null)
const loading = ref(false)
const origins = ref<OriginMap | null>(null)
const links = ref<ThreatMapData | null>(null)
const fullscreen = ref(false)
const freshIds = ref(new Set<string>())
let timer: number | undefined

const TARGET = computed(() => links.value?.target ?? { lat: 3.848, lon: 11.502, label: 'Yaoundé' })
const toneOf = (v: string): Tone => (v === 'phishing' ? 'danger' : v === 'suspicious' ? 'warn' : 'safe')

async function load() {
  loading.value = true
  const before = new Set(items.value.map((i) => i.id))
  try {
    if (layer.value === 'origins') origins.value = await geoService.originMap(days.value, scope.value)
    else links.value = await adminOpsService.getThreatMap(days.value, scope.value)
    // Highlight places that appeared since the last refresh
    freshIds.value = before.size ? new Set(items.value.filter((i) => !before.has(i.id)).map((i) => i.id)) : new Set()
  } catch { /* shown as empty state */ } finally { loading.value = false }
}
watch([layer, days, scope], () => { selectedId.value = null; page.value = 1; replay.value = 100; stopTour(); void load() })
onMounted(() => {
  void load()
  timer = window.setInterval(load, 45_000)
  document.addEventListener('fullscreenchange', onFullscreen)
})
onBeforeUnmount(() => {
  window.clearInterval(timer); window.clearInterval(playTimer); stopTour()
  document.removeEventListener('fullscreenchange', onFullscreen)
})

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
    analyses: p.analysis_ids.map((id) => ({ id, subject: `#${id}`, verdict: p.status === 'safe' ? 'legitimate' : p.status, created_at: p.last_seen })),
    extra: [{ label: 'IP', value: p.ip ?? '—' }, { label: 'ASN', value: p.asn ?? '—' }],
  }))
})

// ---- replay: show only what had appeared by the chosen moment of the period
const replay = ref(100)
const playing = ref(false)
let playTimer: number | undefined
function togglePlay() {
  playing.value = !playing.value
  window.clearInterval(playTimer)
  if (!playing.value) return
  if (replay.value >= 100) replay.value = 0
  playTimer = window.setInterval(() => {
    replay.value = Math.min(100, replay.value + 1.5)
    if (replay.value >= 100) { playing.value = false; window.clearInterval(playTimer) }
  }, 110)
}
const cutoff = computed(() => Date.now() - days.value * 86400_000 * (1 - replay.value / 100))
const cutoffLabel = computed(() => new Date(cutoff.value).toLocaleDateString(undefined, { day: '2-digit', month: 'short' }))
const utc = (s: string | null) => (s ? new Date(s + (/[zZ]|[+-]\d\d:?\d\d$/.test(s) ? '' : 'Z')).getTime() : 0)

const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  return items.value.filter((i) => {
    if (verdictFilter.value && i.tone !== toneOf(verdictFilter.value)) return false
    if (replay.value < 100 && i.first && utc(i.first) > cutoff.value) return false
    if (!needle) return true
    return [i.title, i.subtitle, i.isp, i.country, ...i.flags].some((v) => v?.toLowerCase().includes(needle))
  })
})
const visible = computed(() => filtered.value.slice(0, page.value * PER_PAGE))
watch([q, verdictFilter], () => { page.value = 1 })

const mapPoints = computed<MapPoint[]>(() => filtered.value.map((i) => ({
  id: i.id, lat: i.lat, lon: i.lon, count: i.count, tone: i.tone, label: `${flagHtml(i.cc)}${i.title} · <b>${i.count}</b>`,
})))
const selected = computed(() => items.value.find((i) => i.id === selectedId.value) ?? null)
const routes = computed(() => (layer.value === 'origins' && selectedId.value
  ? (origins.value?.points.find((p) => p.id === selectedId.value)?.routes ?? []) : []))
const circles = computed(() => (selected.value && layer.value === 'origins' && selected.value.accuracy
  ? [{ lat: selected.value.lat, lon: selected.value.lon, radiusKm: selected.value.accuracy, tone: selected.value.tone }] : []))

const stats = computed(() => {
  const list = filtered.value
  return {
    places: list.length,
    messages: list.reduce((n, i) => n + i.count, 0),
    critical: list.filter((i) => i.tone === 'danger').reduce((n, i) => n + i.count, 0),
    countries: new Set(list.map((i) => i.country).filter(Boolean)).size,
    hidden: layer.value === 'origins' ? origins.value?.hidden ?? 0 : links.value?.unlocated.length ?? 0,
  }
})

// Country leaderboard
const leaderboard = computed(() => {
  const by = new Map<string, { name: string; cc: string | null; n: number }>()
  for (const i of filtered.value) {
    const key = i.country ?? '?'
    by.set(key, { name: key, cc: i.cc, n: (by.get(key)?.n ?? 0) + i.count })
  }
  const rows = [...by.values()].sort((a, b) => b.n - a.n).slice(0, 5)
  const max = rows[0]?.n ?? 1
  return rows.map((r) => ({ ...r, pct: Math.round((r.n / max) * 100) }))
})

// Live feed: latest events across all places
const feed = computed<Event[]>(() => filtered.value
  .flatMap((i) => i.analyses.map((a) => ({ ...a, place: i.title, cc: i.cc, itemId: i.id })))
  .sort((a, b) => utc(b.created_at) - utc(a.created_at))
  .slice(0, 4))

// ---- auto tour of the hotspots
const touring = ref(false)
let tourTimer: number | undefined
let tourIndex = 0
function stopTour() { touring.value = false; window.clearInterval(tourTimer) }
function toggleTour() {
  if (touring.value) return stopTour()
  const spots = [...filtered.value].sort((a, b) => b.count - a.count).slice(0, 8)
  if (!spots.length) return
  touring.value = true
  tourIndex = 0
  const step = () => { selectedId.value = spots[tourIndex % spots.length]!.id; tourIndex++ }
  step()
  tourTimer = window.setInterval(step, 5000)
}
function pick(id: string) { stopTour(); selectedId.value = id }
function closeDetail() { selectedId.value = null; mapRef.value?.fitAll() }

// ---- full screen
function onFullscreen() { fullscreen.value = document.fullscreenElement === shell.value; setTimeout(() => mapRef.value?.invalidate(), 200) }
async function toggleFullscreen() {
  if (document.fullscreenElement) await document.exitFullscreen()
  else await shell.value?.requestFullscreen?.()
}

function openAnalysis(id: number) {
  if (layer.value === 'origins') investigate.value = id
  else emit('open', id)
}
const FLAG_ICON: Record<string, IconName> = {
  datacenter: 'cpu', proxy: 'lock', blacklisted: 'ban', scripted: 'zap', foreign_for_local_brand: 'globe', timezone_mismatch: 'clock', long_delay: 'clock',
}
const mapHeight = computed(() => (fullscreen.value ? '100vh' : props.height))
</script>

<template>
  <section ref="shell" class="radar-shell" :class="{ 'is-full': fullscreen }">
    <div class="grid" :class="compact || fullscreen ? '' : 'xl:grid-cols-[1fr_21rem]'">
      <!-- ===== Map with glass HUD ===== -->
      <GeoMap ref="mapRef" :points="mapPoints" :routes="routes" :circles="circles" :mode="mode" theme="dark" :basemap="basemap"
              :selected-id="selectedId" :height="mapHeight" :target="TARGET" :arcs="arcs && mode === 'cluster'" sweep
              @select="pick">
        <!-- Top-left: title + layers -->
        <div class="hud top-left">
          <div class="flex items-center gap-2.5">
            <span class="live-dot"></span>
            <div>
              <h2 class="text-sm font-bold tracking-wide text-white">{{ t('geo.radar.title') }}</h2>
              <p class="text-[10px] text-cyan-200/70">{{ t(`geo.radar.sub.${layer}`) }}</p>
            </div>
          </div>
          <div class="seg mt-2.5">
            <button v-for="l in (['origins', 'links'] as const)" :key="l" :class="{ on: layer === l }" @click="layer = l">
              <AppIcon :name="l === 'origins' ? 'mail' : 'link'" :size="12" /> {{ t(`geo.radar.layer.${l}`) }}
            </button>
          </div>
        </div>

        <!-- Top-right: controls -->
        <div class="hud top-right">
          <div class="seg">
            <button v-for="d in [7, 30, 90]" :key="d" :class="{ on: days === d }" @click="days = d">{{ d }}{{ t('geo.radar.d') }}</button>
          </div>
          <div class="seg">
            <button :class="{ on: mode === 'cluster' }" :title="t('geo.radar.cluster')" :aria-label="t('geo.radar.cluster')" @click="mode = 'cluster'"><AppIcon name="target" :size="13" /></button>
            <button :class="{ on: mode === 'heat' }" :title="t('geo.radar.heat')" :aria-label="t('geo.radar.heat')" @click="mode = 'heat'"><AppIcon name="zap" :size="13" /></button>
            <button :class="{ on: arcs }" :title="t('geo.radar.arcs')" :aria-label="t('geo.radar.arcs')" @click="arcs = !arcs"><AppIcon name="share" :size="13" /></button>
            <button :class="{ on: basemap === 'satellite' }" :title="t('geo.radar.satellite')" :aria-label="t('geo.radar.satellite')" @click="basemap = basemap === 'map' ? 'satellite' : 'map'"><AppIcon name="globe" :size="13" /></button>
            <button :class="{ on: touring }" :title="t('geo.radar.tour')" :aria-label="t('geo.radar.tour')" @click="toggleTour"><AppIcon name="radar" :size="13" /></button>
            <button :class="{ on: !hud }" :title="t('geo.radar.cleanMap')" :aria-label="t('geo.radar.cleanMap')" @click="hud = !hud"><AppIcon name="eye" :size="13" /></button>
            <button :title="t('geo.radar.fullscreen')" :aria-label="t('geo.radar.fullscreen')" @click="toggleFullscreen"><AppIcon :name="fullscreen ? 'x' : 'scan'" :size="13" /></button>
          </div>
        </div>

        <!-- KPIs -->
        <div v-show="hud" class="hud kpis">
          <div class="kpi"><b>{{ stats.messages }}</b><span>{{ layer === 'origins' ? t('geo.radar.emails') : t('geo.radar.hits') }}</span></div>
          <div class="kpi danger"><b>{{ stats.critical }}</b><span>{{ t('geo.radar.critical') }}</span></div>
          <div class="kpi"><b>{{ stats.places }}</b><span>{{ t('geo.radar.places') }}</span></div>
          <div class="kpi"><b>{{ stats.countries }}</b><span>{{ t('geo.radar.countries') }}</span></div>
          <div class="kpi muted"><b>{{ stats.hidden }}</b><span>{{ layer === 'origins' ? t('geo.radar.hidden') : t('geo.radar.unlocated') }}</span></div>
        </div>

        <!-- Live feed -->
        <div v-if="feed.length && !compact" v-show="hud" class="hud feed">
          <p class="hud-title"><span class="live-dot small"></span>{{ t('geo.radar.liveFeed') }}</p>
          <TransitionGroup name="feed" tag="ul" class="space-y-1">
            <li v-for="e in feed" :key="`${e.itemId}-${e.id}`">
              <button class="feed-row" :class="{ fresh: freshIds.has(e.itemId) }" @click="pick(e.itemId)">
                <span class="h-1.5 w-1.5 shrink-0 rounded-full" :class="e.verdict === 'phishing' ? 'bg-rose-500 shadow-[0_0_6px_#f43f5e]' : e.verdict === 'suspicious' ? 'bg-amber-400' : 'bg-emerald-400'"></span>
                <span class="min-w-0 flex-1 truncate text-left"><CountryFlag :code="e.cc" :size="14" /> {{ e.place }}</span>
                <span class="shrink-0 text-slate-500">{{ timeAgo(e.created_at) }}</span>
              </button>
            </li>
          </TransitionGroup>
        </div>

        <!-- Country leaderboard -->
        <div v-if="leaderboard.length && !compact" v-show="hud" class="hud board">
          <p class="hud-title"><AppIcon name="trophy" :size="11" /> {{ t('geo.radar.topCountries') }}</p>
          <button v-for="c in leaderboard" :key="c.name" class="board-row" @click="q = c.name === '?' ? '' : c.name">
            <span class="flex w-24 items-center gap-1.5 truncate text-left"><CountryFlag :code="c.cc" :size="14" /> <span class="truncate">{{ c.name }}</span></span>
            <span class="bar"><i :style="{ width: c.pct + '%' }"></i></span>
            <b class="w-7 text-right tabular-nums">{{ c.n }}</b>
          </button>
        </div>

        <!-- Replay -->
        <div class="hud replay">
          <button class="play" :aria-label="t('geo.radar.play')" @click="togglePlay"><AppIcon :name="playing ? 'pause' : 'play'" :size="13" /></button>
          <input v-model.number="replay" type="range" min="0" max="100" step="0.5" class="flex-1 accent-cyan-400" :aria-label="t('geo.radar.replay')" />
          <span class="w-16 text-right text-[11px] font-semibold tabular-nums text-cyan-200">{{ replay >= 100 ? t('geo.radar.now') : cutoffLabel }}</span>
        </div>

        <!-- States -->
        <div v-if="loading" class="hud loading"><span class="h-3 w-3 animate-spin rounded-full border-2 border-cyan-400/30 border-t-cyan-400"></span>{{ t('common.loading') }}</div>
        <div v-if="!loading && !items.length" class="empty">
          <AppIcon name="radar" :size="30" class="mx-auto mb-2 text-cyan-300" />
          <p>{{ t(`geo.radar.empty.${layer}`) }}</p>
        </div>

        <!-- Detail card (floating, bottom-right in full screen / compact) -->
        <Transition name="card">
          <div v-if="selected && (compact || fullscreen)" class="hud float-detail">
            <div class="flex items-start gap-2">
              <CountryFlag :code="selected.cc" :size="22" class="mt-0.5" />
              <div class="min-w-0 flex-1"><p class="truncate text-sm font-semibold text-white">{{ selected.title }}</p><p class="truncate text-[11px] text-slate-400">{{ selected.subtitle }}</p></div>
              <button class="text-slate-500 hover:text-white" :aria-label="t('common.close')" @click="closeDetail"><AppIcon name="x" :size="14" /></button>
            </div>
            <p class="mt-1.5 text-[11px] text-slate-300">{{ selected.count }} {{ layer === 'origins' ? t('geo.radar.emails') : t('geo.radar.hits') }} · {{ selected.isp }}</p>
            <button v-if="selected.analyses[0]" class="mt-2 w-full rounded-lg bg-cyan-400 py-1.5 text-xs font-bold text-slate-900" @click="openAnalysis(selected.analyses[0].id)">{{ t('geo.inv.open') }}</button>
          </div>
        </Transition>
      </GeoMap>

      <!-- ===== Side panel ===== -->
      <aside v-if="!compact && !fullscreen" class="side" :style="{ maxHeight: mapHeight }">
        <Transition name="card" mode="out-in">
          <div v-if="selected" :key="selected.id" class="detail">
            <div class="flex items-start gap-2">
              <CountryFlag :code="selected.cc" :size="30" class="mt-0.5" />
              <div class="min-w-0 flex-1">
                <p class="truncate font-semibold text-white">{{ selected.title }}</p>
                <p class="truncate text-xs text-slate-400">{{ selected.subtitle }}</p>
              </div>
              <button class="rounded-md p-1 text-slate-500 hover:bg-slate-800 hover:text-white" :aria-label="t('common.close')" @click="closeDetail"><AppIcon name="x" :size="15" /></button>
            </div>
            <div class="mt-3 grid grid-cols-3 gap-1.5 text-center text-[10px]">
              <div class="cell"><b>{{ selected.count }}</b>{{ layer === 'origins' ? t('geo.radar.emails') : t('geo.radar.hits') }}</div>
              <div class="cell"><b>±{{ selected.accuracy ?? '?' }}</b>km</div>
              <div class="cell"><b class="truncate">{{ t(`geo.net.${selected.network ?? 'unknown'}`) }}</b>{{ t('geo.radar.network') }}</div>
            </div>
            <div v-if="selected.flags.length" class="mt-2 flex flex-wrap gap-1">
              <span v-for="f in selected.flags" :key="f" class="flagchip"><AppIcon :name="FLAG_ICON[f] ?? 'alert'" :size="10" /> {{ t(`geo.flagShort.${f}`) }}</span>
            </div>
            <dl class="mt-2 space-y-1 text-[11px]">
              <div v-for="e in selected.extra" :key="e.label"><dt class="text-slate-500">{{ e.label }}</dt><dd class="break-all font-mono text-slate-300">{{ e.value }}</dd></div>
            </dl>
            <p class="mt-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">{{ t('geo.radar.messages') }}</p>
            <ul class="mt-1 max-h-40 space-y-1 overflow-y-auto pr-1">
              <li v-for="a in selected.analyses" :key="a.id">
                <button class="msg" @click="openAnalysis(a.id)">
                  <span class="h-2 w-2 shrink-0 rounded-full" :class="a.verdict === 'phishing' ? 'bg-rose-500' : a.verdict === 'suspicious' ? 'bg-amber-400' : 'bg-emerald-400'"></span>
                  <span class="min-w-0 flex-1 truncate">{{ a.subject || t('ux.live.noSubject') }}</span>
                  <AppIcon :name="layer === 'origins' ? 'radar' : 'arrowRight'" :size="12" class="text-cyan-400" />
                </button>
              </li>
            </ul>
          </div>
        </Transition>

        <div class="flex items-center gap-2">
          <label class="search flex-1">
            <AppIcon name="search" :size="14" class="text-slate-500" />
            <input v-model="q" :placeholder="t('geo.radar.search')" class="w-full bg-transparent text-xs text-white outline-none placeholder:text-slate-500" />
            <button v-if="q" class="text-slate-500 hover:text-white" :aria-label="t('landing.analyzer.clear')" @click="q = ''"><AppIcon name="x" :size="12" /></button>
          </label>
          <select v-model="verdictFilter" class="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-xs text-slate-300" :aria-label="t('geo.radar.verdict')">
            <option value="">{{ t('common.all') }}</option>
            <option value="phishing">{{ t('analysis.verdict.phishing') }}</option>
            <option value="suspicious">{{ t('analysis.verdict.suspicious') }}</option>
            <option value="legitimate">{{ t('analysis.verdict.legitimate') }}</option>
          </select>
        </div>
        <ul class="list">
          <li v-for="(i, idx) in visible" :key="i.id" :style="{ animationDelay: `${Math.min(idx, 12) * 30}ms` }" class="list-item">
            <button class="row" :class="{ on: i.id === selectedId, fresh: freshIds.has(i.id) }" @click="pick(i.id)">
              <span class="rank">{{ idx + 1 }}</span>
              <span class="dot" :class="`tone-${i.tone}`"></span>
              <span class="min-w-0 flex-1 text-left">
                <span class="flex items-center gap-1.5 truncate text-xs font-semibold text-slate-100"><CountryFlag :code="i.cc" :size="14" /> <span class="truncate">{{ i.title }}</span></span>
                <span class="block truncate text-[10px] text-slate-500">{{ i.isp ?? i.subtitle }} · {{ timeAgo(i.last) }}</span>
              </span>
              <span class="count" :class="`c-${i.tone}`">{{ i.count }}</span>
            </button>
          </li>
          <li v-if="!filtered.length && items.length" class="p-3 text-center text-xs text-slate-500">{{ t('history.noResults') }}</li>
        </ul>
        <button v-if="visible.length < filtered.length" class="more" @click="page++">
          {{ t('geo.radar.more', { n: Math.min(PER_PAGE, filtered.length - visible.length), total: filtered.length }) }}
        </button>
        <p v-if="layer === 'origins' && origins?.hidden_by?.length" class="text-[10px] text-slate-500">
          <AppIcon name="eye" :size="11" class="inline" /> {{ t('geo.radar.hiddenBy', { list: origins.hidden_by.map((h) => `${h.provider} (${h.count})`).join(', ') }) }}
        </p>
      </aside>
    </div>

    <OriginInvestigation :analysis-id="investigate" @close="investigate = null" />
  </section>
</template>

<style scoped>
.radar-shell { position: relative; padding: 0.6rem; border-radius: 1.5rem; color: #e2e8f0;
  background: radial-gradient(120% 70% at 0% 0%, rgba(34, 211, 238, 0.1), transparent 55%), radial-gradient(80% 60% at 100% 100%, rgba(244, 63, 94, 0.08), transparent 60%), #020617;
  border: 1px solid rgba(34, 211, 238, 0.14); box-shadow: 0 30px 80px -40px rgba(34, 211, 238, 0.35); }
.radar-shell.is-full { padding: 0; border-radius: 0; border: 0; }
.radar-shell > .grid { gap: 0.6rem; }

/* HUD panels floating over the map */
.hud { position: absolute; z-index: 600; border-radius: 1rem; background: rgba(2, 6, 23, 0.72); border: 1px solid rgba(34, 211, 238, 0.18);
  backdrop-filter: blur(12px) saturate(1.3); -webkit-backdrop-filter: blur(12px) saturate(1.3); box-shadow: 0 12px 30px -16px rgba(0, 0, 0, 0.8); }
.hud-title { display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.45rem; font-size: 0.62rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #67e8f9; }
.top-left { left: 0.8rem; top: 0.8rem; padding: 0.7rem 0.8rem; }
.top-right { right: 0.8rem; top: 0.8rem; display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 0.4rem; padding: 0.4rem; background: transparent; border: 0; box-shadow: none; backdrop-filter: none; }
.top-right .seg { background: rgba(2, 6, 23, 0.72); backdrop-filter: blur(12px); }
.kpis { left: 0.8rem; top: 6.4rem; display: flex; gap: 0.2rem; padding: 0.35rem; }
.kpi { display: flex; min-width: 4.2rem; flex-direction: column; align-items: center; padding: 0.3rem 0.55rem; border-radius: 0.7rem; }
.kpi b { font-size: 1.15rem; line-height: 1.1; color: white; font-variant-numeric: tabular-nums; }
.kpi span { font-size: 0.58rem; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; white-space: nowrap; }
.kpi.danger b { color: #fb7185; text-shadow: 0 0 12px rgba(244, 63, 94, 0.6); }
.kpi.muted b { color: #94a3b8; }
.feed { left: 0.8rem; bottom: 4.2rem; width: 15.5rem; padding: 0.6rem; }
.feed-row { display: flex; width: 100%; align-items: center; gap: 0.45rem; padding: 0.3rem 0.4rem; border-radius: 0.5rem; font-size: 0.7rem; color: #cbd5e1; transition: background 0.2s ease; }
.feed-row:hover { background: rgba(34, 211, 238, 0.08); }
.feed-row.fresh { background: rgba(244, 63, 94, 0.14); }
.board { right: 0.8rem; top: 3.7rem; width: 14.5rem; padding: 0.6rem; }
.board-row { display: flex; width: 100%; align-items: center; gap: 0.45rem; padding: 0.2rem 0; font-size: 0.7rem; color: #cbd5e1; }
.board-row:hover { color: white; }
.bar { position: relative; flex: 1; height: 0.35rem; border-radius: 9999px; background: rgba(148, 163, 184, 0.15); overflow: hidden; }
.bar i { position: absolute; inset: 0 auto 0 0; border-radius: 9999px; background: linear-gradient(90deg, #22d3ee, #f43f5e); transition: width 0.6s ease; }
.replay { left: 50%; bottom: 0.8rem; transform: translateX(-50%); display: flex; width: min(34rem, calc(100% - 1.6rem)); align-items: center; gap: 0.6rem; padding: 0.4rem 0.7rem 0.4rem 0.4rem; border-radius: 9999px; }
.play { display: grid; place-items: center; width: 1.9rem; height: 1.9rem; border-radius: 9999px; color: #0f172a; background: #22d3ee; box-shadow: 0 0 14px rgba(34, 211, 238, 0.6); }
.loading { right: 0.8rem; top: 3.7rem; display: flex; align-items: center; gap: 0.4rem; padding: 0.3rem 0.7rem; font-size: 0.7rem; }
.empty { position: absolute; inset: 0; z-index: 550; display: grid; place-content: center; padding: 2rem; text-align: center; font-size: 0.85rem; color: #cbd5e1; pointer-events: none; }
.empty p { max-width: 22rem; }
.float-detail { right: 0.8rem; top: 50%; transform: translateY(-50%); width: 15rem; padding: 0.8rem; }
.live-dot { position: relative; width: 0.6rem; height: 0.6rem; border-radius: 9999px; background: #22d3ee; box-shadow: 0 0 10px #22d3ee; }
.live-dot::after { content: ''; position: absolute; inset: 0; border-radius: 9999px; border: 2px solid #22d3ee; animation: live 1.8s ease-out infinite; }
.live-dot.small { width: 0.4rem; height: 0.4rem; }
@keyframes live { to { transform: scale(2.6); opacity: 0; } }

.seg { display: flex; gap: 2px; padding: 3px; border-radius: 0.75rem; background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(34, 211, 238, 0.15); }
.seg button { display: inline-flex; align-items: center; gap: 0.3rem; padding: 0.3rem 0.55rem; border-radius: 0.55rem; font-size: 0.7rem; font-weight: 600; color: #94a3b8; transition: all 0.15s ease; }
.seg button:hover { color: white; }
.seg button.on { color: #0f172a; background: #22d3ee; box-shadow: 0 0 12px rgba(34, 211, 238, 0.45); }

/* Side panel */
.side { display: flex; min-height: 0; flex-direction: column; gap: 0.6rem; padding: 0.3rem; overflow: hidden; }
.side .detail { flex-shrink: 0; max-height: 55%; overflow-y: auto; }
.detail { padding: 0.9rem; border-radius: 1rem; background: linear-gradient(160deg, rgba(34, 211, 238, 0.12), rgba(15, 23, 42, 0.95) 55%); border: 1px solid rgba(34, 211, 238, 0.28); box-shadow: 0 0 30px -14px rgba(34, 211, 238, 0.6); }
.cell { display: flex; flex-direction: column; gap: 0.1rem; padding: 0.4rem 0.2rem; border-radius: 0.6rem; background: rgba(2, 6, 23, 0.7); color: #64748b; }
.cell b { color: white; font-size: 0.78rem; }
.flagchip { display: inline-flex; align-items: center; gap: 0.2rem; padding: 0.1rem 0.45rem; border-radius: 9999px; font-size: 0.62rem; color: #fda4af; background: rgba(136, 19, 55, 0.4); border: 1px solid rgba(244, 63, 94, 0.3); }
.msg { display: flex; width: 100%; align-items: center; gap: 0.5rem; padding: 0.4rem 0.55rem; border-radius: 0.55rem; background: rgba(2, 6, 23, 0.7); font-size: 0.72rem; color: #e2e8f0; text-align: left; }
.msg:hover { background: rgba(34, 211, 238, 0.1); }
.search { display: flex; align-items: center; gap: 0.4rem; padding: 0.45rem 0.6rem; border-radius: 0.75rem; background: rgba(15, 23, 42, 0.9); border: 1px solid #1e293b; }
.search:focus-within { border-color: rgba(34, 211, 238, 0.5); box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.1); }
.list { flex: 1; min-height: 6rem; overflow-y: auto; display: flex; flex-direction: column; gap: 0.2rem; padding-right: 0.2rem; }
.list-item { animation: rise 0.35s ease both; }
@keyframes rise { from { opacity: 0; transform: translateY(6px); } }
.row { display: flex; width: 100%; align-items: center; gap: 0.5rem; padding: 0.45rem 0.5rem; border-radius: 0.7rem; transition: background 0.15s ease, box-shadow 0.15s ease; }
.row:hover { background: rgba(15, 23, 42, 0.9); }
.row.on { background: rgba(34, 211, 238, 0.08); box-shadow: inset 2px 0 0 #22d3ee; }
.row.fresh { box-shadow: inset 2px 0 0 #f43f5e; background: rgba(244, 63, 94, 0.08); }
.rank { width: 1.1rem; font-size: 0.62rem; font-weight: 700; color: #475569; text-align: right; font-variant-numeric: tabular-nums; }
.dot { width: 0.55rem; height: 0.55rem; border-radius: 9999px; flex-shrink: 0; }
.tone-danger { background: #f43f5e; box-shadow: 0 0 8px #f43f5e; } .tone-warn { background: #f59e0b; box-shadow: 0 0 6px #f59e0b; } .tone-safe { background: #10b981; } .tone-info { background: #38bdf8; }
.count { min-width: 1.7rem; padding: 0.1rem 0.4rem; border-radius: 9999px; text-align: center; font-size: 0.68rem; font-weight: 800; color: #0f172a; background: #22d3ee; }
.count.c-danger { color: white; background: #e11d48; } .count.c-warn { background: #f59e0b; }
.more { padding: 0.45rem; border-radius: 0.7rem; font-size: 0.72rem; font-weight: 600; color: #22d3ee; border: 1px dashed rgba(34, 211, 238, 0.4); }
.more:hover { background: rgba(34, 211, 238, 0.06); }

.feed-enter-active { transition: all 0.4s ease; }
.feed-enter-from { opacity: 0; transform: translateX(-10px); }
.feed-move { transition: transform 0.4s ease; }
.card-enter-active, .card-leave-active { transition: all 0.25s ease; }
.card-enter-from, .card-leave-to { opacity: 0; transform: translateY(6px); }

@media (max-width: 900px) {
  .kpis { top: auto; bottom: 4.2rem; left: 0.8rem; transform: none; flex-wrap: wrap; max-width: calc(100% - 1.6rem); }
  .feed, .board { display: none; }
}
@media (max-width: 640px) {
  .top-left p { display: none; }
  .kpi { min-width: 3.4rem; }
}
@media (prefers-reduced-motion: reduce) { .live-dot::after, .list-item { animation: none; } }
</style>
