<script setup lang="ts">
/** "Scam in progress" alerts fed by the incidents the SOC correlates (anonymised, public). */
import { onMounted, ref } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { publicService, type CommunityAlert } from '@/services/public.service'
import { timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

withDefaults(defineProps<{ compact?: boolean }>(), { compact: false })
const { t } = useI18n()
const items = ref<CommunityAlert[]>([])
const loaded = ref(false)

onMounted(async () => {
  try { items.value = (await publicService.alerts()).items } catch { /* hidden when unavailable */ }
  loaded.value = true
})

const SEVERITY: Record<string, string> = {
  critical: 'bg-red-500', high: 'bg-orange-500', medium: 'bg-amber-400', low: 'bg-slate-400',
}
</script>

<template>
  <section :id="compact ? undefined : 'alerts'" :class="compact ? '' : 'px-4 py-16'">
    <div :class="compact ? '' : 'mx-auto max-w-5xl'">
      <div class="mb-4 flex items-end justify-between gap-3">
        <div>
          <p class="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-red-600">
            <span class="live"></span> {{ t('ux.alerts.eyebrow') }}
          </p>
          <h2 :class="compact ? 'text-lg' : 'text-2xl sm:text-3xl'" class="mt-1 font-bold text-slate-800 dark:text-white font-display">{{ t('ux.alerts.title') }}</h2>
        </div>
        <span class="hidden text-xs text-slate-500 sm:block">{{ t('ux.alerts.hint') }}</span>
      </div>

      <div v-if="loaded && !items.length" class="calm">
        <AppIcon name="shieldCheck" :size="22" class="text-emerald-600" />
        <p class="text-sm text-slate-600 dark:text-slate-300">{{ t('ux.alerts.none') }}</p>
      </div>

      <ul v-else class="grid gap-3" :class="compact ? 'sm:grid-cols-2 lg:grid-cols-1' : 'sm:grid-cols-2 lg:grid-cols-3'">
        <li v-for="a in items" :key="a.id" class="alert-card">
          <div class="flex items-start gap-3">
            <span class="icon"><AppIcon :name="a.kind === 'brand' ? 'shieldAlert' : 'link'" :size="18" /></span>
            <div class="min-w-0 flex-1">
              <p class="text-sm font-semibold text-slate-800 dark:text-white">
                {{ a.kind === 'brand' ? t('ux.alerts.brand', { brand: a.label }) : t('ux.alerts.domain') }}
              </p>
              <p v-if="a.kind !== 'brand'" class="mt-0.5 truncate font-mono text-xs text-red-600">{{ a.label }}</p>
              <div class="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-slate-500">
                <span class="flex items-center gap-1"><span class="h-2 w-2 rounded-full" :class="SEVERITY[a.severity] ?? 'bg-slate-400'"></span>{{ t(`ux.alerts.sev.${a.severity}`) }}</span>
                <span class="flex items-center gap-1"><AppIcon name="message" :size="12" /> {{ t('ux.alerts.messages', { n: a.messages }) }}</span>
                <span v-if="a.regions.length" class="flex items-center gap-1"><AppIcon name="mapPin" :size="12" /> {{ a.regions.join(', ') }}</span>
                <span v-if="a.last_seen" class="flex items-center gap-1"><AppIcon name="clock" :size="12" /> {{ timeAgo(a.last_seen) }}</span>
              </div>
            </div>
          </div>
        </li>
      </ul>
    </div>
  </section>
</template>

<style scoped>
.live { width: 0.5rem; height: 0.5rem; border-radius: 9999px; background: #ef4444; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); animation: ping 1.8s infinite; }
@keyframes ping { 70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
@media (prefers-reduced-motion: reduce) { .live { animation: none; } }
.alert-card { padding: 1rem; border-radius: 1.2rem; background: white; border: 1px solid rgba(239, 68, 68, 0.15); box-shadow: 0 10px 30px -24px rgba(239, 68, 68, 0.6); }
:global(.dark) .alert-card { background: #0b1224; border-color: rgba(239, 68, 68, 0.25); }
.icon { display: grid; place-items: center; width: 2.3rem; height: 2.3rem; border-radius: 0.8rem; color: #dc2626; background: rgba(239, 68, 68, 0.1); flex-shrink: 0; }
.calm { display: flex; align-items: center; gap: 0.75rem; padding: 1rem 1.1rem; border-radius: 1.2rem; background: rgba(16, 185, 129, 0.07); border: 1px solid rgba(16, 185, 129, 0.2); }
</style>
