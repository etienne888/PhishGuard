<script setup lang="ts">
/**
 * Reusable Leaflet map (OpenStreetMap / CARTO tiles, Esri satellite - free, no API key).
 *   mode 'cluster'  markers grouped into bubbles that split when zooming in
 *   mode 'heat'     heatmap of activity
 *   routes          animated lines (email path: sender -> relays -> recipient)
 *   circles         honest accuracy areas of IP locations
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
}>(), {
  points: () => [], circles: () => [], routes: () => [], mode: 'cluster', theme: 'light', basemap: 'map',
  selectedId: null, height: '420px', interactive: true, zoom: 3,
})
const emit = defineEmits<{ select: [id: string] }>()

const el = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let tiles: L.TileLayer | null = null
let dataLayer: L.Layer | null = null
let overlay: L.LayerGroup | null = null
let pluginsReady: Promise<void> | null = null

const TONE: Record<Tone, string> = { danger: '#ef4444', warn: '#f59e0b', safe: '#10b981', info: '#3b82f6' }
const RANK: Record<Tone, number> = { info: 0, safe: 1, warn: 2, danger: 3 }

const TILES = {
  dark: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
  light: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
  satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
}
const ATTRIBUTION = {
  map: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
  satellite: 'Tiles &copy; Esri',
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
  const size = Math.round(14 + Math.min(14, Math.log2((p.count ?? 1) + 1) * 4))
  return L.divIcon({
    className: 'pg-marker-wrap',
    iconSize: [size, size],
    html: `<span class="pg-marker${selected ? ' is-selected' : ''}" style="--c:${tone};width:${size}px;height:${size}px">`
      + `${(p.count ?? 1) > 1 ? `<b>${p.count}</b>` : ''}</span>`,
  })
}

function setTiles() {
  if (!map) return
  tiles?.remove()
  const url = props.basemap === 'satellite' ? TILES.satellite : TILES[props.theme]
  tiles = L.tileLayer(url, { attribution: ATTRIBUTION[props.basemap], maxZoom: 18, subdomains: 'abcd' }).addTo(map)
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
  // Routes: dashed animated polylines + small dots for each hop
  for (const route of props.routes) {
    if (route.length < 2) continue
    L.polyline(route.map((r) => [r.lat, r.lon] as [number, number]), {
      color: '#22d3ee', weight: 2.5, opacity: 0.9, className: 'pg-route',
    }).addTo(overlay)
    route.forEach((r, i) => L.circleMarker([r.lat, r.lon], {
      radius: i === 0 ? 6 : 4, color: i === 0 ? '#ef4444' : '#22d3ee', weight: 2, fillOpacity: 0.9,
    }).bindTooltip(r.label ?? r.kind ?? '', { direction: 'top' }).addTo(overlay!))
  }

  if (props.mode === 'heat') {
    const heat = (L as unknown as { heatLayer: (pts: number[][], opts: object) => L.Layer }).heatLayer(
      props.points.map((p) => [p.lat, p.lon, Math.min(1, 0.25 + Math.log2((p.count ?? 1) + 1) / 5)]),
      { radius: 28, blur: 22, maxZoom: 10, gradient: { 0.3: '#3b82f6', 0.55: '#f59e0b', 0.8: '#ef4444' } })
    dataLayer = heat.addTo(map)
  } else {
    const group = props.mode === 'cluster'
      ? (L as unknown as { markerClusterGroup: (o: object) => L.LayerGroup }).markerClusterGroup({
          showCoverageOnHover: false, maxClusterRadius: 48, spiderfyOnMaxZoom: true,
          iconCreateFunction: (cluster: { getAllChildMarkers: () => Array<{ options: { pgPoint?: MapPoint } }> }) => {
            const children = cluster.getAllChildMarkers()
            const total = children.reduce((n, m) => n + (m.options.pgPoint?.count ?? 1), 0)
            const worst = children.reduce<Tone>((w, m) => {
              const tone = m.options.pgPoint?.tone ?? 'info'
              return RANK[tone] > RANK[w] ? tone : w
            }, 'info')
            const size = Math.round(34 + Math.min(26, Math.log2(total + 1) * 5))
            return L.divIcon({
              className: 'pg-marker-wrap', iconSize: [size, size],
              html: `<span class="pg-cluster" style="--c:${TONE[worst]};width:${size}px;height:${size}px"><b>${total}</b></span>`,
            })
          },
        })
      : L.layerGroup()
    for (const p of props.points) {
      const marker = L.marker([p.lat, p.lon], { icon: markerIcon(p, p.id === props.selectedId), pgPoint: p } as L.MarkerOptions)
      if (p.label) marker.bindTooltip(p.label, { direction: 'top', offset: [0, -8] })
      marker.on('click', () => emit('select', p.id))
      group.addLayer(marker)
    }
    dataLayer = group.addTo(map)
  }

  if (fit) {
    const coords: [number, number][] = [
      ...props.points.map((p) => [p.lat, p.lon] as [number, number]),
      ...props.circles.map((c) => [c.lat, c.lon] as [number, number]),
      ...props.routes.flat().map((r) => [r.lat, r.lon] as [number, number]),
    ]
    if (coords.length === 1) map.setView(coords[0]!, props.circles.length ? 10 : 6)
    else if (coords.length > 1) map.fitBounds(L.latLngBounds(coords).pad(0.25), { maxZoom: 9 })
  }
}

function flyToSelected() {
  const p = props.points.find((x) => x.id === props.selectedId)
  if (p && map) map.flyTo([p.lat, p.lon], Math.max(map.getZoom(), 7), { duration: 0.8 })
}

onMounted(() => {
  if (!el.value) return
  map = L.map(el.value, {
    center: props.center ?? [7.37, 12.35], zoom: props.zoom, worldCopyJump: true, zoomControl: props.interactive,
    dragging: props.interactive, scrollWheelZoom: false, attributionControl: true,
  })
  map.on('focus', () => map?.scrollWheelZoom.enable())
  map.on('blur', () => map?.scrollWheelZoom.disable())
  setTiles()
  void draw(true)
})
onBeforeUnmount(() => { map?.remove(); map = null })

watch(() => [props.theme, props.basemap], setTiles)
watch(() => [props.points, props.circles, props.routes, props.mode], () => void draw(true), { deep: false })
watch(() => props.selectedId, () => { void draw(false); flyToSelected() })

defineExpose({ invalidate: () => map?.invalidateSize() })
</script>

<template>
  <div ref="el" class="pg-map" :class="`theme-${theme}`" :style="{ height }" role="region" aria-label="Map"></div>
</template>

<style>
.pg-map { width: 100%; border-radius: 1.1rem; overflow: hidden; z-index: 0; }
.pg-map.theme-dark { background: #0b1224; }
.pg-map .leaflet-control-attribution { font-size: 9px; background: rgba(255, 255, 255, 0.6); }
.pg-map.theme-dark .leaflet-control-attribution { background: rgba(2, 6, 23, 0.6); color: #94a3b8; }
.pg-map.theme-dark .leaflet-control-attribution a { color: #67e8f9; }
.pg-marker-wrap { background: none; border: 0; }
.pg-marker {
  display: grid; place-items: center; border-radius: 9999px;
  background: color-mix(in srgb, var(--c) 85%, white 15%);
  border: 2px solid white; box-shadow: 0 0 0 4px color-mix(in srgb, var(--c) 30%, transparent), 0 6px 14px -6px var(--c);
  color: white; font: 700 10px/1 system-ui, sans-serif; animation: pg-pulse 2.2s ease-out infinite;
}
.pg-marker.is-selected { box-shadow: 0 0 0 6px color-mix(in srgb, var(--c) 45%, transparent), 0 0 24px var(--c); transform: scale(1.2); }
.pg-cluster {
  display: grid; place-items: center; border-radius: 9999px; color: white; font: 800 12px/1 system-ui, sans-serif;
  background: radial-gradient(circle, color-mix(in srgb, var(--c) 90%, white 10%) 0 55%, color-mix(in srgb, var(--c) 35%, transparent) 56% 100%);
  box-shadow: 0 0 22px -4px var(--c);
}
.pg-route { stroke-dasharray: 8 10; animation: pg-dash 1.2s linear infinite; filter: drop-shadow(0 0 4px #22d3ee); }
@keyframes pg-dash { to { stroke-dashoffset: -18; } }
@keyframes pg-pulse { 0% { box-shadow: 0 0 0 0 color-mix(in srgb, var(--c) 55%, transparent); } 100% { box-shadow: 0 0 0 14px transparent; } }
@media (prefers-reduced-motion: reduce) { .pg-marker, .pg-route { animation: none; } }
</style>
