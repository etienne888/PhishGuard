<script setup lang="ts">
/** Small status label. `dot` adds a coloured dot, `pulse` animates it (live / active). */
withDefaults(defineProps<{
  tone?: 'slate' | 'red' | 'amber' | 'green' | 'blue' | 'violet' | 'cyan' | 'orange'
  dot?: boolean
  pulse?: boolean
}>(), { tone: 'slate' })

const TONES = {
  slate: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
  red: 'bg-red-50 text-red-700 ring-1 ring-red-200 dark:bg-red-500/10 dark:text-red-300 dark:ring-red-500/30',
  orange: 'bg-orange-50 text-orange-700 ring-1 ring-orange-200 dark:bg-orange-500/10 dark:text-orange-300 dark:ring-orange-500/30',
  amber: 'bg-amber-50 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-500/10 dark:text-amber-300 dark:ring-amber-500/30',
  green: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-500/10 dark:text-emerald-300 dark:ring-emerald-500/30',
  blue: 'bg-blue-50 text-blue-700 ring-1 ring-blue-200 dark:bg-blue-500/10 dark:text-blue-300 dark:ring-blue-500/30',
  violet: 'bg-violet-50 text-violet-700 ring-1 ring-violet-200 dark:bg-violet-500/10 dark:text-violet-300 dark:ring-violet-500/30',
  cyan: 'bg-cyan-50 text-cyan-700 ring-1 ring-cyan-200 dark:bg-cyan-500/10 dark:text-cyan-300 dark:ring-cyan-500/30',
} as const
const DOTS = {
  slate: 'bg-slate-400', red: 'bg-red-500', orange: 'bg-orange-500', amber: 'bg-amber-500',
  green: 'bg-emerald-500', blue: 'bg-blue-500', violet: 'bg-violet-500', cyan: 'bg-cyan-500',
} as const
</script>

<template>
  <span class="inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-[11px] font-semibold" :class="TONES[tone]">
    <span v-if="dot" class="relative flex h-1.5 w-1.5">
      <span v-if="pulse" class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75" :class="DOTS[tone]"></span>
      <span class="relative inline-flex h-1.5 w-1.5 rounded-full" :class="DOTS[tone]"></span>
    </span>
    <slot />
  </span>
</template>
