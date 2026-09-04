import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Notification {
  id: number
  message: string
  tone: 'success' | 'error' | 'info'
}

let nextId = 1

export const useNotificationsStore = defineStore('notifications', () => {
  const items = ref<Notification[]>([])

  function push(message: string, tone: Notification['tone'] = 'info', duration = 3200) {
    const id = nextId++
    items.value.push({ id, message, tone })
    window.setTimeout(() => dismiss(id), duration)
  }

  function dismiss(id: number) {
    items.value = items.value.filter((n) => n.id !== id)
  }

  return { items, push, dismiss }
})
