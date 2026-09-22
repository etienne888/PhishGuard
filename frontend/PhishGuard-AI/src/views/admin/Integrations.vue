<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">🔌 Intégrations</h1>
      <p class="text-sm text-slate-500">Connectez PhishGuard-AI à vos outils SOC, SIEM et sources de renseignement</p>
    </div>

    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div v-for="integration in integrations" :key="integration.id" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-5 shadow-sm">
        <div class="flex items-start justify-between">
          <div>
            <p class="font-semibold text-slate-800 dark:text-slate-100">{{ integration.name }}</p>
            <p class="text-xs text-slate-500 mt-0.5">{{ integration.description }}</p>
          </div>
          <span class="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full flex-shrink-0" :class="integration.connected ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'">
            {{ integration.connected ? 'Connecté' : 'Déconnecté' }}
          </span>
        </div>
        <div class="mt-4 flex items-center justify-between">
          <span class="text-[11px] uppercase tracking-wide text-slate-400">{{ integration.category }}</span>
          <button @click="integration.connected = !integration.connected"
            class="text-xs font-medium px-3 py-1.5 rounded-lg transition"
            :class="integration.connected ? 'bg-red-50 text-red-600 hover:bg-red-100' : 'bg-blue-50 text-blue-600 hover:bg-blue-100'">
            {{ integration.connected ? 'Déconnecter' : 'Connecter' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const integrations = ref([
  { id: 'slack', name: 'Slack', description: 'Alertes temps réel', connected: true, category: 'alerting' },
  { id: 'teams', name: 'Microsoft Teams', description: 'Alertes temps réel', connected: false, category: 'alerting' },
  { id: 'splunk', name: 'Splunk', description: 'Export SIEM', connected: true, category: 'siem' },
  { id: 'virustotal', name: 'VirusTotal', description: 'Enrichissement IOC', connected: true, category: 'threat intel' },
  { id: 'abuseipdb', name: 'AbuseIPDB', description: 'Réputation IP', connected: false, category: 'threat intel' },
  { id: 'cirt-cm', name: 'CIRT-CM', description: 'Signalement national', connected: true, category: 'gouvernemental' },
])
</script>
