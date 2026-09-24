<script setup lang="ts">
import { useUserNotificationsStore } from '@/stores/userNotifications'
import type { UserNotification } from '@/services/userAccount.service'
import { timeAgo } from '@/utils/risk'

/** Shared by the header bell (compact) and the Notifications tab. */
withDefaults(defineProps<{ limit?: number }>(), { limit: 50 })
const emit = defineEmits<{ open: [notification: UserNotification] }>()
const store = useUserNotificationsStore()

const ICON = { threat: '🚨', warning: '⚠️', tip: '💡' } as const

function open(n: UserNotification) {
  store.markRead(n.id)
  emit('open', n)
}
</script>

<template>
  <div>
    <p v-if="!store.items.length" class="px-4 py-8 text-center text-sm text-slate-400">
      Aucune notification. Les alertes de vos analyses apparaîtront ici.
    </p>
    <ul v-else class="divide-y divide-slate-100">
      <li v-for="n in store.items.slice(0, limit)" :key="n.id">
        <button class="flex w-full gap-3 px-4 py-3 text-left transition hover:bg-slate-50" @click="open(n)">
          <span class="text-lg leading-none">{{ ICON[n.type] }}</span>
          <span class="min-w-0 flex-1">
            <span class="flex items-center gap-2">
              <span class="text-sm font-semibold" :class="store.isRead(n.id) ? 'text-slate-500' : 'text-slate-800'">{{ n.title }}</span>
              <span v-if="!store.isRead(n.id)" class="h-2 w-2 rounded-full bg-blue-500" aria-label="Non lue"></span>
            </span>
            <span class="mt-0.5 line-clamp-2 block text-xs text-slate-500">{{ n.body }}</span>
            <span class="mt-1 block text-[11px] text-slate-400">
              {{ timeAgo(n.created_at) }}<template v-if="n.analysis_id"> · <span class="text-blue-600">Lire plus →</span></template>
            </span>
          </span>
        </button>
      </li>
    </ul>
  </div>
</template>
