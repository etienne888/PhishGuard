<script setup lang="ts">
/**
 * Reusable Leaflet map (OpenStreetMap / CARTO tiles, Esri satellite - free, no API key).
 *   mode 'cluster'  markers grouped into glowing bubbles that split when zooming in
 *   mode 'heat'     heatmap of activity
 *   target + arcs   curved "attack arcs" from every point to the target (Yaoundé),
 *                   with light particles travelling along the busiest ones
 *   routes          animated lines (email path: sender -> relays -> recipient)
 *   circles         honest accuracy areas of IP locations
 *   sweep           rotating radar sweep over the map (decorative)
 * Leaflet objects are kept outside Vue reactivity (plain variables).
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'

export type Tone = 'danger' | 'warn' | 'safe' | 'info'
export interface MapPoint { id: string; lat: number; lon: number; count?: number; tone?: Tone; label?: string }
export interface MapCircle { lat: number; lon: number; radiusKm: number; tone?: Tone }
export interface RoutePoint { lat: number; lon: number; kind?: string; label?: string }
export interface MapTarget { lat: number; lon: number; label: string }

const props = withDefaults(defineProps<{
  points?: MapPoint[]
  circles?: MapCircle[]
  routes?: RoutePoint[][]
  mode?: 'cluster' | 'heat' | 'plain'
  theme?: 'dark' | 'light'
  basemap?: 'map' | 'satellite'
  selectedId?: string | null
  height?: string
  interactive?: boolean
  center?: [number, number]
  zoom?: number
  target?: MapTarget | null
  arcs?: boolean
  sweep?: boolean
}>(), {
  points: () => [], circles: () => [], routes: () => [], mode: 'cluster', theme: 'light', basemap: 'map',
  selectedId: null, height: '420px', interactive: true, zoom: 3, target: null, arcs: false, sweep: false,
})
const emit = defineEmits<{ select: [id: string] }>()

const el = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let tiles: L.TileLayer | null = null
let labels: L.TileLayer | null = null
let dataLayer: L.Layer | null = null
let overlay: L.LayerGroup | null = null
let arcLayer: L.LayerGroup | null = null
let pluginsReady: Promise<void> | null = null
let particles: Array<{ marker: L.Marker; path: [number, number][]; t: number; speed: number }> = []
let raf = 0

const TONE: Record<Tone, string> = { danger: '#f43f5e', warn: '#f59e0b', safe: '#10b981', info: '#38bdf8' }
const RANK: Record<Tone, number> = { info: 0, safe: 1, warn: 2, danger: 3 }
const reduceMotion = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

// Keyless tile services (CARTO basemaps now require an API key)
const ESRI = 'https://server.arcgisonline.com/ArcGIS/rest/services'
const TILES = {
  dark: `${ESRI}/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}`,
  darkLabels: `${ESRI}/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}`,
  light: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  satellite: `${ESRI}/World_Imagery/MapServer/tile/{z}/{y}/{x}`,
}
const ATTRIBUTION = {
  dark: 'Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  light: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  satellite: 'Tiles &copy; Esri &mdash; Esri, Maxar, Earthstar Geographics',
}

function loadPlugins() {
  // The two plugins extend the global `L`: expose it before loading them
  pluginsReady ??= (async () => {
    ;(window as unknown as { L: typeof L }).L = L
    await import('leaflet.markercluster')
    await import('leaflet.heat')
  })()
  return pluginsReady
}

function markerIcon(p: MapPoint, selected: boolean) {
  const tone = TONE[p.tone ?? 'info']
  const size = Math.round(16 + Math.min(18, Math.log2((p.count ?? 1) + 1) * 4.5))
  return L.divIcon({
    className: 'pg-marker-wrap',
    iconSize: [size, size],
    html: `<span class="pg-marker${selected ? ' is-selected' : ''}" style="--c:${tone};--s:${size}px">`
      + `<i class="pg-ring"></i><i class="pg-ring r2"></i>`
      + `<em>${(p.count ?? 1) > 1 ? p.count : ''}</em></span>`,
  })
}

function targetIcon(label: string) {
  return L.divIcon({
    className: 'pg-marker-wrap', iconSize: [44, 44],
    html: `<span class="pg-target"><i></i><i></i><i></i><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v6c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6l7-3zM9 12l2 2 4-4"/></svg><b>${label}</b></span>`,
  })
}

/** Curved arc between two points (quadratic Bézier in lat/lon space, bulging "north"). */
function arcPath(a: [number, number], b: [number, number], steps = 48): [number, number][] {
  const [lat1, lon1] = a
  const [lat2, lon2] = b
  const dist = Math.hypot(lat2 - lat1, lon2 - lon1)
  const cLat = (lat1 + lat2) / 2 + Math.min(28, dist * 0.32)
  const cLon = (lon1 + lon2) / 2
  const out: [number, number][] = []
  for (let i = 0; i <= steps; i++) {
    const t = i / steps
    const u = 1 - t
    out.push([u * u * lat1 + 2 * u * t * cLat + t * t * lat2, u * u * lon1 + 2 * u * t * cLon + t * t * lon2])
  }
  return out
}

