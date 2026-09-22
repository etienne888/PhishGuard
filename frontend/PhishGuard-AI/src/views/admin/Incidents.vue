<template>
  <div class="space-y-6">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">⚠️ Gestion des incidents</h1>
        <p class="text-sm text-slate-500">Suivi des incidents de sécurité ouverts sur la plateforme</p>
      </div>
      <span class="px-2.5 py-1 rounded-full bg-red-100 text-red-700 text-xs font-semibold">{{ openCount }} ouverts</span>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div v-for="stat in stats" :key="stat.label" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-4">
        <div class="text-2xl font-bold tabular-nums" :class="stat.color">{{ stat.value }}</div>
        <div class="text-sm text-slate-500 mt-1">{{ stat.label }}</div>
      </div>
    </div>

    <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden">
      <div class="divide-y divide-slate-100 dark:divide-slate-800">
        <div v-for="incident in incidents" :key="incident.id" class="p-4 flex items-start gap-4 hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
          <span class="w-2 h-2 rounded-full mt-2 flex-shrink-0" :class="severityDot(incident.severity)" />
          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2 flex-wrap">
              <span class="font-mono text-xs text-slate-400">{{ incident.ref }}</span>
              <p class="font-medium text-slate-800 dark:text-slate-200 truncate">{{ incident.title }}</p>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">{{ incident.detail }}</p>
          </div>
          <span class="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full flex-shrink-0" :class="severityBadge(incident.severity)">{{ incident.severity }}</span>
          <select v-model="incident.status" class="text-xs border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg px-2 py-1 outline-none flex-shrink-0">
            <option value="open">Ouvert</option>
            <option value="investigating">Investigation</option>
            <option value="resolved">Résolu</option>
          </select>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Incident {
  id: number
  ref: string
  title: string
  detail: string
  severity: 'critical' | 'high' | 'medium'
  status: 'open' | 'investigating' | 'resolved'
}

const incidents = ref<Incident[]>([
  { id: 1, ref: 'INC-2026-0142', title: 'Campagne Mobile Money', detail: 'Investigation en cours · 18 utilisateurs ciblés', severity: 'critical', status: 'investigating' },
  { id: 2, ref: 'INC-2026-0141', title: 'Domaine typosquatté détecté', detail: 'mtn-secure-cm.tk bloqué automatiquement', severity: 'high', status: 'resolved' },
  { id: 3, ref: 'INC-2026-0139', title: 'Pic de signalements groupés', detail: '7 signalements similaires en 1h', severity: 'medium', status: 'open' },
])

const openCount = computed(() => incidents.value.filter(i => i.status !== 'resolved').length)
const stats = computed(() => [
  { label: 'Ouverts', value: incidents.value.filter(i => i.status === 'open').length, color: 'text-red-600' },
  { label: 'En investigation', value: incidents.value.filter(i => i.status === 'investigating').length, color: 'text-amber-600' },
  { label: 'Résolus (7j)', value: incidents.value.filter(i => i.status === 'resolved').length, color: 'text-emerald-600' },
])

function severityDot(s: Incident['severity']) {
  return s === 'critical' ? 'bg-red-500' : s === 'high' ? 'bg-amber-500' : 'bg-slate-400'
}
function severityBadge(s: Incident['severity']) {
  return s === 'critical' ? 'bg-red-100 text-red-700' : s === 'high' ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'
}
</script>
