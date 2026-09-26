<script setup lang="ts">
/**
 * Dashboard widget: shows a live, compact view while one of the user's mailboxes
 * is being scanned (manually or by the 5-minute background job).
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import LiveScan from './LiveScan.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { mailboxService, type MailboxConnection } from '@/services/mailbox.service'
import { useI18n } from '@/i18n'

const emit = defineEmits<{ finished: [] }>()
const { t } = useI18n()
const running = ref<MailboxConnection[]>([])
let timer: number | undefined

async function check() {
  try {
    const { items } = await mailboxService.list(true)
    const now = items.filter((m) => m.progress?.state === 'running')
    // keep the ones already shown so their LiveScan can finish its animation
    const ids = new Set(running.value.map((m) => m.id))
    running.value = [...running.value, ...now.filter((m) => !ids.has(m.id))]
  } catch { /* no mailbox API: widget stays hidden */ }
}

function finished(id: number) {
  emit('finished')
  setTimeout(() => { running.value = running.value.filter((m) => m.id !== id) }, 6000)
}

onMounted(() => { void check(); timer = window.setInterval(check, 15_000) })
onBeforeUnmount(() => window.clearInterval(timer))
</script>

<template>
  <div v-if="running.length" class="space-y-3">
    <div v-for="m in running" :key="m.id">
      <LiveScan :mailbox-id="m.id" :email="m.email" compact @finished="finished(m.id)" />
      <RouterLink to="/dashboard/mailboxes" class="mt-1.5 inline-flex items-center gap-1 text-xs font-semibold text-blue-600 hover:underline">
        {{ t('ux.live.watch') }} <AppIcon name="arrowRight" :size="13" />
      </RouterLink>
    </div>
  </div>
</template>
