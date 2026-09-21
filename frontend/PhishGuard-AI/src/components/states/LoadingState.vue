<script setup lang="ts">
withDefaults(defineProps<{
  message?: string
  hint?: string
  onRetry?: () => void
  rows?: number
}>(), {
  message: 'Chargement des données...',
  rows: 3,
})
</script>

<template>
  <section class="space-y-3" aria-busy="true" role="status">
    <p class="text-sm font-medium text-slate-500">{{ message }}</p>
    <p v-if="hint" class="text-xs text-slate-400">{{ hint }}</p>
    <div v-for="row in rows" :key="row" class="animate-pulse rounded-lg border border-slate-200 bg-white p-4">
      <div class="h-4 w-2/5 rounded bg-slate-200" />
      <div class="mt-3 h-3 w-4/5 rounded bg-slate-100" />
    </div>
  </section>
</template>