function setTiles() {
  if (!map) return
  tiles?.remove()
  labels?.remove()
  labels = null
  if (props.basemap === 'satellite') {
    tiles = L.tileLayer(TILES.satellite, { attribution: ATTRIBUTION.satellite, maxZoom: 18 }).addTo(map)
  } else if (props.theme === 'dark') {
    tiles = L.tileLayer(TILES.dark, { attribution: ATTRIBUTION.dark, maxZoom: 16, className: 'pg-dark-tiles' }).addTo(map)
    labels = L.tileLayer(TILES.darkLabels, { maxZoom: 16, pane: 'shadowPane', opacity: 0.7 }).addTo(map)
  } else {
    tiles = L.tileLayer(TILES.light, { attribution: ATTRIBUTION.light, maxZoom: 19 }).addTo(map)
  }
}

function stopParticles() {
  cancelAnimationFrame(raf)
  particles = []
}

function animate() {
  for (const p of particles) {
    p.t = (p.t + p.speed) % 1
    const idx = Math.floor(p.t * (p.path.length - 1))
    p.marker.setLatLng(p.path[idx]!)
  }
  raf = requestAnimationFrame(animate)
}

function drawArcs() {
  arcLayer?.remove()
  stopParticles()
  if (!map || !props.arcs || !props.target) return
  arcLayer = L.layerGroup().addTo(map)
  const target: [number, number] = [props.target.lat, props.target.lon]
  const busiest = [...props.points].sort((a, b) => (b.count ?? 1) - (a.count ?? 1)).slice(0, 40)
  busiest.forEach((p, i) => {
    const far = Math.hypot(p.lat - target[0], p.lon - target[1]) > 0.8
    if (!far) return
    const path = arcPath([p.lat, p.lon], target)
    const color = TONE[p.tone ?? 'info']
    L.polyline(path, { color, weight: 6, opacity: 0.08, interactive: false }).addTo(arcLayer!)
    L.polyline(path, { color, weight: 1.6, opacity: 0.75, className: 'pg-arc', interactive: false }).addTo(arcLayer!)
    if (!reduceMotion && i < 18) {
      const marker = L.marker(path[0]!, {
        interactive: false, keyboard: false,
        icon: L.divIcon({ className: 'pg-marker-wrap', iconSize: [8, 8], html: `<span class="pg-particle" style="--c:${color}"></span>` }),
      }).addTo(arcLayer!)
      particles.push({ marker, path, t: (i * 0.137) % 1, speed: 0.0035 + Math.min(0.004, (p.count ?? 1) * 0.0004) })
    }
  })
  L.marker(target, { icon: targetIcon(props.target.label), interactive: false, zIndexOffset: 1000 }).addTo(arcLayer)
  if (particles.length) raf = requestAnimationFrame(animate)
}

