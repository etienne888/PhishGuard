<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { geoNaturalEarth1, geoPath } from 'd3-geo'
import { feature } from 'topojson-client'
import type { GeometryCollection, Topology } from 'topojson-specification'
import world from 'world-atlas/countries-110m.json'
import { adminOpsService, type ThreatMapData, type ThreatPoint } from '@/services/admin.service'
import { timeAgo } from '@/utils/risk'

/**
 * Live map of where malicious links are hosted (IP geolocation, city-level and
 * approximate), with animated attack paths towards Cameroon.
 */
const props = withDefaults(defineProps<{ refreshMs?: number; showTable?: boolean }>(), { refreshMs: 30_000, showTable: true })
const emit = defineEmits<{ open: [analysisId: number] }>()

const W = 960
const H = 470
const projection = geoNaturalEarth1().scale(172).translate([W / 2, H / 2 + 10])
const path = geoPath(projection)
const topology = world as unknown as Topology<{ countries: GeometryCollection }>
const countries = (feature(topology, topology.objects.countries) as unknown as { features: GeoJSON.Feature[] }).features
const countryPaths = countries.map((f, i) => ({ id: String(f.id ?? i), d: path(f) ?? '' }))

const data = ref<ThreatMapData | null>(null)
const days = ref(30)
const scope = ref<'threats' | 'all'>('threats')
const loading = ref(false)
const error = ref('')
const hovered = ref<ThreatPoint | null>(null)
const selected = ref<string | null>(null)
const newHosts = ref<Set<string>>(new Set())
const flash = ref<ThreatPoint | null>(null)
let timer: number | undefined
let flashTimer: number | undefined

const project = (lon: number, lat: number) => projection([lon, lat]) ?? [0, 0]
const target = computed(() => {
  const t = data.value?.target ?? { lat: 3.848, lon: 11.5021, label: 'Yaoundé' }
  const [x, y] = project(t.lon, t.lat)
  return { x, y, label: t.label }
})

const markers = computed(() => (data.value?.points ?? [])
  .filter((p) => p.lat !== undefined && p.lon !== undefined)
  .map((p, i) => {
    const [x, y] = project(p.lon!, p.lat!)
    const dx = target.value.x - x
    const dy = target.value.y - y
    const lift = Math.min(160, Math.hypot(dx, dy) * 0.35)
    const cx = (x + target.value.x) / 2
    const cy = (y + target.value.y) / 2 - lift
    return {
      ...p, x, y, delay: (i % 6) * 0.45,
      r: 4 + Math.min(8, Math.log2(p.count + 1) * 2.2),
      arc: `M${x},${y} Q${cx},${cy} ${target.value.x},${target.value.y}`,
    }
  }))

const totals = computed(() => {
  const pts = data.value?.points ?? []
  return {
    located: pts.length,
    hits: pts.reduce((n, p) => n + p.count, 0),
    countries: new Set(pts.map((p) => p.country)).size,
    unlocated: data.value?.unlocated.length ?? 0,
  }
})

async function load(retry = false) {
  loading.value = true
  error.value = ''
  const before = new Set(data.value?.points.map((p) => p.host) ?? [])
  try {
    const next = await adminOpsService.getThreatMap(days.value, scope.value, retry)
    const fresh = before.size ? next.points.filter((p) => !before.has(p.host)) : []
    data.value = next
    newHosts.value = new Set(fresh.map((p) => p.host))
    if (fresh.length) {
      flash.value = fresh[0] ?? null
      window.clearTimeout(flashTimer)
      flashTimer = window.setTimeout(() => (flash.value = null), 6000)
    }
  } catch {
    error.value = 'Impossible de charger la carte (vérifiez la connexion internet du serveur).'
  } finally {
    loading.value = false
  }
}

watch([days, scope], () => {
  data.value = null // new filter: don't announce every point as "new"
  void load()
})
onMounted(() => {
  void load()
  timer = window.setInterval(() => load(), props.refreshMs)
})
onBeforeUnmount(() => { window.clearInterval(timer); window.clearTimeout(flashTimer) })

function place(p: ThreatPoint) {
  return [p.city, p.country].filter(Boolean).join(', ') || 'Inconnu'
}
</script>

