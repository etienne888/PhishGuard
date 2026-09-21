  <template>
    <div class="space-y-6">
      <div class="flex items-start justify-between gap-4">
        <div>
          <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">📜 {{ t('admin.audit.title') }}</h1>
          <p class="text-sm text-slate-500">Journal immuable des actions administrateur & événements système</p>
        </div>
        <button class="px-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm font-medium rounded-lg hover:border-slate-300 transition inline-flex items-center gap-2">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" /></svg>
          {{ t('admin.audit.export') }}
        </button>
      </div>

      <!-- Filters -->
      <div class="flex flex-wrap gap-3">
        <div class="relative flex-1 min-w-[200px]">
          <svg class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.35-4.35" /></svg>
          <input v-model="query" type="text" :placeholder="t('admin.audit.search')"
            class="w-full pl-9 pr-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500" />
        </div>
        <select v-model="actionFilter" class="px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg text-sm outline-none">
          <option value="">Toutes les actions</option>
          <option>Connexion</option>
          <option>Modification</option>
          <option>Suppression</option>
          <option>Signalement</option>
          <option>Déploiement modèle</option>
        </select>
        <select v-model="statusFilter" class="px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg text-sm outline-none">
          <option value="">Tous les statuts</option>
          <option>Succès</option>
          <option>Échec</option>
        </select>
        <input type="date" class="px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg text-sm outline-none" />
      </div>

      <!-- Table -->
      <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Horodatage</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Acteur</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Action</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Ressource</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">IP</th>
                <th class="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Statut</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
              <tr v-for="entry in filteredLogs" :key="entry.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                <td class="px-4 py-3 text-xs font-mono text-slate-500 tabular-nums">{{ entry.ts }}</td>
                <td class="px-4 py-3 text-xs font-medium text-slate-700 dark:text-slate-200">{{ entry.actor }}</td>
                <td class="px-4 py-3 text-xs">
                  <span class="inline-flex items-center gap-1.5">
                    <span>{{ entry.actionIcon }}</span>
                    <span class="text-slate-600 dark:text-slate-300">{{ entry.action }}</span>
                  </span>
                </td>
                <td class="px-4 py-3 text-xs text-slate-600 dark:text-slate-400 max-w-xs truncate">{{ entry.target }}</td>
                <td class="px-4 py-3 text-xs font-mono text-slate-500">{{ entry.ip }}</td>
                <td class="px-4 py-3 text-center">
                  <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="entry.status === 'Succès' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'">{{ entry.status }}</span>
                </td>
              </tr>
              <tr v-if="filteredLogs.length === 0">
                <td colspan="6" class="px-4 py-12 text-center text-sm text-slate-400">Aucun événement ne correspond à vos filtres</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="flex items-center justify-between px-4 py-3 border-t border-slate-200 dark:border-slate-800">
          <p class="text-xs text-slate-500">Affichage 1-{{ filteredLogs.length }} sur {{ logs.length }} entrées</p>
          <div class="flex gap-1">
            <button class="px-3 py-1 text-xs border border-slate-200 dark:border-slate-800 rounded hover:bg-slate-50 dark:hover:bg-slate-800 transition">{{ t('admin.audit.previous') }}</button>
            <button class="px-3 py-1 text-xs bg-blue-600 text-white rounded">1</button>
            <button class="px-3 py-1 text-xs border border-slate-200 dark:border-slate-800 rounded hover:bg-slate-50 dark:hover:bg-slate-800 transition">{{ t('admin.audit.next') }}</button>
          </div>
        </div>
      </div>
    </div>
  </template>

  <script setup lang="ts">
  import { ref, computed } from 'vue'
  import { useI18n } from '@/i18n'

  const { t } = useI18n()

  const logs = ref([
    { id: 1, ts: '2026-09-15 14:32:12', actor: 'Lareine Tracy', action: 'Connexion', actionIcon: '🔐', target: 'Admin Panel', ip: '192.168.1.100', status: 'Succès' },
    { id: 2, ts: '2026-09-15 13:15:08', actor: 'Jean Dupont', action: 'Modification', actionIcon: '✏️', target: 'Utilisateur: marie@example.com', ip: '192.168.1.45', status: 'Succès' },
    { id: 3, ts: '2026-09-15 11:22:45', actor: 'Marie Kamdem', action: 'Signalement', actionIcon: '🚨', target: 'Phishing: "Compte MTN bloqué"', ip: '192.168.1.78', status: 'Succès' },
    { id: 4, ts: '2026-09-15 08:32:00', actor: 'Système', action: 'Déploiement modèle', actionIcon: '🤖', target: 'Modèle v2.4.1', ip: '127.0.0.1', status: 'Succès' },
    { id: 5, ts: '2026-09-14 22:45:11', actor: 'Paul Nguea', action: 'Connexion', actionIcon: '🔐', target: 'Tentative de connexion', ip: '10.0.0.23', status: 'Échec' },
    { id: 6, ts: '2026-09-14 20:10:04', actor: 'Lareine Tracy', action: 'Suppression', actionIcon: '🗑️', target: 'Utilisateur: fraude@suspect.cm', ip: '192.168.1.100', status: 'Succès' },
  ])

  const query = ref('')
  const actionFilter = ref('')
  const statusFilter = ref('')

  const filteredLogs = computed(() => {
    const q = query.value.toLowerCase()
    return logs.value.filter(l => {
      const matchQ = !q || l.actor.toLowerCase().includes(q) || l.action.toLowerCase().includes(q) || l.target.toLowerCase().includes(q)
      const matchA = !actionFilter.value || l.action === actionFilter.value
      const matchS = !statusFilter.value || l.status === statusFilter.value
      return matchQ && matchA && matchS
    })
  })
  </script>