async function draw(fit = false) {
  if (!map) return
  await loadPlugins()
  dataLayer?.remove()
  overlay?.remove()
  overlay = L.layerGroup().addTo(map)

  // Accuracy circles (under everything)
  for (const c of props.circles) {
    L.circle([c.lat, c.lon], {
      radius: c.radiusKm * 1000, color: TONE[c.tone ?? 'info'], weight: 1.5, fillOpacity: 0.12, dashArray: '4 4',
    }).addTo(overlay)
  }
  // Email routes: dashed animated polylines + small dots for each hop
  for (const route of props.routes) {
    if (route.length < 2) continue
    L.polyline(route.map((r) => [r.lat, r.lon] as [number, number]), {
      color: '#22d3ee', weight: 2.5, opacity: 0.9, className: 'pg-route',
    }).addTo(overlay)
    route.forEach((r, i) => L.circleMarker([r.lat, r.lon], {
      radius: i === 0 ? 6 : 4, color: i === 0 ? '#f43f5e' : '#22d3ee', weight: 2, fillOpacity: 0.9,
    }).bindTooltip(r.label ?? r.kind ?? '', { direction: 'top', className: 'pg-tip' }).addTo(overlay!))
  }

  if (props.mode === 'heat') {
    const heat = (L as unknown as { heatLayer: (pts: number[][], opts: object) => L.Layer }).heatLayer(
      props.points.map((p) => [p.lat, p.lon, Math.min(1, 0.3 + Math.log2((p.count ?? 1) + 1) / 5)]),
      { radius: 30, blur: 24, maxZoom: 10, gradient: { 0.25: '#1d4ed8', 0.5: '#22d3ee', 0.7: '#f59e0b', 0.9: '#f43f5e' } })
    dataLayer = heat.addTo(map)
  } else {
    const group = props.mode === 'cluster'
      ? (L as unknown as { markerClusterGroup: (o: object) => L.LayerGroup }).markerClusterGroup({
          showCoverageOnHover: false, maxClusterRadius: 50, spiderfyOnMaxZoom: true, animate: true,
          iconCreateFunction: (cluster: { getAllChildMarkers: () => Array<{ options: { pgPoint?: MapPoint } }> }) => {
            const children = cluster.getAllChildMarkers()
            const total = children.reduce((n, m) => n + (m.options.pgPoint?.count ?? 1), 0)
            const worst = children.reduce<Tone>((w, m) => {
              const tone = m.options.pgPoint?.tone ?? 'info'
              return RANK[tone] > RANK[w] ? tone : w
            }, 'info')
            const size = Math.round(38 + Math.min(28, Math.log2(total + 1) * 5))
            return L.divIcon({
              className: 'pg-marker-wrap', iconSize: [size, size],
              html: `<span class="pg-cluster" style="--c:${TONE[worst]};--s:${size}px"><i class="pg-ring"></i><b>${total}</b></span>`,
            })
          },
        })
      : L.layerGroup()
    for (const p of props.points) {
      const marker = L.marker([p.lat, p.lon], { icon: markerIcon(p, p.id === props.selectedId), pgPoint: p, riseOnHover: true } as L.MarkerOptions)
      if (p.label) marker.bindTooltip(p.label, { direction: 'top', offset: [0, -10], className: 'pg-tip' })
      marker.on('click', () => emit('select', p.id))
      group.addLayer(marker)
    }
    dataLayer = group.addTo(map)
  }
  drawArcs()

  if (fit) {
    const coords: [number, number][] = [
      ...props.points.map((p) => [p.lat, p.lon] as [number, number]),
      ...props.circles.map((c) => [c.lat, c.lon] as [number, number]),
      ...props.routes.flat().map((r) => [r.lat, r.lon] as [number, number]),
      ...(props.arcs && props.target ? [[props.target.lat, props.target.lon] as [number, number]] : []),
    ]
    map.invalidateSize()
    if (coords.length === 1) map.setView(coords[0]!, props.circles.length ? 10 : 6)
    else if (coords.length > 1) map.fitBounds(L.latLngBounds(coords).pad(0.15), { maxZoom: 8, animate: false })
  }
}

function flyTo(id: string, zoom = 7) {
  const p = props.points.find((x) => x.id === id)
  if (p && map) map.flyTo([p.lat, p.lon], Math.max(map.getZoom(), zoom), { duration: 1.4 })
}

