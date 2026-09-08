<template>
    <div class="space-y-6">
        <!-- Page Header -->
        <div>
            <h1 class="text-2xl font-bold text-slate-800 font-display">🚨 Signalements</h1>
            <p class="text-sm text-slate-500">Modération des signalements de phishing soumis par les utilisateurs</p>
        </div>

        <!-- Filters -->
        <div class="flex flex-wrap gap-3">
            <select
                class="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white">
                <option>Tous les statuts</option>
                <option>En attente</option>
                <option>Confirmé</option>
                <option>Rejeté</option>
            </select>
            <input type="date"
                class="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
            <input type="date"
                class="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
            <div class="flex gap-2 ml-auto">
                <button
                    class="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition">
                    <i class="fas fa-check mr-1.5"></i> Confirmer
                </button>
                <button
                    class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg shadow-md shadow-red-500/25 hover:shadow-red-500/40 transition">
                    <i class="fas fa-times mr-1.5"></i> Rejeter
                </button>
            </div>
        </div>

        <!-- Table -->
        <div class="bg-white rounded-xl border border-slate-100 shadow-md overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead class="bg-slate-50 border-b border-slate-200">
                        <tr>
                            <th class="w-8 px-4 py-3"><input type="checkbox" class="rounded border-slate-300" /></th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Expéditeur</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Objet/URL</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Soumis par</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Risque</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Statut</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Date</th>
                            <th
                                class="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <tr v-for="report in reports" :key="report.id" class="hover:bg-slate-50/50 transition">
                            <td class="px-4 py-3"><input type="checkbox" class="rounded border-slate-300" /></td>
                            <td class="px-4 py-3 text-xs text-slate-600 font-medium">{{ report.sender }}</td>
                            <td class="px-4 py-3 text-xs text-slate-600 max-w-xs truncate">{{ report.subject }}</td>
                            <td class="px-4 py-3 text-xs text-slate-500">{{ report.submittedBy }}</td>
                            <td class="px-4 py-3">
                                <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="report.riskScore >= 80 ? 'bg-red-100 text-red-700' :
                                        report.riskScore >= 50 ? 'bg-yellow-100 text-yellow-700' :
                                            'bg-emerald-100 text-emerald-700'
                                    ">
                                    {{ report.riskScore }}%
                                </span>
                            </td>
                            <td class="px-4 py-3">
                                <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="report.status === 'En attente' ? 'bg-yellow-100 text-yellow-700' :
                                        report.status === 'Confirmé' ? 'bg-red-100 text-red-700' :
                                            'bg-slate-100 text-slate-600'
                                    ">
                                    {{ report.status }}
                                </span>
                            </td>
                            <td class="px-4 py-3 text-xs text-slate-500">{{ report.date }}</td>
                            <td class="px-4 py-3">
                                <div class="flex items-center justify-center gap-1">
                                    <button @click="viewReport(report)"
                                        class="p-1.5 rounded hover:bg-blue-50 text-blue-600 transition"
                                        title="Voir détails">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                        </svg>
                                    </button>
                                    <button class="p-1.5 rounded hover:bg-emerald-50 text-emerald-600 transition"
                                        title="Confirmer">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M5 13l4 4L19 7" />
                                        </svg>
                                    </button>
                                    <button class="p-1.5 rounded hover:bg-red-50 text-red-600 transition"
                                        title="Rejeter">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M6 18L18 6M6 6l12 12" />
                                        </svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div class="flex items-center justify-between px-4 py-3 border-t border-slate-200">
                <p class="text-xs text-slate-500">Affichage 1-8 sur 47 signalements</p>
                <div class="flex gap-1">
                    <button
                        class="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 transition">Précédent</button>
                    <button class="px-3 py-1 text-xs bg-blue-600 text-white rounded">1</button>
                    <button
                        class="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 transition">2</button>
                    <button
                        class="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 transition">Suivant</button>
                </div>
            </div>
        </div>

        <!-- Report Detail Drawer -->
        <div v-if="selectedReport"
            class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
            <div class="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl max-h-[90vh] overflow-y-auto">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold text-slate-800 font-display">Détails du signalement</h3>
                    <button @click="selectedReport = null"
                        class="text-slate-400 hover:text-slate-600 transition">✕</button>
                </div>
                <div class="space-y-4 text-sm">
                    <div class="grid grid-cols-2 gap-3">
                        <div><span class="font-medium text-slate-600">Expéditeur:</span> {{ selectedReport.sender }}
                        </div>
                        <div><span class="font-medium text-slate-600">Soumis par:</span> {{ selectedReport.submittedBy
                            }}</div>
                        <div><span class="font-medium text-slate-600">Risque:</span> {{ selectedReport.riskScore }}%
                        </div>
                        <div><span class="font-medium text-slate-600">Statut:</span> {{ selectedReport.status }}</div>
                    </div>
                    <div class="bg-slate-50 rounded-lg p-4 border border-slate-200">
                        <p class="font-medium text-slate-600 mb-2">Contenu du message:</p>
                        <p class="text-slate-700 whitespace-pre-wrap">{{ selectedReport.content }}</p>
                    </div>
                    <div class="bg-slate-50 rounded-lg p-4 border border-slate-200">
                        <p class="font-medium text-slate-600 mb-2">Détection ML:</p>
                        <div class="space-y-2">
                            <div class="flex items-center gap-2">
                                <span class="text-xs text-slate-500 w-24">Phishing</span>
                                <div class="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                                    <div class="h-full bg-red-500 rounded-full"
                                        :style="{ width: selectedReport.mlBreakdown?.phishing || 85 + '%' }"></div>
                                </div>
                                <span class="text-xs font-medium">{{ selectedReport.mlBreakdown?.phishing || 85
                                    }}%</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="text-xs text-slate-500 w-24">Légitime</span>
                                <div class="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                                    <div class="h-full bg-emerald-500 rounded-full"
                                        :style="{ width: selectedReport.mlBreakdown?.legitimate || 10 + '%' }"></div>
                                </div>
                                <span class="text-xs font-medium">{{ selectedReport.mlBreakdown?.legitimate || 10
                                    }}%</span>
                            </div>
                            <div class="flex items-center gap-2">
                                <span class="text-xs text-slate-500 w-24">Suspect</span>
                                <div class="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                                    <div class="h-full bg-yellow-500 rounded-full"
                                        :style="{ width: selectedReport.mlBreakdown?.suspicious || 5 + '%' }"></div>
                                </div>
                                <span class="text-xs font-medium">{{ selectedReport.mlBreakdown?.suspicious || 5
                                    }}%</span>
                            </div>
                        </div>
                    </div>
                    <div class="flex gap-2 pt-2">
                        <button
                            class="flex-1 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition">Confirmer</button>
                        <button
                            class="flex-1 py-2 bg-red-600 text-white text-sm font-medium rounded-lg shadow-md shadow-red-500/25 hover:shadow-red-500/40 transition">Rejeter</button>
                        <button
                            class="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition">Escalader</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

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

const viewReport = (report: Report) => {
    selectedReport.value = {
        ...report,
        content: 'Cher client, votre compte Mobile Money a été bloqué pour des raisons de sécurité. Veuillez cliquer sur le lien ci-dessous pour réactiver votre compte: http://mtn-secure-cm.tk/verify',
        mlBreakdown: { phishing: 85, legitimate: 10, suspicious: 5 }
    }
}
</script>