<script setup lang="ts">
/** "Your month": scans, scams avoided, reports, most imitated brand and quiz level. */
import { computed, onMounted, ref } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { experienceService, type MonthlySummary } from '@/services/experience.service'
import { LEVELS } from '@/data/quiz'
import { intlLocale, useI18n } from '@/i18n'

const { t } = useI18n()
const data = ref<MonthlySummary | null>(null)

onMounted(async () => {
  try { data.value = await experienceService.summary() } catch { /* card hidden */ }
})

const monthName = computed(() => {
  if (!data.value) return ''
  const [y, m] = data.value.month.split('-').map(Number)
  return new Date(y!, (m ?? 1) - 1, 1).toLocaleDateString(intlLocale.value, { month: 'long', year: 'numeric' })
})
const trend = computed(() => {
  if (!data.value) return 0
  return data.value.scans - data.value.scans_previous_month
})
const level = computed(() => LEVELS.find((l) => l.key === data.value?.quiz.level.key) ?? LEVELS[0]!)

defineExpose({ reload: async () => { data.value = await experienceService.summary() } })
</script>

<template>
  <section v-if="data" class="summary">
    <div class="flex items-center justify-between">
      <p class="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-blue-700 dark:text-cyan-300">
        <AppIcon name="clock" :size="14" /> {{ t('ux.summary.month', { month: monthName }) }}
      </p>
      <span v-if="trend !== 0" class="text-xs font-semibold" :class="trend > 0 ? 'text-emerald-600' : 'text-slate-500'">
        {{ trend > 0 ? '+' : '' }}{{ trend }} {{ t('ux.summary.vsLast') }}
      </span>
    </div>
    <h3 class="mt-2 text-lg font-bold text-slate-800 dark:text-white">
      {{ data.threats_avoided ? t('ux.summary.avoided', { n: data.threats_avoided }) : t('ux.summary.calm') }}
    </h3>

    <div class="mt-4 grid grid-cols-3 gap-2">
      <div class="tile"><AppIcon name="search" :size="16" class="text-blue-600" /><b>{{ data.scans }}</b><span>{{ t('ux.summary.scans') }}</span></div>
      <div class="tile"><AppIcon name="shieldAlert" :size="16" class="text-red-600" /><b>{{ data.threats_avoided + data.suspicious }}</b><span>{{ t('ux.summary.dangers') }}</span></div>
      <div class="tile"><AppIcon name="users" :size="16" class="text-violet-600" /><b>{{ data.reports }}</b><span>{{ t('ux.summary.reports') }}</span></div>
    </div>

    <p v-if="data.top_brand" class="mt-3 flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
      <AppIcon name="target" :size="16" class="text-amber-600" /> {{ t('ux.summary.topBrand', { brand: data.top_brand }) }}
    </p>

    <RouterLink to="/learn" class="level">
      <span class="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-violet-500 to-blue-500 text-white"><AppIcon :name="level.icon" :size="17" /></span>
      <span class="flex-1">
        <span class="block text-xs text-slate-500">{{ t('ux.learn.yourLevel') }}</span>
        <span class="block text-sm font-semibold text-slate-800 dark:text-white">{{ t(`ux.level.${level.key}`) }} · {{ data.quiz.level.xp }} XP</span>
      </span>
      <span class="text-xs font-semibold text-blue-600">{{ t('ux.summary.playQuiz') }}</span>
      <AppIcon name="chevronRight" :size="16" class="text-blue-600" />
    </RouterLink>
  </section>
</template>

<style scoped>
.summary { padding: 1.2rem; border-radius: 1.4rem; background: linear-gradient(135deg, rgba(37, 99, 235, 0.07), rgba(139, 92, 246, 0.07)); border: 1px solid rgba(99, 102, 241, 0.18); }
.tile { display: flex; flex-direction: column; align-items: flex-start; gap: 0.15rem; padding: 0.7rem; border-radius: 1rem; background: rgba(255, 255, 255, 0.8); }
:global(.dark) .tile { background: rgba(15, 23, 42, 0.7); }
.tile b { font-size: 1.35rem; line-height: 1.2; color: #1e293b; font-variant-numeric: tabular-nums; }
:global(.dark) .tile b { color: #f1f5f9; }
.tile span { font-size: 0.7rem; color: #64748b; }
.level { margin-top: 0.9rem; display: flex; align-items: center; gap: 0.7rem; padding: 0.65rem 0.8rem; border-radius: 1rem; background: rgba(255, 255, 255, 0.8); transition: box-shadow 0.2s ease; }
.level:hover { box-shadow: 0 8px 20px -12px rgba(99, 102, 241, 0.6); }
:global(.dark) .level { background: rgba(15, 23, 42, 0.7); }
</style>
