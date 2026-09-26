<script setup lang="ts">
/** Card with an optional header (title, hint, actions). `flush` removes the body padding for tables. */
defineProps<{ title?: string; hint?: string; flush?: boolean }>()
</script>

<template>
  <section class="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900/80">
    <div v-if="title || $slots.actions" class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 px-5 py-3.5 dark:border-slate-800">
      <div class="min-w-0">
        <h2 class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ title }}</h2>
        <p v-if="hint" class="text-xs text-slate-500 dark:text-slate-400">{{ hint }}</p>
      </div>
      <div class="flex flex-wrap items-center gap-2"><slot name="actions" /></div>
    </div>
    <div :class="flush ? '' : 'p-5'"><slot /></div>
  </section>
</template>
