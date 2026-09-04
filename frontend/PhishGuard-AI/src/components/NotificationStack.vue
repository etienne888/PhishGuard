<script setup lang="ts">
import { useNotificationsStore } from '@/stores'

const store = useNotificationsStore()

const toneClass: Record<string, string> = {
  success: 'bg-emerald-600',
  error: 'bg-red-600',
  info: 'bg-slate-800'
}
</script>

<template>
  <div class="fixed bottom-4 right-4 z-[60] flex flex-col gap-2 max-w-xs">
    <TransitionGroup name="toast">
      <div
        v-for="n in store.items"
        :key="n.id"
        class="text-white text-sm px-4 py-3 rounded-xl shadow-lift"
        :class="toneClass[n.tone]"
      >
        {{ n.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