<template>
  <div class="threat-map">
    <div class="flex flex-wrap items-center gap-3 px-5 pt-4">
      <div>
        <h2 class="flex items-center gap-2 font-semibold text-white">
          <span class="relative flex h-2.5 w-2.5"><span class="absolute h-full w-full animate-ping rounded-full bg-red-500 opacity-75"></span><span class="relative h-2.5 w-2.5 rounded-full bg-red-500"></span></span>
          Carte des menaces en direct
        </h2>
        <p class="text-xs text-slate-400">Localisation des serveurs qui hébergent les liens malveillants détectés · géolocalisation IP (ville, approximative)</p>
      </div>
      <div class="ml-auto flex items-center gap-2 text-xs">
        <div class="flex rounded-lg border border-slate-700 p-0.5">
          <button v-for="s in [{ id: 'threats', label: 'Menaces' }, { id: 'all', label: 'Tous les liens' }] as const" :key="s.id"
                  class="rounded-md px-2.5 py-1" :class="scope === s.id ? 'bg-slate-700 text-white' : 'text-slate-400'" @click="scope = s.id">{{ s.label }}</button>
        </div>
        <select v-model.number="days" class="rounded-lg border border-slate-700 bg-slate-900 px-2 py-1.5 text-slate-200">
          <option :value="7">7 jours</option><option :value="30">30 jours</option><option :value="90">90 jours</option>
        </select>
        <button class="rounded-lg border border-slate-700 px-3 py-1.5 text-slate-200 hover:border-cyan-400" :disabled="loading"
                title="Re-vérifie aussi les domaines qui n'avaient pas pu être localisés" @click="load(true)">
          {{ loading ? 'Balayage…' : '↻ Balayer' }}
        </button>
      </div>
    </div>

    <!-- New threat banner -->
    <Transition name="flash">
      <div v-if="flash" class="mx-5 mt-3 flex items-center gap-3 rounded-xl border border-red-500/50 bg-red-500/15 px-4 py-2.5 text-sm text-red-100">
        <span class="text-lg">🚨</span>
        <span><b>Nouvelle menace localisée :</b> {{ flash.host }} — {{ place(flash) }}</span>
      </div>
    </Transition>

    <div class="relative mt-2">
      <svg :viewBox="`0 0 ${W} ${H}`" class="block w-full" role="img"
           :aria-label="`Carte : ${totals.located} serveurs malveillants localisés dans ${totals.countries} pays`">
        <defs>
          <radialGradient id="glow"><stop offset="0%" stop-color="#22d3ee" stop-opacity="0.35" /><stop offset="100%" stop-color="#22d3ee" stop-opacity="0" /></radialGradient>
          <linearGradient id="sweep" x1="0" x2="1"><stop offset="0%" stop-color="#22d3ee" stop-opacity="0" /><stop offset="100%" stop-color="#22d3ee" stop-opacity="0.18" /></linearGradient>
        </defs>

        <g class="countries"><path v-for="c in countryPaths" :key="c.id" :d="c.d" /></g>

        <!-- Attack paths -->
        <g>
          <path v-for="m in markers" :key="`arc-${m.host}`" :d="m.arc" class="arc" :class="[m.status, { hot: selected === m.host || hovered?.host === m.host }]"
                :style="{ animationDelay: `${m.delay}s` }" />
          <circle v-for="m in markers" :key="`bolt-${m.host}`" r="2.6" class="bolt" :class="m.status">
            <animateMotion :path="m.arc" :dur="`${2.4 + (m.delay % 1)}s`" :begin="`${m.delay}s`" repeatCount="indefinite" />
          </circle>
        </g>

        <!-- Target: Cameroon -->
        <g :transform="`translate(${target.x},${target.y})`">
          <circle r="46" fill="url(#glow)" />
          <circle r="6" class="ring" /><circle r="6" class="ring d2" /><circle r="6" class="ring d3" />
          <circle r="4.5" fill="#22d3ee" stroke="#0b1120" stroke-width="2" />
          <text y="-14" text-anchor="middle" class="label">🇨🇲 {{ target.label }}</text>
        </g>

        <!-- Threat origins -->
        <g v-for="m in markers" :key="m.host" :transform="`translate(${m.x},${m.y})`" class="origin" :class="{ fresh: newHosts.has(m.host) }"
           @mouseenter="hovered = m" @mouseleave="hovered = null" @click="selected = selected === m.host ? null : m.host">
          <circle :r="m.r * 2.4" class="pulse" :class="m.status" :style="{ animationDelay: `${m.delay}s` }" />
          <circle :r="m.r" class="dot" :class="m.status" />
          <circle :r="m.r + 10" fill="transparent" />
        </g>

        <rect class="scan" :width="W / 5" :height="H" fill="url(#sweep)" />
      </svg>

      <div v-if="hovered" class="pointer-events-none absolute left-4 top-4 rounded-xl border border-slate-700 bg-slate-950/90 px-3 py-2 text-xs text-slate-200 shadow-xl">
        <p class="font-semibold" :class="hovered.status === 'phishing' ? 'text-red-400' : 'text-amber-400'">{{ hovered.host }}</p>
        <p>📍 {{ place(hovered) }}</p>
        <p class="text-slate-400">{{ hovered.ip }} · {{ hovered.isp }} {{ hovered.asn }}</p>
        <p>{{ hovered.count }} détection(s) · score max {{ hovered.max_score }}</p>
      </div>

      <div class="absolute bottom-3 left-4 flex flex-wrap gap-3 text-[11px] text-slate-300">
        <span class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-[#f25555]"></span>Dangereux</span>
        <span class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-[#e0950a]"></span>Suspect</span>
        <span v-if="scope === 'all'" class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-[#12a877]"></span>Sans danger</span>
        <span class="flex items-center gap-1.5"><span class="h-2.5 w-2.5 rounded-full bg-cyan-400"></span>Cible : Cameroun</span>
      </div>
      <p v-if="data && !markers.length" class="absolute inset-0 grid place-items-center text-sm text-slate-400">
        Aucun serveur malveillant localisé sur cette période.
      </p>
    </div>

    <!-- Totals -->
    <div class="grid grid-cols-2 gap-px border-t border-slate-800 bg-slate-800 text-center sm:grid-cols-4">
      <div class="stat"><b>{{ totals.located }}</b><span>serveurs localisés</span></div>
      <div class="stat"><b>{{ totals.countries }}</b><span>pays d'hébergement</span></div>
      <div class="stat"><b>{{ totals.hits }}</b><span>détections</span></div>
      <div class="stat"><b>{{ totals.unlocated }}</b><span>domaines hors ligne / non localisés</span></div>
    </div>
    <p v-if="data && totals.unlocated" class="px-5 pt-3 text-[11px] text-slate-500">
      Un domaine « hors ligne » n'a plus d'adresse IP (site fermé, domaine inventé ou expiré) : il reste listé ci-dessous mais ne peut pas être placé sur la carte.
      {{ data.analyses_scanned }} analyses examinées.
    </p>
    <p v-if="error" class="px-5 py-3 text-sm text-red-300">{{ error }}</p>

    <!-- Results -->
    <div v-if="showTable && data" class="overflow-x-auto border-t border-slate-800">
      <table class="w-full text-left text-xs text-slate-300">
        <thead class="text-[11px] uppercase tracking-wide text-slate-500">
          <tr><th class="px-5 py-2.5">Domaine</th><th class="px-3">Localisation</th><th class="hidden px-3 md:table-cell">IP · Hébergeur</th><th class="px-3 text-right">Détections</th><th class="px-3 text-right">Score max</th><th class="hidden px-3 sm:table-cell">Vu</th><th class="px-5"></th></tr>
        </thead>
        <tbody class="divide-y divide-slate-800">
          <tr v-for="p in [...data.points, ...data.unlocated]" :key="p.host" class="transition hover:bg-slate-800/60"
              :class="{ 'bg-cyan-500/10': selected === p.host, fresh: newHosts.has(p.host) }" @mouseenter="p.lat !== undefined && (hovered = p)" @mouseleave="hovered = null">
            <td class="px-5 py-2.5"><span class="mr-1.5 inline-block h-2 w-2 rounded-full" :class="p.status === 'phishing' ? 'bg-[#f25555]' : 'bg-[#e0950a]'"></span><code>{{ p.host }}</code></td>
            <td class="px-3">{{ p.lat !== undefined ? `📍 ${place(p)}` : '— hors ligne' }}</td>
            <td class="hidden px-3 text-slate-400 md:table-cell">{{ p.ip ?? '—' }}<template v-if="p.isp"> · {{ p.isp }}</template></td>
            <td class="px-3 text-right tabular-nums">{{ p.count }}</td>
            <td class="px-3 text-right tabular-nums" :class="p.max_score > 60 ? 'text-red-400' : 'text-amber-400'">{{ p.max_score }}</td>
            <td class="hidden px-3 text-slate-400 sm:table-cell">{{ timeAgo(p.last_seen) }}</td>
            <td class="px-5 text-right"><button v-if="p.analysis_ids[0]" class="text-cyan-400 hover:underline" @click="emit('open', p.analysis_ids[0])">Voir →</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.threat-map { border-radius: 1rem; overflow: hidden; background: radial-gradient(ellipse at 55% 45%, #0c2536 0%, #070d1a 70%); border: 1px solid #1e293b; }
.countries path { fill: #13233a; stroke: #1f3b5a; stroke-width: 0.5; }
.label { fill: #a5f3fc; font-size: 11px; font-weight: 600; }
.arc { fill: none; stroke-width: 1.3; stroke-dasharray: 5 7; opacity: 0.55; animation: travel 1.6s linear infinite; }
.arc.phishing { stroke: #f25555; }
.arc.suspicious { stroke: #e0950a; }
.arc.safe { stroke: #12a877; opacity: 0.25; animation: none; }
.bolt.safe { display: none; }
.dot.safe { fill: #12a877; }
.pulse.safe { stroke: #12a877; animation: none; opacity: 0; }
.arc.hot { stroke-width: 2.4; opacity: 1; }
.bolt.phishing { fill: #fecaca; filter: drop-shadow(0 0 4px #f25555); }
.bolt.suspicious { fill: #fde68a; filter: drop-shadow(0 0 4px #e0950a); }
.dot { stroke: #070d1a; stroke-width: 1.5; }
.dot.phishing { fill: #f25555; }
.dot.suspicious { fill: #e0950a; }
.pulse { fill: none; stroke-width: 1.5; transform-box: fill-box; transform-origin: center; animation: pulse 2.2s ease-out infinite; }
.pulse.phishing { stroke: #f25555; }
.pulse.suspicious { stroke: #e0950a; }
.origin { cursor: pointer; }
.origin.fresh .dot { animation: impact 0.9s ease-out 4; transform-box: fill-box; transform-origin: center; }
.ring { fill: none; stroke: #22d3ee; stroke-width: 1.4; transform-box: fill-box; transform-origin: center; animation: radar 2.6s ease-out infinite; }
.ring.d2 { animation-delay: 0.85s; }
.ring.d3 { animation-delay: 1.7s; }
.scan { animation: scan 7s linear infinite; }
.stat { display: flex; flex-direction: column; gap: 2px; padding: 0.75rem; background: #0a1322; }
.stat b { font-size: 1.25rem; color: white; font-variant-numeric: tabular-nums; }
.stat span { font-size: 11px; color: #94a3b8; }
tr.fresh { animation: rowflash 2.5s ease-out; }
.flash-enter-active, .flash-leave-active { transition: all 0.3s ease; }
.flash-enter-from, .flash-leave-to { opacity: 0; transform: translateY(-6px); }
@keyframes travel { to { stroke-dashoffset: -24; } }
@keyframes pulse { from { transform: scale(0.4); opacity: 0.9; } to { transform: scale(1.3); opacity: 0; } }
@keyframes radar { from { transform: scale(1); opacity: 0.9; } to { transform: scale(7); opacity: 0; } }
@keyframes impact { 50% { transform: scale(2.2); } }
@keyframes scan { from { transform: translateX(-200px); } to { transform: translateX(1000px); } }
@keyframes rowflash { from { background: rgba(239, 68, 68, 0.25); } to { background: transparent; } }
@media (prefers-reduced-motion: reduce) {
  .arc, .pulse, .ring, .scan, .origin.fresh .dot, tr.fresh { animation: none; }
  .bolt { display: none; }
}
</style>
