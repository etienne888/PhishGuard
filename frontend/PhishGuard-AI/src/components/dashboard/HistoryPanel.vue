<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { userAccountService } from '@/services/userAccount.service'
import type { DashboardMessage, MessageStatus } from '@/services/userDashboard.service'
import { STATUS_META, formatDate } from '@/utils/risk'

const emit = defineEmits<{ open: [id: number]; analyze: [] }>()

const items = ref<DashboardMessage[]>([])
const total = ref(0)
const page = ref(1)
const perPage = 10
const status = ref<MessageStatus | ''>('')
const q = ref('')
const loading = ref(false)
const error = ref('')

const FILTERS: Array<{ id: MessageStatus | ''; label: string }> = [
  { id: '', label: 'Tout' },
  { id: 'phishing', label: '🔴 Dangereux' },
  { id: 'suspicious', label: '🟠 Suspects' },
  { id: 'safe', label: '🟢 Sans danger' },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    const result = await userAccountService.listAnalyses({ page: page.value, per_page: perPage, status: status.value, q: q.value })
    items.value = result.items
    total.value = result.total
  } catch {
    error.value = "Impossible de charger l'historique."
  } finally {
    loading.value = false
  }
}

let searchTimer: number | undefined
watch(q, () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => { page.value = 1; load() }, 350)
})
watch(status, () => { page.value = 1; load() })
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
          {{ f.label }}
        </button>
      </div>
      <input v-model="q" type="search" placeholder="Rechercher un message…"
             class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400 sm:w-64" />
    </div>

    <p v-if="error" class="p-6 text-sm text-red-600">{{ error }}</p>
    <div v-else-if="!loading && !items.length" class="p-10 text-center">
      <p class="text-3xl">🔍</p>
      <p class="mt-2 text-sm font-medium text-slate-700">{{ q || status ? 'Aucun résultat pour ce filtre.' : 'Aucune analyse pour le moment.' }}</p>
      <button v-if="!q && !status" class="mt-3 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white" @click="emit('analyze')">
        Analyser mon premier message
      </button>
    </div>

    <ul v-else class="divide-y divide-slate-100" :class="{ 'opacity-60': loading }">
      <li v-for="item in items" :key="item.id">
        <button class="flex w-full items-center gap-3 px-4 py-3 text-left transition hover:bg-slate-50" @click="emit('open', item.id)">
          <span class="h-2.5 w-2.5 flex-shrink-0 rounded-full" :class="STATUS_META[item.status].dot"></span>
          <span class="min-w-0 flex-1">
            <span class="block truncate text-sm text-slate-800">{{ item.preview }}</span>
            <span class="block text-xs text-slate-400">{{ formatDate(item.received_at) }}</span>
          </span>
          <span class="flex-shrink-0 rounded-full border px-2.5 py-1 text-xs font-medium" :class="STATUS_META[item.status].chip">
            {{ STATUS_META[item.status].label }} · {{ Math.round(item.score) }}
          </span>
        </button>
      </li>
    </ul>

    <div v-if="total > perPage" class="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-xs text-slate-500">
      <span>{{ (page - 1) * perPage + 1 }}–{{ Math.min(page * perPage, total) }} sur {{ total }}</span>
      <div class="flex gap-2">
        <button class="rounded-lg border px-3 py-1.5 disabled:opacity-40" :disabled="page === 1" @click="page--">← Précédent</button>
        <button class="rounded-lg border px-3 py-1.5 disabled:opacity-40" :disabled="page * perPage >= total" @click="page++">Suivant →</button>
      </div>
    </div>
  </div>
</template>
