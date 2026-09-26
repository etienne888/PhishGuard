<script setup lang="ts">
import { translate as t } from '@/i18n'
defineProps<{
  message?: string
  hint?: string
  onRetry?: () => void
}>()
</script>

<template>
  <section class="rounded-lg border border-dashed border-slate-300 bg-slate-50 px-6 py-10 text-center">
    <i class="fas fa-inbox text-2xl text-slate-400" aria-hidden="true" />
    <p class="mt-3 text-sm font-semibold text-slate-700">{{ message ?? t('common.empty') }}</p>
    <p v-if="hint" class="mt-1 text-xs text-slate-500">{{ hint }}</p>
    <button
      v-if="onRetry"
      class="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
      type="button"
      :aria-label="t('common.retry')"
      @click="onRetry"
    >
      {{ t('common.retry') }}
    </button>
  </section>
</template>
