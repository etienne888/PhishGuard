<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { adminOpsService, type WhitelistCategory, type WhitelistEntry } from '@/services/admin.service'
import { useNotificationsStore } from '@/stores/notifications'
import { ApiError } from '@/services/http'

/** Official Cameroonian domains. The detection engine trusts senders from these and flags look-alikes. */
const toast = useNotificationsStore()

const CATEGORIES: Record<WhitelistCategory, string> = {
  mobile_money: '📱 Mobile Money', banking: '🏦 Banque', telecom: '📡 Télécom', government: '🏛️ Administration', other: '• Autre',
}

const items = ref<WhitelistEntry[]>([])
const q = ref('')
const loading = ref(false)
const form = ref({ domain: '', institution: '', category: 'banking' as WhitelistCategory })
const adding = ref(false)

const activeCount = computed(() => items.value.filter((i) => i.is_active).length)

async function load() {
  loading.value = true
  try { items.value = (await adminOpsService.listWhitelist(q.value)).items } finally { loading.value = false }
}

let searchTimer: number | undefined
watch(q, () => { window.clearTimeout(searchTimer); searchTimer = window.setTimeout(load, 300) })
onMounted(load)

async function add() {
  adding.value = true
  try {
    await adminOpsService.createWhitelist(form.value)
    toast.push(`${form.value.domain} ajouté à la liste blanche.`, 'success')
    form.value = { domain: '', institution: '', category: form.value.category }
    await load()
  } catch (e) {
    if (!(e instanceof ApiError)) toast.push("Impossible d'ajouter ce domaine.", 'error')
  } finally {
    adding.value = false
  }
}

async function toggle(entry: WhitelistEntry) {
  const updated = await adminOpsService.updateWhitelist(entry.id, { is_active: !entry.is_active })
  Object.assign(entry, updated)
}

async function remove(entry: WhitelistEntry) {
  if (!confirm(`Retirer ${entry.domain} (${entry.institution}) de la liste blanche ?`)) return
  await adminOpsService.deleteWhitelist(entry.id)
  items.value = items.value.filter((i) => i.id !== entry.id)
  toast.push('Domaine retiré.', 'success')
}
</script>

<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-2xl font-bold">Liste blanche des institutions</h1>
      <p class="text-sm text-slate-500">
        Domaines officiels camerounais. Le moteur fait confiance à ces expéditeurs et repère les domaines qui les imitent
        (ex. <code>mtnmobil3money.com</code>). {{ activeCount }} domaine(s) actif(s).
      </p>
    </div>

    <form class="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 md:grid-cols-[1fr_1fr_12rem_auto]" @submit.prevent="add">
      <input v-model="form.domain" required placeholder="Domaine (ex. afrilandfirstbank.com)"
             class="rounded-xl border border-slate-200 bg-transparent px-3 py-2 text-sm outline-none focus:border-blue-400 dark:border-slate-700" />
      <input v-model="form.institution" required placeholder="Institution (ex. Afriland First Bank)"
             class="rounded-xl border border-slate-200 bg-transparent px-3 py-2 text-sm outline-none focus:border-blue-400 dark:border-slate-700" />
      <select v-model="form.category" class="rounded-xl border border-slate-200 bg-transparent px-3 py-2 text-sm dark:border-slate-700">
        <option v-for="(label, key) in CATEGORIES" :key="key" :value="key">{{ label }}</option>
      </select>
      <button class="rounded-xl bg-blue-600 px-5 py-2 text-sm font-semibold text-white disabled:opacity-60" :disabled="adding">+ Ajouter</button>
    </form>

    <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div class="border-b border-slate-100 p-3 dark:border-slate-800">
        <input v-model="q" type="search" placeholder="Rechercher un domaine ou une institution…"
               class="w-full rounded-xl border border-slate-200 bg-transparent px-3 py-2 text-sm outline-none focus:border-blue-400 dark:border-slate-700 sm:w-80" />
      </div>
      <p v-if="!loading && !items.length" class="p-8 text-center text-sm text-slate-400">Aucun domaine.</p>
      <ul v-else class="divide-y divide-slate-100 dark:divide-slate-800" :class="{ 'opacity-60': loading }">
        <li v-for="e in items" :key="e.id" class="flex flex-wrap items-center gap-3 px-4 py-3">
          <code class="rounded bg-slate-100 px-2 py-1 text-sm dark:bg-slate-800" :class="{ 'line-through opacity-50': !e.is_active }">{{ e.domain }}</code>
          <span class="min-w-0 flex-1 text-sm">{{ e.institution }} <span class="text-xs text-slate-400">· {{ CATEGORIES[e.category] ?? e.category }}</span></span>
          <button class="rounded-full px-3 py-1 text-xs font-semibold"
                  :class="e.is_active ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300' : 'bg-slate-100 text-slate-500 dark:bg-slate-800'"
                  :title="e.is_active ? 'Cliquer pour désactiver' : 'Cliquer pour activer'" @click="toggle(e)">
            {{ e.is_active ? '✓ Actif' : 'Désactivé' }}
          </button>
          <button class="rounded-lg px-2 py-1 text-xs text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-500/10" @click="remove(e)">Supprimer</button>
        </li>
      </ul>
    </div>
  </div>
</template>
