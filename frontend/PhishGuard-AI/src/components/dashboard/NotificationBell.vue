<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useUserNotificationsStore } from '@/stores/userNotifications'
import type { UserNotification } from '@/services/userAccount.service'
import NotificationList from './NotificationList.vue'

const emit = defineEmits<{ open: [notification: UserNotification]; seeAll: [] }>()
const store = useUserNotificationsStore()
const isOpen = ref(false)
const root = ref<HTMLElement | null>(null)

function onDocumentClick(event: MouseEvent) {
  if (root.value && !root.value.contains(event.target as Node)) isOpen.value = false
}
onMounted(() => document.addEventListener('click', onDocumentClick))
onBeforeUnmount(() => document.removeEventListener('click', onDocumentClick))

function open(n: UserNotification) {
  isOpen.value = false
  emit('open', n)
}
</script>

<template>
  <div ref="root" class="relative">
    <button class="relative rounded-xl border border-slate-200 bg-white p-2.5 text-slate-600 transition hover:border-blue-300 hover:text-blue-600"
            :aria-label="`Notifications (${store.unreadCount} non lues)`" @click="isOpen = !isOpen">
      <svg viewBox="0 0 24 24" class="h-5 w-5" :class="{ ring: store.unreadCount }" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
      <span v-if="store.unreadCount" class="absolute -right-1.5 -top-1.5 grid h-5 min-w-5 place-items-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
        {{ store.unreadCount > 9 ? '9+' : store.unreadCount }}
      </span>
    </button>

    <div v-if="isOpen" class="absolute right-0 z-40 mt-2 w-80 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl">
      <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
        <span class="text-sm font-bold text-slate-800">Notifications</span>
        <button v-if="store.unreadCount" class="text-xs text-blue-600 hover:underline" @click="store.markAllRead()">Tout marquer comme lu</button>
      </div>
      <div class="max-h-96 overflow-y-auto"><NotificationList :limit="6" @open="open" /></div>
      <button class="w-full border-t border-slate-100 py-2.5 text-xs font-medium text-slate-600 hover:bg-slate-50" @click="isOpen = false; emit('seeAll')">
        Voir toutes les notifications
      </button>
    </div>
  </div>
</template>

<style scoped>
.ring { animation: ring 2.5s ease-in-out infinite; transform-origin: top center; }
@keyframes ring {
  0%, 80%, 100% { transform: rotate(0); }
  84% { transform: rotate(14deg); } 88% { transform: rotate(-12deg); }
  92% { transform: rotate(8deg); } 96% { transform: rotate(-4deg); }
}
@media (prefers-reduced-motion: reduce) { .ring { animation: none; } }
</style>
