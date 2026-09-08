<template>
  <div class="space-y-6">
    <!-- Page Header -->
    <div>
      <h1 class="text-2xl font-bold text-slate-800 font-display">📜 Audit</h1>
      <p class="text-sm text-slate-500">Journal des actions administrateur et événements système</p>
    </div>

    <!-- Filters -->
    <div class="flex flex-wrap gap-3">
      <input type="text" placeholder="Rechercher..." class="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition w-full sm:w-48" />
      <select class="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white">
        <option>Toutes les actions</option>
        <option>Connexion</option>
        <option>Modification</option>
        <option>Suppression</option>
        <option>Signalement</option>
      </select>
      <input type="date" class="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
      <input type="date" class="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-slate-100 shadow-md overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 border-b border-slate-200">
            <tr>
              <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Acteur</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Cible</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">IP</th>
              <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
              <th class="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Statut</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="entry in auditLogs" :key="entry.id" class="hover:bg-slate-50/50 transition">
              <td class="px-4 py-3 text-xs font-medium text-slate-700">{{ entry.actor }}</td>
              <td class="px-4 py-3 text-xs text-slate-600">{{ entry.action }}</td>
              <td class="px-4 py-3 text-xs text-slate-600">{{ entry.target }}</td>
              <td class="px-4 py-3 text-xs font-mono text-slate-500">{{ entry.ip }}</td>
              <td class="px-4 py-3 text-xs text-slate-500">{{ entry.date }}</td>
              <td class="px-4 py-3 text-center">
                <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="entry.status === 'Succès' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'">
                  {{ entry.status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="flex items-center justify-between px-4 py-3 border-t border-slate-200">
        <p class="text-xs text-slate-500">Affichage 1-10 sur 342 entrées</p>
        <div class="flex gap-1">
          <button class="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 transition">Précédent</button>
          <button class="px-3 py-1 text-xs bg-blue-600 text-white rounded">1</button>
          <button class="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 transition">2</button>
          <button class="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 transition">Suivant</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const auditLogs = ref([
  { id: 1, actor: 'Lareine Tracy', action: '🔐 Connexion', target: 'Admin Panel', ip: '192.168.1.100', date: 'Aujourd\'hui, 14:32:12', status: 'Succès' },
  { id: 2, actor: 'Jean Dupont', action: '✏️ Modification', target: 'Utilisateur: marie@example.com', ip: '192.168.1.45', date: 'Aujourd\'hui, 13:15:08', status: 'Succès' },
  { id: 3, actor: 'Marie Kamdem', action: '🚨 Signalement', target: 'Phishing: "Compte MTN bloqué"', ip: '192.168.1.78', date: 'Aujourd\'hui, 11:22:45', status: 'Succès' },
  { id: 4, actor: 'Système', action: '🤖 Entraînement ML', target: 'Modèle v2.4.1', ip: '127.0.0.1', date: 'Aujourd\'hui, 08:32:00', status: 'Succès' },
  { id: 5, actor: 'Paul Nguea', action: '⛔ Échec connexion', target: 'Tentative de connexion', ip: '10.0.0.23', date: 'Hier, 22:45:11', status: 'Échec' },
])
</script>