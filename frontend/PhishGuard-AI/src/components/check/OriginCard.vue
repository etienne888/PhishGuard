<script setup lang="ts">
/**
 * "Where did this email come from?" (user view): approximate area on a map with
 * an honest accuracy circle, network, sending software, precision meter and
 * warnings. No IP address or header is ever shown here (admin-only).
 */
import { computed } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import CountryFlag from '@/components/ui/CountryFlag.vue'
import type { IconName } from '@/components/ui/icons'
import GeoMap from '@/components/map/GeoMap.vue'
import type { OriginPublic } from '@/services/geo.service'
import { useI18n } from '@/i18n'

const props = defineProps<{ origin: OriginPublic }>()
const { t } = useI18n()

const hidden = computed(() => props.origin.precision === 'hidden' || props.origin.lat == null)
const place = computed(() => [props.origin.city, props.origin.region !== props.origin.city ? props.origin.region : null, props.origin.country]
  .filter(Boolean).join(', '))
const PRECISION: Record<OriginPublic['precision'], { level: number; tone: string }> = {
  high: { level: 3, tone: 'bg-emerald-500' }, medium: { level: 2, tone: 'bg-amber-500' },
  low: { level: 1, tone: 'bg-orange-500' }, hidden: { level: 0, tone: 'bg-slate-400' },
}
const NETWORK_ICON: Record<string, IconName> = { mobile: 'smartphone', fixed: 'home', hosting: 'cpu', proxy: 'lock' }
const WARNINGS = ['foreign_for_local_brand', 'datacenter', 'proxy', 'blacklisted', 'scripted', 'timezone_mismatch']
const warnings = computed(() => props.origin.flags.filter((f) => WARNINGS.includes(f)))
const circle = computed(() => (hidden.value ? [] : [{
  lat: props.origin.lat!, lon: props.origin.lon!, radiusKm: props.origin.accuracy_km ?? 15,
  tone: warnings.value.length ? 'danger' as const : 'info' as const,
}]))
</script>

<template>
  <div class="grid gap-4 md:grid-cols-5">
    <!-- Map (or explanation when the provider hides the sender) -->
    <div class="md:col-span-3">
      <GeoMap v-if="!hidden" :circles="circle" :points="[{ id: 'o', lat: origin.lat!, lon: origin.lon!, tone: warnings.length ? 'danger' : 'info', label: place }]"
              mode="plain" theme="light" height="220px" :zoom="9" :center="[origin.lat!, origin.lon!]" />
      <div v-else class="hidden-box">
        <AppIcon name="eye" :size="26" class="text-slate-400" />
        <p class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ origin.provider ? t('geo.hiddenBy', { provider: origin.provider }) : t('geo.hiddenUnknown') }}</p>
        <p class="text-xs text-slate-500">{{ t('geo.hiddenWhy') }}</p>
      </div>
    </div>

    <!-- Facts -->
    <div class="space-y-2.5 md:col-span-2">
      <p v-if="!hidden" class="flex items-start gap-2 text-sm">
        <CountryFlag :code="origin.country_code" :size="20" class="mt-0.5" />
        <span><b class="text-slate-800 dark:text-white">{{ t('geo.around', { place }) }}</b>
          <span class="block text-xs text-slate-500">{{ t('geo.radius', { km: origin.accuracy_km ?? '?' }) }}</span></span>
      </p>
      <p v-if="origin.isp" class="fact"><AppIcon :name="NETWORK_ICON[origin.network_type ?? ''] ?? 'globe'" :size="15" />
        <span>{{ origin.isp }} · {{ t(`geo.net.${origin.network_type ?? 'unknown'}`) }}</span></p>
      <p v-if="origin.provider" class="fact"><AppIcon name="mail" :size="15" /><span>{{ t('geo.via', { provider: origin.provider }) }}</span></p>
      <p v-if="origin.device" class="fact"><AppIcon name="cpu" :size="15" /><span>{{ t('geo.software', { device: origin.device }) }}</span></p>
      <p class="fact"><AppIcon name="radar" :size="15" /><span>{{ t('geo.hops', { n: origin.hop_count }) }}</span></p>

      <div>
        <p class="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">{{ t('geo.precision') }}</p>
        <div class="flex items-center gap-2">
          <div class="flex gap-1"><span v-for="i in 3" :key="i" class="h-1.5 w-6 rounded-full" :class="i <= PRECISION[origin.precision].level ? PRECISION[origin.precision].tone : 'bg-slate-200 dark:bg-slate-700'"></span></div>
          <span class="text-xs font-semibold text-slate-600 dark:text-slate-300">{{ t(`geo.prec.${origin.precision}`) }}</span>
        </div>
      </div>
    </div>

    <ul v-if="warnings.length" class="space-y-1.5 md:col-span-5">
      <li v-for="w in warnings" :key="w" class="warn"><AppIcon name="alert" :size="15" class="mt-0.5 shrink-0" /> {{ t(`geo.flag.${w}`) }}</li>
    </ul>
    <p class="text-[11px] text-slate-400 md:col-span-5"><AppIcon name="info" :size="12" class="inline" /> {{ t('geo.disclaimer') }}</p>
  </div>
</template>

<style scoped>
.hidden-box { display: flex; height: 220px; flex-direction: column; align-items: center; justify-content: center; gap: 0.4rem; padding: 1rem; border-radius: 1.1rem; text-align: center; background: repeating-linear-gradient(135deg, rgba(148, 163, 184, 0.08) 0 10px, transparent 10px 20px); border: 1px dashed rgba(148, 163, 184, 0.5); }
.fact { display: flex; align-items: center; gap: 0.5rem; font-size: 0.82rem; color: #475569; }
:global(.dark) .fact { color: #cbd5e1; }
.warn { display: flex; gap: 0.5rem; padding: 0.5rem 0.7rem; border-radius: 0.8rem; font-size: 0.82rem; color: #9f1239; background: rgba(244, 63, 94, 0.07); }
:global(.dark) .warn { color: #fda4af; }
</style>
