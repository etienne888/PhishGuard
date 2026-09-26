<script setup lang="ts">
import { translate as t } from '@/i18n'
defineProps<{
  message?: string
  hint?: string
  onRetry?: () => void
}>()
</script>

<template>
  <section class="rounded-lg border border-red-200 bg-red-50 px-6 py-8 text-center" role="alert">
    <i class="fas fa-triangle-exclamation text-2xl text-red-500" aria-hidden="true" />
    <p class="mt-3 text-sm font-semibold text-red-800">{{ message ?? t('states.loadFailed') }}</p>
    <p v-if="hint" class="mt-1 text-xs text-red-600">{{ hint }}</p>
    <button
      v-if="onRetry"
      class="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-red-700"
      type="button"
      :aria-label="t('common.retry')"
      @click="onRetry"
    >
      {{ t('common.retry') }}
    </button>
  </section>
</template>
