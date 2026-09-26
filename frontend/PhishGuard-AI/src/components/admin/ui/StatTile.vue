<script setup lang="ts">
/** KPI tile: label, big value, hint line, colour tone, optional click target. */
withDefaults(defineProps<{
  label: string
  value: string | number
  hint?: string
  icon?: string
  tone?: 'slate' | 'red' | 'amber' | 'green' | 'blue' | 'violet' | 'cyan'
  clickable?: boolean
}>(), { tone: 'slate' })

const TONES = {
  slate: 'text-slate-900 dark:text-white',
  red: 'text-red-600 dark:text-red-400',
  amber: 'text-amber-600 dark:text-amber-400',
  green: 'text-emerald-600 dark:text-emerald-400',
  blue: 'text-blue-600 dark:text-blue-400',
  violet: 'text-violet-600 dark:text-violet-400',
  cyan: 'text-cyan-600 dark:text-cyan-400',
} as const
</script>

<template>
  <component :is="clickable ? 'button' : 'div'"
             class="group relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white p-4 text-left shadow-sm transition dark:border-slate-800 dark:bg-slate-900/80"
             :class="clickable ? 'hover:-translate-y-0.5 hover:border-blue-300 hover:shadow-md dark:hover:border-cyan-500/40' : ''">
    <div class="flex items-start justify-between gap-2">
      <p class="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">{{ label }}</p>
      <span v-if="icon" class="text-base opacity-70">{{ icon }}</span>
    </div>
    <p class="mt-1.5 text-2xl font-bold tabular-nums" :class="TONES[tone]">{{ value }}</p>
    <p v-if="hint" class="mt-0.5 truncate text-xs text-slate-400">{{ hint }}</p>
    <slot />
  </component>
</template>
