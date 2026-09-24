<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import ReviewDrawer from '@/components/admin/ReviewDrawer.vue'
import { adminOpsService, type ReviewItem, type ReviewView } from '@/services/admin.service'
import { useAdminOpsStore } from '@/stores/adminOps'
import { STATUS_META, formatDate } from '@/utils/risk'

const ops = useAdminOpsStore()
const VIEWS: Array<{ id: ReviewView; label: string; help: string }> = [
  { id: 'pending', label: 'À traiter', help: 'Signalements des usagers + scores incertains (40–70) sans décision.' },
  { id: 'reported', label: '🚩 Signalés', help: 'Messages que les usagers ont signalés.' },
  { id: 'borderline', label: '❓ Incertains', help: 'Le moteur hésite (score entre 40 et 70) : votre avis compte le plus ici.' },
  { id: 'reviewed', label: '✓ Traités', help: 'Décisions déjà prises, exportables pour réentraîner le modèle.' },
]

const view = ref<ReviewView>('pending')
const items = ref<ReviewItem[]>([])
const total = ref(0)
const page = ref(1)
const perPage = 15
const loading = ref(false)
const selected = ref<number | null>(null)

async function load() {
  loading.value = true
  try {
    const result = await adminOpsService.listReviewQueue(view.value, page.value)
    items.value = result.items
    total.value = result.total
  } finally {
    loading.value = false
  }
}

function onDecided() {
  void load()
  void ops.load() // keep the menu badge in sync
}

watch(view, () => { page.value = 1; load() })
watch(page, load)
onMounted(load)
</script>

<template>
  <div class="space-y-4">
    <div class="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 class="text-2xl font-bold">Signalements & revue</h1>
        <p class="text-sm text-slate-500">Confirmez ou rejetez les verdicts. Chaque décision devient une donnée d'entraînement.</p>
      </div>
      <a :href="adminOpsService.exportUrl" class="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium hover:border-blue-300 dark:border-slate-700">📥 Exporter les décisions (CSV)</a>
    </div>

    <div class="flex flex-wrap gap-2">
      <button v-for="v in VIEWS" :key="v.id" class="rounded-full border px-4 py-1.5 text-sm font-medium transition"
              :class="view === v.id ? 'border-slate-800 bg-slate-800 text-white dark:border-white dark:bg-white dark:text-slate-900' : 'border-slate-200 text-slate-600 hover:border-slate-400 dark:border-slate-700 dark:text-slate-300'"
              @click="view = v.id">{{ v.label }}</button>
    </div>
    <p class="text-xs text-slate-500">{{ VIEWS.find((v) => v.id === view)?.help }}</p>

    <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div v-if="!loading && !items.length" class="p-10 text-center">
        <p class="text-3xl">✅</p>
        <p class="mt-2 text-sm text-slate-500">Rien à traiter ici. Beau travail !</p>
      </div>
      <table v-else class="w-full text-sm" :class="{ 'opacity-60': loading }">
        <thead class="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500 dark:bg-slate-800/60">
          <tr>
            <th class="px-4 py-3">Message</th>
            <th class="hidden px-4 py-3 md:table-cell">Origine</th>
            <th class="px-4 py-3">Moteur</th>
            <th class="hidden px-4 py-3 sm:table-cell">{{ view === 'reviewed' ? 'Décision' : 'Motif' }}</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
          <tr v-for="i in items" :key="i.id" class="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50" @click="selected = i.id">
            <td class="max-w-xs px-4 py-3">
              <p class="truncate">{{ i.preview }}</p>
              <p class="text-[11px] text-slate-400">#{{ i.id }} · {{ formatDate(i.received_at) }}</p>
            </td>
            <td class="hidden max-w-[12rem] truncate px-4 py-3 text-xs text-slate-500 md:table-cell">{{ i.source }}</td>
            <td class="px-4 py-3">
              <span class="rounded-full border px-2 py-0.5 text-xs" :class="STATUS_META[i.status].chip">{{ STATUS_META[i.status].label }} · {{ Math.round(i.score) }}</span>
            </td>
            <td class="hidden px-4 py-3 text-xs sm:table-cell">
              <template v-if="view === 'reviewed'">{{ i.review_label === 'phishing' ? '🔴 Phishing' : '🟢 Sans danger' }} <span class="text-slate-400">· {{ i.reviewer }}</span></template>
              <template v-else>{{ i.reason === 'reported' ? '🚩 Signalé' : '❓ Incertain' }}</template>
            </td>
            <td class="px-4 py-3 text-right text-xs font-semibold text-blue-600 dark:text-blue-400">Examiner →</td>
          </tr>
        </tbody>
      </table>
      <div v-if="total > perPage" class="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-xs text-slate-500 dark:border-slate-800">
        <span>{{ (page - 1) * perPage + 1 }}–{{ Math.min(page * perPage, total) }} sur {{ total }}</span>
        <div class="flex gap-2">
          <button class="rounded-lg border px-3 py-1.5 disabled:opacity-40 dark:border-slate-700" :disabled="page === 1" @click="page--">← Précédent</button>
          <button class="rounded-lg border px-3 py-1.5 disabled:opacity-40 dark:border-slate-700" :disabled="page * perPage >= total" @click="page++">Suivant →</button>
        </div>
      </div>
    </div>

    <ReviewDrawer :analysis-id="selected" @close="selected = null" @decided="onDecided" />
  </div>
</template>
