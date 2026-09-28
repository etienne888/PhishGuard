<script setup lang="ts">
/** "Where do my emails come from?" - approximate origins of the user's emails (no IPs). */
import { computed, onMounted, ref, watch } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import CountryFlag from '@/components/ui/CountryFlag.vue'
import GeoMap from '@/components/map/GeoMap.vue'
import type { Tone } from '@/components/map/GeoMap.vue'
import { geoService, type MyOriginPoint } from '@/services/geo.service'
import { useI18n } from '@/i18n'

const emit = defineEmits<{ open: [analysisId: number] }>()
const { t } = useI18n()
const points = ref<MyOriginPoint[]>([])
const hidden = ref(0)
const loaded = ref(false)
const available = ref(false)
const selected = ref<string | null>(null)
const scope = ref<'threats' | 'all'>('threats')

async function load(first = false) {
  try {
    const res = await geoService.myOrigins(90, scope.value)
    // No traced threat yet: start on "all emails" so the map is not empty
    if (first && !res.points.length) {
      scope.value = 'all'
      return
    }
    points.value = res.points
    hidden.value = res.hidden
    available.value = available.value || !!(res.points.length || res.hidden)
  } catch { /* card stays hidden */ }
  loaded.value = true
}
onMounted(() => load(true))
watch(scope, () => { selected.value = null; void load() })

const tone = (v?: string): Tone => (v === 'phishing' ? 'danger' : v === 'suspicious' ? 'warn' : 'safe')
const mapPoints = computed(() => points.value.map((p) => ({
  id: `${p.lat},${p.lon}`, lat: p.lat, lon: p.lon, count: p.count, tone: tone(p.verdict),
  label: `${p.city ?? p.country ?? '?'} · ${p.count}`,
})))
const circles = computed(() => points.value.map((p) => ({ lat: p.lat, lon: p.lon, radiusKm: p.accuracy_km ?? 15, tone: tone(p.verdict) })))
const countries = computed(() => {
  const by = new Map<string, { cc: string | null; name: string; n: number }>()
  for (const p of points.value) {
    const key = p.country ?? '?'
    by.set(key, { cc: p.country_code, name: key, n: (by.get(key)?.n ?? 0) + p.count })
  }
  return [...by.values()].sort((a, b) => b.n - a.n).slice(0, 4)
})
const current = computed(() => points.value.find((p) => `${p.lat},${p.lon}` === selected.value) ?? null)
</script>

<template>
  <section v-if="loaded && available" class="rounded-2xl border border-slate-200 bg-white p-4">
    <div class="mb-3 flex items-center gap-2">
      <span class="grid h-8 w-8 place-items-center rounded-xl bg-red-50 text-red-600"><AppIcon name="mapPin" :size="16" /></span>
      <div class="flex-1">
        <h3 class="font-semibold text-slate-800">{{ t('geo.mine.title') }}</h3>
        <p class="text-xs text-slate-500">{{ t('geo.mine.subtitle') }}</p>
      </div>
      <div class="flex rounded-full bg-slate-100 p-0.5 text-xs">
        <button v-for="s in (['threats', 'all'] as const)" :key="s" class="rounded-full px-2.5 py-1"
                :class="scope === s ? 'bg-white font-semibold text-slate-800 shadow-sm' : 'text-slate-500'" @click="scope = s">{{ t(`geo.scope.${s}`) }}</button>
      </div>
    </div>
    <GeoMap v-if="points.length" :points="mapPoints" :circles="circles" mode="plain" theme="light" height="260px"
            :selected-id="selected" @select="(id) => (selected = id)" />
    <p v-else class="rounded-xl bg-slate-50 px-3 py-6 text-center text-xs text-slate-500">{{ t('geo.mine.empty') }}</p>
    <div class="mt-3 flex flex-wrap gap-2">
      <span v-for="c in countries" :key="c.name" class="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700"><CountryFlag :code="c.cc" :size="14" /> {{ c.name }} <b>{{ c.n }}</b></span>
      <span v-if="hidden" class="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-500"><AppIcon name="eye" :size="12" /> {{ t('geo.mine.hidden', { n: hidden }) }}</span>
    </div>
    <ul v-if="current" class="mt-3 space-y-1">
      <li v-for="a in current.analyses" :key="a.id">
        <button class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs hover:bg-slate-50" @click="emit('open', a.id)">
          <span class="h-2 w-2 rounded-full" :class="a.verdict === 'phishing' ? 'bg-red-500' : a.verdict === 'suspicious' ? 'bg-amber-500' : 'bg-emerald-500'"></span>
          <span class="min-w-0 flex-1 truncate text-slate-700">{{ a.subject || t('ux.live.noSubject') }}</span>
          <AppIcon name="chevronRight" :size="14" class="text-slate-400" />
        </button>
      </li>
    </ul>
  </section>
</template>
