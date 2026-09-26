<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { userAccountService } from '@/services/userAccount.service'
import type { DashboardMessage, MessageStatus } from '@/services/userDashboard.service'
import { experienceService } from '@/services/experience.service'
import { STATUS_META, formatDate } from '@/utils/risk'
import { useI18n } from '@/i18n'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'

type Source = 'web' | 'mailbox' | 'forward' | 'share'
const SOURCE_ICON: Record<Source, IconName> = { web: 'search', mailbox: 'inbox', forward: 'mail', share: 'share' }

const emit = defineEmits<{ open: [id: number]; analyze: [] }>()
const { t } = useI18n()

const items = ref<DashboardMessage[]>([])
const total = ref(0)
const page = ref(1)
const perPage = 10
const status = ref<MessageStatus | ''>('')
const q = ref('')
const source = ref<Source | ''>('')
const confirmId = ref<number | null>(null)
const loading = ref(false)
const error = ref('')

const FILTERS = computed<Array<{ id: MessageStatus | ''; label: string }>>(() => [
  { id: '', label: t('common.all') },
  { id: 'phishing', label: t('status.phishing') },
  { id: 'suspicious', label: t('dashboard.suspiciousPlural') },
  { id: 'safe', label: t('status.safe') },
])

async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = await userAccountService.listAnalyses({ page: page.value, per_page: perPage, status: status.value, source: source.value, q: q.value })
    items.value = result.items
    total.value = result.total
  } catch {
    error.value = t('history.loadFailed')
  } finally {
    loading.value = false
  }
}

let searchTimer: number | undefined
watch(q, () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => { page.value = 1; load() }, 350)
})
watch([status, source], () => { page.value = 1; load() })

async function remove(id: number) {
  try {
    await experienceService.deleteAnalysis(id)
    confirmId.value = null
    await load()
  } catch { /* toast from apiFetch */ }
}
watch(page, load)
onMounted(load)

defineExpose({ reload: load })
</script>

<template>
  <div class="rounded-2xl border border-slate-200 bg-white">
    <div class="flex flex-col gap-3 border-b border-slate-100 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div class="flex flex-wrap gap-1.5">
        <button v-for="f in FILTERS" :key="f.id" class="rounded-full border px-3 py-1.5 text-xs font-medium transition"
                :class="status === f.id ? 'border-slate-800 bg-slate-800 text-white' : 'border-slate-200 text-slate-600 hover:border-slate-400'"
                @click="status = f.id">
          <span v-if="f.id" class="mr-1 inline-block h-2 w-2 rounded-full" :class="STATUS_META[f.id].dot"></span>{{ f.label }}
        </button>
        <label class="sr-only" for="history-source">{{ t('ux.history.source') }}</label>
        <select id="history-source" v-model="source" class="rounded-full border border-slate-200 bg-transparent px-3 py-1.5 text-xs text-slate-600">
          <option value="">{{ t('ux.history.allSources') }}</option>
          <option v-for="s in (['web', 'mailbox', 'forward', 'share'] as const)" :key="s" :value="s">{{ t(`ux.source.${s}`) }}</option>
        </select>
      </div>
      <input v-model="q" type="search" :placeholder="t('history.search')"
             class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400 sm:w-64" />
    </div>

    <p v-if="error" class="p-6 text-sm text-red-600">{{ error }}</p>
    <div v-else-if="!loading && !items.length" class="p-10 text-center">
      <p class="text-3xl">🔍</p>
      <p class="mt-2 text-sm font-medium text-slate-700">{{ q || status ? t('history.noResults') : t('history.empty') }}</p>
      <button v-if="!q && !status" class="mt-3 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white" @click="emit('analyze')">
        {{ t('history.analyzeFirst') }}
      </button>
    </div>

    <ul v-else class="divide-y divide-slate-100" :class="{ 'opacity-60': loading }">
      <li v-for="item in items" :key="item.id" class="group flex items-center">
        <button class="flex min-w-0 flex-1 items-center gap-3 px-4 py-3 text-left transition hover:bg-slate-50" @click="emit('open', item.id)">
          <span class="grid h-8 w-8 flex-shrink-0 place-items-center rounded-xl bg-slate-100 text-slate-500" :title="t(`ux.source.${item.origin ?? 'web'}`)">
            <AppIcon :name="SOURCE_ICON[item.origin ?? 'web']" :size="15" />
          </span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm text-slate-800">{{ item.preview }}</span>
            <span class="block text-xs text-slate-400">{{ formatDate(item.received_at) }}</span>
          </span>
          <span class="flex-shrink-0 rounded-full border px-2.5 py-1 text-xs font-medium" :class="STATUS_META[item.status].chip">
            {{ STATUS_META[item.status].label }} · {{ Math.round(item.score) }}
          </span>
        </button>
        <button v-if="confirmId !== item.id" class="mr-2 rounded-lg p-2 text-slate-300 transition hover:bg-red-50 hover:text-red-600 focus:text-red-600"
                :aria-label="t('ux.history.delete')" :title="t('ux.history.delete')" @click="confirmId = item.id">
          <AppIcon name="trash" :size="16" />
        </button>
        <span v-else class="mr-2 flex items-center gap-1">
          <button class="rounded-lg bg-red-600 px-2 py-1 text-xs font-semibold text-white" @click="remove(item.id)">{{ t('ux.history.deleteYes') }}</button>
          <button class="rounded-lg px-2 py-1 text-xs text-slate-500" :aria-label="t('common.cancel')" @click="confirmId = null"><AppIcon name="x" :size="14" /></button>
        </span>
      </li>
    </ul>

    <div v-if="total > perPage" class="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-xs text-slate-500">
      <span>{{ t('history.range', { from: (page - 1) * perPage + 1, to: Math.min(page * perPage, total), total }) }}</span>
      <div class="flex gap-2">
        <button class="rounded-lg border px-3 py-1.5 disabled:opacity-40" :disabled="page === 1" @click="page--">← {{ t('common.previous') }}</button>
        <button class="rounded-lg border px-3 py-1.5 disabled:opacity-40" :disabled="page * perPage >= total" @click="page++">{{ t('common.next') }} →</button>
      </div>
    </div>
  </div>
</template>