function fitAll() {
  if (!map) return
  const coords = props.points.map((p) => [p.lat, p.lon] as [number, number])
  if (props.target) coords.push([props.target.lat, props.target.lon])
  if (coords.length > 1) map.flyToBounds(L.latLngBounds(coords).pad(0.2), { maxZoom: 8, duration: 1.2 })
}

let resizeObserver: ResizeObserver | null = null
onMounted(() => {
  if (!el.value) return
  map = L.map(el.value, {
    center: props.center ?? [7.37, 12.35], zoom: props.zoom, worldCopyJump: true, zoomControl: false,
    dragging: props.interactive, scrollWheelZoom: false, attributionControl: true, zoomSnap: 0.25,
  })
  if (props.interactive) L.control.zoom({ position: 'bottomright' }).addTo(map)
  map.on('focus', () => map?.scrollWheelZoom.enable())
  map.on('blur', () => map?.scrollWheelZoom.disable())
  setTiles()
  // Wait for the final layout (flex/grid parents) before fitting the points
  requestAnimationFrame(() => { map?.invalidateSize(); void draw(true) })
  // Full screen / panel resize: let Leaflet recompute its size
  resizeObserver = new ResizeObserver(() => map?.invalidateSize())
  resizeObserver.observe(el.value)
})
onBeforeUnmount(() => { stopParticles(); resizeObserver?.disconnect(); map?.remove(); map = null })

watch(() => [props.theme, props.basemap], setTiles)
watch(() => [props.points, props.circles, props.routes, props.mode, props.arcs, props.target], () => void draw(true))
watch(() => props.selectedId, (id) => { void draw(false); if (id) flyTo(id) })

defineExpose({ flyTo, fitAll, invalidate: () => map?.invalidateSize() })
</script>

<template>
  <div class="pg-map-frame" :class="[`theme-${theme}`, { 'has-sweep': sweep && !reduceMotion }]" :style="{ height }">
    <div ref="el" class="pg-map" role="region" aria-label="Map"></div>
    <div v-if="theme === 'dark'" class="pg-vignette" aria-hidden="true"></div>
    <div v-if="sweep && !reduceMotion" class="pg-sweep" aria-hidden="true"></div>
    <slot />
  </div>
</template>

