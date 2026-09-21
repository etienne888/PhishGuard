    <template>
    <div class="space-y-6">
        <!-- Page Header -->
        <div class="flex items-start justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">🚨 {{ t('admin.reports.title') }}</h1>
            <p class="text-sm text-slate-500">Modération des signalements de phishing soumis par les utilisateurs</p>
        </div>
        <div class="flex items-center gap-2 text-xs">
            <span class="px-2.5 py-1 rounded-full bg-amber-100 text-amber-700 font-medium">12 en attente</span>
            <span class="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700 font-medium">8 confirmés</span>
        </div>
        </div>

        <!-- Filters -->
        <div class="flex flex-wrap gap-3">
        <div class="relative flex-1 min-w-[200px]">
            <svg class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.35-4.35" /></svg>
            <input v-model="searchQuery" type="text" :placeholder="t('admin.reports.search')"
            class="w-full pl-9 pr-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition" />
        </div>
        <select v-model="statusFilter" class="px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg text-sm outline-none">
            <option value="">Tous les statuts</option>
            <option>En attente</option>
            <option>Confirmé</option>
            <option>Rejeté</option>
        </select>
        <select v-model="severityFilter" class="px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg text-sm outline-none">
            <option value="">Toutes les sévérités</option>
            <option value="critical">Critique (≥90)</option>
            <option value="high">Élevée (70–89)</option>
            <option value="medium">Moyenne (50–69)</option>
            <option value="low">Faible (&lt;50)</option>
        </select>
        <div class="flex gap-2 ml-auto">
            <button @click="bulkAction('confirm')" :disabled="!selectedIds.length"
            class="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition disabled:opacity-40 disabled:shadow-none">
            <i class="fas fa-check mr-1.5"></i> Confirmer ({{ selectedIds.length }})
            </button>
            <button @click="bulkAction('reject')" :disabled="!selectedIds.length"
            class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg shadow-md shadow-red-500/25 hover:shadow-red-500/40 transition disabled:opacity-40 disabled:shadow-none">
            <i class="fas fa-times mr-1.5"></i> Rejeter
            </button>
        </div>
        </div>

        <!-- Table -->
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
                <tr>
                <th class="w-8 px-4 py-3"><input type="checkbox" :checked="allSelected" @change="toggleAll" class="rounded border-slate-300" /></th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Expéditeur</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Objet / URL</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Soumis par</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Risque</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">IA</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Statut</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
                <th class="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                <tr v-for="report in filteredReports" :key="report.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                <td class="px-4 py-3"><input type="checkbox" :value="report.id" v-model="selectedIds" class="rounded border-slate-300" /></td>
                <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                    <span class="w-7 h-7 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-[10px] font-bold">{{ initials(report.sender) }}</span>
                    <span class="text-xs text-slate-600 dark:text-slate-300 font-medium truncate max-w-[160px]">{{ report.sender }}</span>
                    </div>
                </td>
                <td class="px-4 py-3 text-xs text-slate-600 dark:text-slate-400 max-w-xs truncate">{{ report.subject }}</td>
                <td class="px-4 py-3 text-xs text-slate-500">{{ report.submittedBy }}</td>
                <td class="px-4 py-3">
                    <div class="flex items-center gap-2 w-24">
                    <div class="h-1.5 flex-1 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                        <div class="h-full rounded-full" :class="riskColor(report.riskScore)" :style="{ width: report.riskScore + '%' }" />
                    </div>
                    <span class="text-xs font-semibold tabular-nums" :class="riskTextColor(report.riskScore)">{{ report.riskScore }}</span>
                    </div>
                </td>
                <td class="px-4 py-3">
                    <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">94%</span>
                </td>
                <td class="px-4 py-3">
                    <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="statusBadge(report.status)">{{ report.status }}</span>
                </td>
                <td class="px-4 py-3 text-xs text-slate-500">{{ report.date }}</td>
                <td class="px-4 py-3">
                    <div class="flex items-center justify-center gap-1">
                    <button @click="viewReport(report)" class="p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-500/10 text-blue-600 transition" title="Investiguer">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" /><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                    </button>
                    <button @click="quickAction(report, 'Confirmé')" class="p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-500/10 text-emerald-600 transition" title="Confirmer">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 13l4 4L19 7" /></svg>
                    </button>
                    <button @click="quickAction(report, 'Rejeté')" class="p-1.5 rounded hover:bg-red-50 dark:hover:bg-red-500/10 text-red-600 transition" title="Rejeter">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                    </div>
                </td>
                </tr>
                <tr v-if="filteredReports.length === 0">
                <td colspan="9" class="px-4 py-12 text-center text-sm text-slate-400">
                    <div class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 dark:bg-slate-800">
                    <svg class="w-6 h-6 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><path d="M22 4L12 14.01l-3-3" /></svg>
                    </div>
                    Aucun signalement ne correspond à vos filtres
                </td>
                </tr>
            </tbody>
            </table>
        </div>
        <div class="flex items-center justify-between px-4 py-3 border-t border-slate-200 dark:border-slate-800">
            <p class="text-xs text-slate-500">Affichage 1-{{ filteredReports.length }} sur {{ reports.length }} signalements</p>
            <div class="flex gap-1">
            <button class="px-3 py-1 text-xs border border-slate-200 dark:border-slate-800 rounded hover:bg-slate-50 dark:hover:bg-slate-800 transition">Précédent</button>
            <button class="px-3 py-1 text-xs bg-blue-600 text-white rounded">1</button>
            <button class="px-3 py-1 text-xs border border-slate-200 dark:border-slate-800 rounded hover:bg-slate-50 dark:hover:bg-slate-800 transition">2</button>
            <button class="px-3 py-1 text-xs border border-slate-200 dark:border-slate-800 rounded hover:bg-slate-50 dark:hover:bg-slate-800 transition">Suivant</button>
            </div>
        </div>
        </div>

        <!-- =============== DETAIL DRAWER WITH AI EXPLANATION =============== -->
        <div v-if="selectedReport" class="fixed inset-0 z-50 flex items-stretch justify-end bg-slate-900/60 backdrop-blur-sm" @click.self="selectedReport = null">
        <div class="w-full max-w-3xl bg-white dark:bg-slate-900 shadow-2xl overflow-y-auto">
            <div class="sticky top-0 bg-white/90 dark:bg-slate-900/90 backdrop-blur border-b border-slate-200 dark:border-slate-800 px-6 py-4 flex items-center justify-between z-10">
            <div>
                <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100">Investigation du signalement</h3>
                <p class="text-xs text-slate-500">Réf. #PG-{{ selectedReport.id.toString().padStart(5, '0') }}</p>
            </div>
            <button @click="selectedReport = null" class="text-slate-400 hover:text-slate-600 transition">✕</button>
            </div>

            <div class="p-6 space-y-6">

            <!-- Threat summary -->
            <div class="rounded-xl border border-red-200 dark:border-red-500/30 bg-red-50 dark:bg-red-500/5 p-5">
                <div class="flex items-start justify-between gap-4">
                <div>
                    <div class="text-[11px] font-semibold uppercase tracking-wide text-red-600 dark:text-red-400">Phishing détecté</div>
                    <div class="mt-1 text-2xl font-bold text-slate-800 dark:text-slate-100">{{ selectedReport.subject }}</div>
                    <div class="text-sm text-slate-500 mt-1">Expéditeur : {{ selectedReport.sender }}</div>
                </div>
                <div class="text-right">
                    <div class="text-[11px] uppercase tracking-wide text-slate-500">Score de risque</div>
                    <div class="text-3xl font-bold tabular-nums text-red-600">{{ selectedReport.riskScore }}<span class="text-base text-red-400">/100</span></div>
                    <div class="text-[11px] uppercase tracking-wide text-slate-500 mt-1">Sévérité</div>
                    <div class="text-sm font-bold text-red-600">{{ severityLabel(selectedReport.riskScore) }}</div>
                </div>
                </div>
            </div>

            <!-- Why was this flagged? -->
            <div class="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                <div class="px-5 py-3 bg-slate-900 text-white flex items-center gap-2">
                <svg class="w-4 h-4 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v1a3 3 0 0 0-3 3v1a3 3 0 0 0 0 6v1a3 3 0 0 0 3 3v1a3 3 0 0 0 6 0v-1a3 3 0 0 0 3-3v-1a3 3 0 0 0 0-6v-1a3 3 0 0 0-3-3V5a3 3 0 0 0-3-3z" /></svg>
                <span class="text-sm font-semibold">Pourquoi PhishGuard-AI a signalé cet email</span>
                </div>
                <div class="p-5 space-y-3">
                <div v-for="ind in explanation(selectedReport)" :key="ind.label" class="flex items-center gap-3">
                    <span class="w-56 text-xs text-slate-600 dark:text-slate-300 truncate">{{ ind.label }}</span>
                    <div class="flex-1 h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                    <div class="h-full rounded-full bg-gradient-to-r from-amber-400 to-red-500 transition-all duration-700"
                        :style="{ width: (ind.weight / 30) * 100 + '%' }" />
                    </div>
                    <span class="w-10 text-right text-xs font-semibold text-slate-700 dark:text-slate-200 tabular-nums">+{{ ind.weight }}</span>
                </div>
                <div class="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-sm">
                    <span class="text-slate-500">Score de risque final</span>
                    <span class="font-bold text-slate-800 dark:text-slate-100 tabular-nums">{{ selectedReport.riskScore }}/100</span>
                </div>
                </div>
            </div>

            <!-- Sender analysis -->
            <div class="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                <div class="px-5 py-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Analyse de l'expéditeur</span>
                </div>
                <div class="p-5 grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
                <div><div class="text-xs text-slate-500">Domaine</div><div class="font-mono text-xs">{{ domain(selectedReport.sender) }}</div></div>
                <div><div class="text-xs text-slate-500">Âge du domaine</div><div class="text-xs">14 jours</div></div>
                <div><div class="text-xs text-slate-500">Réputation</div><div class="text-xs font-semibold text-red-600">Malveillante</div></div>
                <div><div class="text-xs text-slate-500">SPF</div><div class="text-xs text-red-600 font-semibold">Échec</div></div>
                <div><div class="text-xs text-slate-500">DKIM</div><div class="text-xs text-amber-600 font-semibold">Absent</div></div>
                <div><div class="text-xs text-slate-500">DMARC</div><div class="text-xs text-red-600 font-semibold">Échec</div></div>
                </div>
            </div>

            <!-- URL analysis -->
            <div class="rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                <div class="px-5 py-3 border-b border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50">
                <span class="text-xs font-semibold uppercase tracking-wider text-slate-500">Analyse des URLs</span>
                </div>
                <div class="p-5 space-y-2 text-sm">
                <div class="flex items-center gap-2 text-xs">
                    <span class="px-2 py-0.5 rounded-full bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300 font-semibold">MALVEILLANTE</span>
                    <span class="font-mono text-slate-600 dark:text-slate-300 truncate">http://mtn-secure-cm.tk/verify</span>
                </div>
                <ul class="text-xs text-slate-600 dark:text-slate-400 space-y-1 pl-4 list-disc">
                    <li>Domaine enregistré il y a 14 jours</li>
                    <li>Similarité au domaine officiel : 82%</li>
                    <li>Pas de HTTPS (HTTP en clair)</li>
                    <li>Chaîne de redirection : 3 sauts détectés</li>
                </ul>
                </div>
            </div>

            <!-- Original content -->
            <div class="rounded-xl border border-slate-200 dark:border-slate-800 p-5">
                <p class="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">Contenu original</p>
                <p class="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono bg-slate-50 dark:bg-slate-800/40 rounded-lg p-4 border border-slate-100 dark:border-slate-800">{{ selectedReport.content }}</p>
            </div>

            <!-- Actions -->
            <div class="flex flex-wrap gap-2 pt-2">
                <button @click="quickAction(selectedReport, 'Confirmé')"
                class="flex-1 min-w-[140px] py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-semibold rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition">
                ✓ Confirmer la menace
                </button>
                <button @click="quickAction(selectedReport, 'Rejeté')"
                class="flex-1 min-w-[140px] py-2.5 bg-red-600 text-white text-sm font-semibold rounded-lg shadow-md shadow-red-500/25 hover:shadow-red-500/40 transition">
                ✕ Rejeter le signalement
                </button>
                <button class="flex-1 min-w-[140px] py-2.5 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-sm font-semibold rounded-lg transition">
                ↗ Escalader en incident
                </button>
            </div>
            </div>
        </div>
        </div>
    </div>
    </template>

    <script setup lang="ts">
    import { ref, computed } from 'vue'
    import { useI18n } from '@/i18n'

    const { t } = useI18n()

    interface Report {
    id: number
    sender: string
    subject: string
    submittedBy: string
    riskScore: number
    status: string
    date: string
    content?: string
    mlBreakdown?: { phishing: number; legitimate: number; suspicious: number }
    }

    const reports = ref<Report[]>([
    { id: 1, sender: 'support@mtn-secure.tk', subject: 'Votre compte MTN a été bloqué', submittedBy: 'jean@example.com', riskScore: 92, status: 'En attente', date: 'Aujourd\'hui, 10:32' },
    { id: 2, sender: 'orange@verification.cm', subject: 'Confirmation de transaction Orange Money', submittedBy: 'marie@example.com', riskScore: 78, status: 'Confirmé', date: 'Hier, 16:15' },
    { id: 3, sender: 'banque@afriland-secure.ga', subject: 'URGENT: Votre compte a été compromis', submittedBy: 'paul@example.com', riskScore: 95, status: 'En attente', date: 'Hier, 09:45' },
    { id: 4, sender: 'info@camtel.cm', subject: 'Offre spéciale Camtel - 50% de réduction', submittedBy: 'sarah@example.com', riskScore: 45, status: 'Rejeté', date: '2 sept. 2026' },
    ])

    const selectedReport = ref<Report | null>(null)
    const selectedIds = ref<number[]>([])
    const searchQuery = ref('')
    const statusFilter = ref('')
    const severityFilter = ref('')

    const filteredReports = computed(() => {
    const q = searchQuery.value.toLowerCase()
    return reports.value.filter(r => {
        const matchQ = !q || r.sender.toLowerCase().includes(q) || r.subject.toLowerCase().includes(q) || r.submittedBy.toLowerCase().includes(q)
        const matchStatus = !statusFilter.value || r.status === statusFilter.value
        const matchSev = !severityFilter.value ||
        (severityFilter.value === 'critical' && r.riskScore >= 90) ||
        (severityFilter.value === 'high' && r.riskScore >= 70 && r.riskScore < 90) ||
        (severityFilter.value === 'medium' && r.riskScore >= 50 && r.riskScore < 70) ||
        (severityFilter.value === 'low' && r.riskScore < 50)
        return matchQ && matchStatus && matchSev
    })
    })

    const allSelected = computed(() => filteredReports.value.length > 0 && filteredReports.value.every(r => selectedIds.value.includes(r.id)))

    function toggleAll(e: Event) {
    const checked = (e.target as HTMLInputElement).checked
    selectedIds.value = checked ? filteredReports.value.map(r => r.id) : []
    }

    function bulkAction(action: 'confirm' | 'reject') {
    if (!selectedIds.value.length) return
    const count = selectedIds.value.length
    const label = action === 'confirm' ? 'confirmer' : 'rejeter'
    if (!confirm(`Voulez-vous ${label} ${count} signalement(s) ? Cette action sera journalisée dans l'audit.`)) return
    reports.value.forEach(r => {
        if (selectedIds.value.includes(r.id)) r.status = action === 'confirm' ? 'Confirmé' : 'Rejeté'
    })
    selectedIds.value = []
    }

    function quickAction(report: Report, status: string) {
    if (status === 'Confirmé' && !confirm(`Confirmer "${report.subject}" comme menace ? Cette action déclenchera le blocage global du domaine.`)) return
    if (status === 'Rejeté' && !confirm(`Rejeter le signalement "${report.subject}" ?`)) return
    report.status = status
    selectedReport.value = { ...report }
    }

    function viewReport(report: Report) {
    selectedReport.value = {
        ...report,
        content: 'Cher client, votre compte Mobile Money a été bloqué pour des raisons de sécurité. Veuillez cliquer sur le lien ci-dessous pour réactiver votre compte: http://mtn-secure-cm.tk/verify',
        mlBreakdown: { phishing: 85, legitimate: 10, suspicious: 5 }
    }
    }

    function explanation(report: Report) {
    return [
        { label: 'URL suspecte', weight: 30 },
        { label: 'Anomalie du domaine expéditeur', weight: 24 },
        { label: 'Demande d\'identifiants', weight: 18 },
        { label: 'Langage d\'urgence', weight: 12 },
        { label: 'Usurpation de marque', weight: Math.min(10, Math.round(report.riskScore / 10)) },
    ]
    }

    const initials = (email?: string) => (email ?? '').split('@')[0]?.slice(0, 2).toUpperCase() || 'NA'
    const domain = (email?: string) => (email ?? '').split('@')[1] || ''
    const riskColor = (s: number) => s >= 80 ? 'bg-red-500' : s >= 50 ? 'bg-amber-500' : 'bg-emerald-500'
    const riskTextColor = (s: number) => s >= 80 ? 'text-red-600' : s >= 50 ? 'text-amber-600' : 'text-emerald-600'
    const severityLabel = (s: number) => s >= 90 ? 'CRITIQUE' : s >= 70 ? 'ÉLEVÉE' : s >= 50 ? 'MOYENNE' : 'FAIBLE'
    const statusBadge = (s: string) => s === 'En attente' ? 'bg-amber-100 text-amber-700' : s === 'Confirmé' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'
    </script>