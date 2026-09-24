<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { adminOpsService, type ReviewDetail, type ReviewLabel } from '@/services/admin.service'
import { useNotificationsStore } from '@/stores/notifications'
import { LEVEL_LABEL, SIGNAL_LABEL, STATUS_META, formatDate } from '@/utils/risk'

/** Admin view of one analysis + the ground-truth decision (feeds retraining). */
const props = defineProps<{ analysisId: number | null }>()
const emit = defineEmits<{ close: []; decided: [id: number] }>()
const toast = useNotificationsStore()

const item = ref<ReviewDetail | null>(null)
const loading = ref(false)
const note = ref('')
const saving = ref(false)

watch(() => props.analysisId, async (id) => {
  item.value = null
  note.value = ''
  if (id === null) return
  loading.value = true
  try {
    item.value = await adminOpsService.getReviewItem(id)
    note.value = item.value.review_note ?? ''
  } finally {
    loading.value = false
  }
}, { immediate: true })

const meta = computed(() => item.value ? STATUS_META[item.value.status] : null)
const disagreement = computed(() => {
  const i = item.value
  if (!i?.review_label) return false
  return (i.review_label === 'phishing') !== (i.status === 'phishing')
})

async function decide(label: ReviewLabel | 'reset') {
  if (!item.value) return
  saving.value = true
  try {
    const updated = await adminOpsService.decide(item.value.id, label, note.value)
    item.value = { ...item.value, ...updated }
    toast.push(label === 'reset' ? 'Décision annulée.' : label === 'phishing' ? 'Confirmé comme phishing.' : 'Marqué comme sans danger.', 'success')
    emit('decided', item.value.id)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="analysisId !== null" class="fixed inset-0 z-50 flex justify-end bg-slate-900/40" @click.self="emit('close')">
        <aside class="h-full w-full max-w-xl overflow-y-auto bg-white text-slate-800 shadow-2xl dark:bg-slate-900 dark:text-slate-100" role="dialog" aria-modal="true">
          <header class="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white px-5 py-4 dark:border-slate-800 dark:bg-slate-900">
            <div>
              <h2 class="font-bold">Analyse #{{ analysisId }}</h2>
              <p v-if="item" class="text-xs text-slate-500">{{ item.source }} · {{ formatDate(item.received_at) }}</p>
            </div>
            <button class="rounded-lg px-2 py-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Fermer" @click="emit('close')">✕</button>
          </header>

          <div v-if="loading" class="p-6 text-sm text-slate-500">Chargement…</div>

          <div v-else-if="item && meta" class="space-y-5 p-5">
            <!-- Engine verdict vs admin decision -->
            <div class="grid grid-cols-2 gap-3">
              <div class="rounded-xl border p-3" :class="meta.chip">
                <p class="text-[11px] font-semibold uppercase opacity-70">Verdict du moteur</p>
                <p class="mt-1 font-bold">{{ meta.emoji }} {{ meta.label }}</p>
                <p class="text-xs opacity-80">{{ Math.round(item.score) }}/100 · {{ LEVEL_LABEL[item.level ?? ''] ?? '—' }}</p>
              </div>
              <div class="rounded-xl border border-slate-200 p-3 dark:border-slate-700">
                <p class="text-[11px] font-semibold uppercase text-slate-500">Décision admin</p>
                <p class="mt-1 font-bold">
                  {{ item.review_label === 'phishing' ? '🔴 Phishing confirmé' : item.review_label === 'safe' ? '🟢 Sans danger' : '⏳ En attente' }}
                </p>
                <p v-if="item.reviewer" class="text-xs text-slate-500">par {{ item.reviewer }}</p>
              </div>
            </div>
            <p v-if="disagreement" class="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-500/10 dark:text-amber-300">
              ⚠️ Le moteur s'est trompé sur ce message : il servira à corriger le modèle lors du prochain réentraînement.
            </p>

            <section v-if="item.reported_at" class="rounded-xl bg-red-50 p-3 text-sm dark:bg-red-500/10">
              <p class="font-semibold text-red-700 dark:text-red-300">🚩 Signalé le {{ formatDate(item.reported_at) }}</p>
              <p v-if="item.report_note" class="mt-1 text-red-800 dark:text-red-200">« {{ item.report_note }} »</p>
            </section>

            <section>
              <h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">Message</h3>
              <pre class="mt-1.5 whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-3 font-sans text-sm dark:bg-slate-800">{{ item.text }}</pre>
            </section>

            <section v-if="item.evidence.length">
              <h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">Indices détectés</h3>
              <ul class="mt-1.5 space-y-1 text-sm">
                <li v-for="e in item.evidence" :key="e" class="flex gap-2"><span class="text-slate-400">•</span>{{ e }}</li>
              </ul>
            </section>

            <section v-if="item.signals" class="grid grid-cols-2 gap-2 text-xs">
              <div v-for="(value, key) in item.signals" :key="key" class="rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-800">
                <span class="text-slate-500">{{ SIGNAL_LABEL[key] ?? key }}</span>
                <b class="float-right tabular-nums">{{ value == null ? '—' : Math.round(value) }}</b>
              </div>
            </section>

            <!-- Decision -->
            <section class="rounded-xl border border-slate-200 p-4 dark:border-slate-700">
              <h3 class="text-sm font-semibold">Votre décision</h3>
              <p class="mt-0.5 text-xs text-slate-500">Elle devient la « vérité terrain » exportée pour réentraîner le modèle.</p>
              <textarea v-model="note" rows="2" maxlength="1000" placeholder="Note (facultatif)"
                        class="mt-3 w-full rounded-lg border border-slate-200 bg-transparent p-2 text-sm outline-none focus:border-blue-400 dark:border-slate-700"></textarea>
              <div class="mt-3 flex flex-wrap gap-2">
                <button class="rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60" :disabled="saving" @click="decide('phishing')">🔴 Confirmer phishing</button>
                <button class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-60" :disabled="saving" @click="decide('safe')">🟢 Sans danger</button>
                <button v-if="item.review_label" class="rounded-lg border border-slate-200 px-4 py-2 text-sm dark:border-slate-700" :disabled="saving" @click="decide('reset')">Annuler la décision</button>
              </div>
            </section>
          </div>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-enter-active aside, .drawer-leave-active aside { transition: transform 0.25s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from aside, .drawer-leave-to aside { transform: translateX(100%); }
</style>