<style>
.pg-map-frame { position: relative; width: 100%; border-radius: 1.2rem; overflow: hidden; isolation: isolate; }
.pg-map { position: absolute; inset: 0; z-index: 0; }
.pg-map-frame.theme-dark { background: #060b18; }
.pg-map-frame.theme-dark .pg-map { background: #060b18; }
.pg-dark-tiles { filter: brightness(0.75) contrast(1.15) saturate(1.4) hue-rotate(185deg) sepia(0.25); }
.pg-vignette { position: absolute; inset: 0; z-index: 401; pointer-events: none;
  background: radial-gradient(ellipse at center, transparent 55%, rgba(2, 6, 23, 0.75) 100%),
              repeating-linear-gradient(0deg, rgba(34, 211, 238, 0.025) 0 1px, transparent 1px 4px); }
.pg-sweep { position: absolute; left: 50%; top: 50%; width: 180%; aspect-ratio: 1; z-index: 402; pointer-events: none;
  transform: translate(-50%, -50%); border-radius: 9999px;
  background: conic-gradient(from 0deg, rgba(34, 211, 238, 0.10) 0deg, rgba(34, 211, 238, 0.04) 18deg, rgba(34, 211, 238, 0) 42deg, transparent 360deg);
  -webkit-mask: radial-gradient(circle, #000 0, #000 35%, transparent 70%); mask: radial-gradient(circle, #000 0, #000 35%, transparent 70%);
  animation: pg-spin 7s linear infinite; mix-blend-mode: screen; }
@keyframes pg-spin { to { transform: translate(-50%, -50%) rotate(360deg); } }
.pg-map .leaflet-control-attribution { font-size: 9px; background: rgba(255, 255, 255, 0.6); }
.theme-dark .pg-map .leaflet-control-attribution { background: rgba(2, 6, 23, 0.55); color: #64748b; }
.theme-dark .pg-map .leaflet-control-attribution a { color: #67e8f9; }
.theme-dark .leaflet-control-zoom a { background: rgba(15, 23, 42, 0.85); color: #e2e8f0; border-color: #1e293b; backdrop-filter: blur(6px); }
.theme-dark .leaflet-control-zoom a:hover { background: #22d3ee; color: #0f172a; }
.pg-marker-wrap { background: none; border: 0; }

/* Markers: glowing core + two expanding rings */
.pg-marker { position: relative; display: grid; place-items: center; width: var(--s); height: var(--s); border-radius: 9999px;
  background: radial-gradient(circle at 35% 35%, color-mix(in srgb, var(--c) 45%, white), var(--c) 60%);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.85), 0 0 18px 2px color-mix(in srgb, var(--c) 70%, transparent);
  transition: transform 0.25s ease; }
.pg-marker em { position: relative; z-index: 1; font: 800 10px/1 system-ui, sans-serif; font-style: normal; color: white; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5); }
.pg-marker:hover { transform: scale(1.18); }
.pg-marker.is-selected { transform: scale(1.3); box-shadow: 0 0 0 3px white, 0 0 30px 6px var(--c); }
.pg-ring { position: absolute; inset: 0; border-radius: 9999px; border: 2px solid var(--c); opacity: 0; animation: pg-ring 2.4s ease-out infinite; }
.pg-ring.r2 { animation-delay: 1.2s; }
@keyframes pg-ring { 0% { transform: scale(1); opacity: 0.7; } 100% { transform: scale(2.8); opacity: 0; } }

.pg-cluster { position: relative; display: grid; place-items: center; width: var(--s); height: var(--s); border-radius: 9999px;
  background: radial-gradient(circle, color-mix(in srgb, var(--c) 92%, white) 0 42%, color-mix(in srgb, var(--c) 30%, transparent) 43% 70%, transparent 71%);
  box-shadow: 0 0 28px -2px var(--c); }
.pg-cluster b { position: relative; z-index: 1; font: 800 12px/1 system-ui, sans-serif; color: white; }

/* Target (Yaoundé): shield + three sonar rings */
.pg-target { position: relative; display: grid; place-items: center; width: 44px; height: 44px; border-radius: 9999px; color: #0f172a;
  background: radial-gradient(circle, #67e8f9, #22d3ee 60%); box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.9), 0 0 36px 8px rgba(34, 211, 238, 0.6); }
.pg-target svg { position: relative; z-index: 1; }
.pg-target i { position: absolute; inset: 0; border-radius: 9999px; border: 2px solid #22d3ee; animation: pg-ring 3s ease-out infinite; }
.pg-target i:nth-child(2) { animation-delay: 1s; } .pg-target i:nth-child(3) { animation-delay: 2s; }
.pg-target b { position: absolute; top: 50px; left: 50%; transform: translateX(-50%); white-space: nowrap; padding: 2px 8px; border-radius: 9999px;
  font: 700 10px/1.4 system-ui, sans-serif; letter-spacing: 0.08em; text-transform: uppercase; color: #67e8f9; background: rgba(2, 6, 23, 0.8); border: 1px solid rgba(34, 211, 238, 0.4); }

.pg-arc { stroke-dasharray: 3 7; animation: pg-dash 1.6s linear infinite; }
.pg-route { stroke-dasharray: 8 10; animation: pg-dash 1.2s linear infinite; filter: drop-shadow(0 0 4px #22d3ee); }
@keyframes pg-dash { to { stroke-dashoffset: -20; } }
.pg-particle { display: block; width: 8px; height: 8px; border-radius: 9999px; background: white; box-shadow: 0 0 6px 2px var(--c), 0 0 14px 4px var(--c); }

.pg-tip { padding: 4px 9px; border-radius: 8px; font: 600 11px/1.4 system-ui, sans-serif; color: #e2e8f0; background: rgba(2, 6, 23, 0.9); border: 1px solid rgba(34, 211, 238, 0.35); box-shadow: 0 8px 20px -8px rgba(0, 0, 0, 0.6); }
.pg-tip::before { display: none; }
.theme-light .pg-tip { color: #0f172a; background: white; border-color: #e2e8f0; }
@media (prefers-reduced-motion: reduce) { .pg-ring, .pg-arc, .pg-route, .pg-target i { animation: none; } }
</style>
