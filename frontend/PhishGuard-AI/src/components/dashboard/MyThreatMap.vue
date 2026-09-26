<script setup lang="ts">
/** "Where do my threats come from?" - approximate origins of the user's dangerous emails (no IPs). */
import { computed, onMounted, ref } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import GeoMap from '@/components/map/GeoMap.vue'
import { flag, geoService, type MyOriginPoint } from '@/services/geo.service'
import { useI18n } from '@/i18n'

const emit = defineEmits<{ open: [analysisId: number] }>()
const { t } = useI18n()
const points = ref<MyOriginPoint[]>([])
const hidden = ref(0)
const loaded = ref(false)
const selected = ref<string | null>(null)

onMounted(async () => {
  try {
    const res = await geoService.myOrigins()
    points.value = res.points
    hidden.value = res.hidden
  } catch { /* card stays hidden */ }
  loaded.value = true
})

const mapPoints = computed(() => points.value.map((p) => ({
  id: `${p.lat},${p.lon}`, lat: p.lat, lon: p.lon, count: p.count, tone: 'danger' as const,
  label: `${p.city ?? p.country ?? '?'} · ${p.count}`,
})))
const circles = computed(() => points.value.map((p) => ({ lat: p.lat, lon: p.lon, radiusKm: p.accuracy_km ?? 15, tone: 'danger' as const })))
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
  <section v-if="loaded && (points.length || hidden)" class="rounded-2xl border border-slate-200 bg-white p-4">
    <div class="mb-3 flex items-center gap-2">
      <span class="grid h-8 w-8 place-items-center rounded-xl bg-red-50 text-red-600"><AppIcon name="mapPin" :size="16" /></span>
      <div class="flex-1">
        <h3 class="font-semibold text-slate-800">{{ t('geo.mine.title') }}</h3>
        <p class="text-xs text-slate-500">{{ t('geo.mine.subtitle') }}</p>
      </div>
    </div>
    <GeoMap v-if="points.length" :points="mapPoints" :circles="circles" mode="plain" theme="light" height="240px"
            :selected-id="selected" @select="(id) => (selected = id)" />
    <div class="mt-3 flex flex-wrap gap-2">
      <span v-for="c in countries" :key="c.name" class="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-700">{{ flag(c.cc) }} {{ c.name }} <b>{{ c.n }}</b></span>
      <span v-if="hidden" class="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-500"><AppIcon name="eye" :size="12" /> {{ t('geo.mine.hidden', { n: hidden }) }}</span>
    </div>
    <ul v-if="current" class="mt-3 space-y-1">
      <li v-for="a in current.analyses" :key="a.id">
        <button class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-xs hover:bg-slate-50" @click="emit('open', a.id)">
          <span class="h-2 w-2 rounded-full" :class="a.verdict === 'phishing' ? 'bg-red-500' : 'bg-amber-500'"></span>
          <span class="min-w-0 flex-1 truncate text-slate-700">{{ a.subject || t('ux.live.noSubject') }}</span>
          <AppIcon name="chevronRight" :size="14" class="text-slate-400" />
        </button>
      </li>
    </ul>
  </section>
</template>
