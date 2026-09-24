import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { userAccountService, type UserNotification } from '@/services/userAccount.service'

const READ_KEY = 'pg-read-notifications'

function loadReadIds(): Set<string> {
  try {
    return new Set(JSON.parse(localStorage.getItem(READ_KEY) || '[]'))
  } catch {
    return new Set()
  }
}

function saveReadIds(ids: Set<string>) {
  try {
    localStorage.setItem(READ_KEY, JSON.stringify([...ids].slice(-200)))
  } catch {
    /* private mode / storage blocked: read state just won't persist */
  }
}

/** In-app notifications generated from the user's analyses (not the toast stack). */
export const useUserNotificationsStore = defineStore('userNotifications', () => {
  const items = ref<UserNotification[]>([])
  const readIds = ref<Set<string>>(loadReadIds())
  const isLoading = ref(false)

  const unreadCount = computed(() => items.value.filter((n) => !readIds.value.has(n.id)).length)
  const isRead = (id: string) => readIds.value.has(id)

  async function load() {
    isLoading.value = true
    try {
      items.value = (await userAccountService.listNotifications()).items
    } catch {
      /* keep the previous list; the bell simply stays as it was */
    } finally {
      isLoading.value = false
    }
  }

  function markRead(id: string) {
    readIds.value = new Set(readIds.value).add(id)
    saveReadIds(readIds.value)
  }

  function markAllRead() {
    readIds.value = new Set([...readIds.value, ...items.value.map((n) => n.id)])
    saveReadIds(readIds.value)
  }

  return { items, isLoading, unreadCount, isRead, load, markRead, markAllRead }
})
