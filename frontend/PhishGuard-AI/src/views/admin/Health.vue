<template>
  <div class="space-y-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">💚 Santé infrastructure</h1>
        <p class="text-sm text-slate-500">État en direct des services PhishGuard-AI</p>
      </div>
      <button @click="refresh" :disabled="loading" class="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 transition disabled:opacity-50">
        <i class="fas fa-rotate mr-1.5" :class="{ 'fa-spin': loading }"></i> Actualiser
      </button>
    </div>

    <div v-if="loadError" class="text-sm text-red-600 bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 rounded-lg px-4 py-2">{{ loadError }}</div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-5">
        <p class="text-xs text-slate-500 uppercase tracking-wider">Statut global</p>
        <p class="mt-1 text-lg font-bold" :class="health?.status === 'healthy' ? 'text-emerald-600' : 'text-amber-600'">
          {{ health?.status === 'healthy' ? '● Opérationnel' : health ? '● Dégradé' : '—' }}
        </p>
      </div>
      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-5">
        <p class="text-xs text-slate-500 uppercase tracking-wider">Base de données</p>
        <p class="mt-1 text-lg font-bold" :class="health?.db === 'connected' ? 'text-emerald-600' : 'text-red-600'">
          {{ health?.db === 'connected' ? '● Connectée' : health ? '● Indisponible' : '—' }}
        </p>
      </div>
      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-5">
        <p class="text-xs text-slate-500 uppercase tracking-wider">Moteur IA</p>
        <p class="mt-1 text-lg font-bold" :class="health?.ml_engine === 'loaded' ? 'text-emerald-600' : 'text-amber-600'">
          {{ health?.ml_engine === 'loaded' ? '● Chargé' : health ? '● Indisponible' : '—' }}
        </p>
      </div>
      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-5">
        <p class="text-xs text-slate-500 uppercase tracking-wider">Disponibilité API</p>
        <p class="mt-1 text-lg font-bold tabular-nums text-slate-800 dark:text-slate-100">{{ health?.uptime_seconds ?? '—' }}s</p>
      </div>
    </div>

    <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-6 shadow-sm">
      <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">Détails</h3>
      <dl class="grid sm:grid-cols-2 gap-3 text-sm">
        <div class="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-2"><dt class="text-slate-500">Version API</dt><dd class="font-medium">{{ health?.version ?? '—' }}</dd></div>
        <div class="flex justify-between border-b border-slate-100 dark:border-slate-800 pb-2"><dt class="text-slate-500">Fournisseur IA</dt><dd class="font-medium">{{ health?.ai_provider ?? '—' }}</dd></div>
      </dl>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { healthService, type HealthStatus } from '@/services'

const health = ref<HealthStatus | null>(null)
const loading = ref(false)
const loadError = ref<string | null>(null)

async function refresh() {
  loading.value = true
  loadError.value = null
  try {
    health.value = await healthService.getStatus()
  } catch {
    loadError.value = "Impossible de contacter l'API PhishGuard-AI."
  } finally {
    loading.value = false
  }
}

onMounted(refresh)
</script>
