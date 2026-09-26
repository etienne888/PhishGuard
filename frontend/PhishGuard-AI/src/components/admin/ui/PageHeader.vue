<script setup lang="ts">
/** Title block shared by every admin screen: icon, title, subtitle, actions on the right. */
defineProps<{ title: string; subtitle?: string; icon?: string; live?: boolean }>()
</script>

<template>
  <header class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
    <div class="flex items-start gap-3">
      <span v-if="icon" class="grid h-11 w-11 flex-shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-slate-900 to-slate-700 text-lg text-white shadow-md dark:from-cyan-500/20 dark:to-blue-500/10 dark:ring-1 dark:ring-cyan-400/30">{{ icon }}</span>
      <div>
        <h1 class="flex items-center gap-2 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          {{ title }}
          <span v-if="live" class="relative flex h-2.5 w-2.5" aria-hidden="true">
            <span class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
          </span>
        </h1>
        <p v-if="subtitle" class="mt-0.5 max-w-3xl text-sm text-slate-500 dark:text-slate-400">{{ subtitle }}</p>
      </div>
    </div>
    <div class="flex flex-wrap items-center gap-2"><slot /></div>
  </header>
</template>
