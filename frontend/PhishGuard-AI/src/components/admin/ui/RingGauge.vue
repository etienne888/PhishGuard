<script setup lang="ts">
import { computed } from 'vue'

/** Circular 0-100 gauge. Colour follows the value unless `invert` (high = bad, e.g. CPU). */
const props = withDefaults(defineProps<{ value: number | null | undefined; size?: number; label?: string; invert?: boolean; unit?: string }>(),
  { size: 96, label: '', invert: false, unit: '' })

const pct = computed(() => Math.max(0, Math.min(100, props.value ?? 0)))
const color = computed(() => {
  const good = props.invert ? pct.value < 60 : pct.value >= 70
  const medium = props.invert ? pct.value < 85 : pct.value >= 45
  return good ? '#10b981' : medium ? '#f59e0b' : '#ef4444'
})
const R = 42
const C = 2 * Math.PI * R
</script>

<template>
  <div class="relative inline-grid place-items-center" :style="{ width: `${size}px`, height: `${size}px` }" role="img"
       :aria-label="`${label} ${value ?? '—'}${unit}`">
    <svg viewBox="0 0 100 100" class="absolute inset-0 -rotate-90">
      <circle cx="50" cy="50" :r="R" fill="none" stroke="currentColor" stroke-width="9" class="text-slate-100 dark:text-slate-800" />
      <circle cx="50" cy="50" :r="R" fill="none" :stroke="color" stroke-width="9" stroke-linecap="round"
              :stroke-dasharray="C" :stroke-dashoffset="C * (1 - pct / 100)" class="transition-all duration-700" />
    </svg>
    <div class="relative text-center leading-none">
      <span class="text-xl font-bold tabular-nums text-slate-900 dark:text-white">{{ value ?? '—' }}</span><span class="text-xs text-slate-400">{{ unit }}</span>
      <p v-if="label" class="mt-1 text-[10px] font-medium uppercase tracking-wide text-slate-400">{{ label }}</p>
    </div>
  </div>
</template>
