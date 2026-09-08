<template>
    <div class="space-y-6">
        <!-- Page Header -->
        <div>
            <h1 class="text-2xl font-bold text-slate-800 font-display">🤖 Modèles ML</h1>
            <p class="text-sm text-slate-500">Gestion des modèles de détection de phishing</p>
        </div>

        <!-- Current Model Card -->
        <div class="bg-white rounded-xl p-6 border border-slate-100 shadow-md">
            <div class="flex items-start justify-between">
                <div>
                    <div class="flex items-center gap-3">
                        <h3 class="text-lg font-bold text-slate-800 font-display">Modèle actuel</h3>
                        <span
                            class="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-medium">Version
                            {{ currentModel.version }}</span>
                    </div>
                    <p class="text-sm text-slate-500 mt-1">Entraîné le {{ currentModel.lastTrained }}</p>
                </div>
                <button
                    class="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition">
                    <i class="fas fa-rotate-right mr-1.5"></i> Réentraîner
                </button>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-4">
                <div class="bg-slate-50 rounded-lg p-3 text-center">
                    <p class="text-xs text-slate-500">Précision</p>
                    <p class="text-lg font-bold text-slate-800">{{ currentModel.accuracy }}%</p>
                </div>
                <div class="bg-slate-50 rounded-lg p-3 text-center">
                    <p class="text-xs text-slate-500">Rappel</p>
                    <p class="text-lg font-bold text-slate-800">{{ currentModel.recall }}%</p>
                </div>
                <div class="bg-slate-50 rounded-lg p-3 text-center">
                    <p class="text-xs text-slate-500">F1-Score</p>
                    <p class="text-lg font-bold text-slate-800">{{ currentModel.f1 }}%</p>
                </div>
                <div class="bg-slate-50 rounded-lg p-3 text-center">
                    <p class="text-xs text-slate-500">Données entraînement</p>
                    <p class="text-lg font-bold text-slate-800">{{ currentModel.dataSize }}</p>
                </div>
            </div>
        </div>

        <!-- Past Models -->
        <div class="bg-white rounded-xl border border-slate-100 shadow-md overflow-hidden">
            <div class="px-6 py-4 border-b border-slate-200">
                <h3 class="text-sm font-semibold text-slate-700">📋 Versions antérieures</h3>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead class="bg-slate-50">
                        <tr>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Version</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Date</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Précision</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Rappel</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Status</th>
                            <th
                                class="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <tr v-for="model in pastModels" :key="model.version" class="hover:bg-slate-50/50 transition">
                            <td class="px-4 py-3 text-sm font-medium text-slate-700">v{{ model.version }}</td>
                            <td class="px-4 py-3 text-xs text-slate-500">{{ model.date }}</td>
                            <td class="px-4 py-3 text-xs text-slate-600">{{ model.accuracy }}%</td>
                            <td class="px-4 py-3 text-xs text-slate-600">{{ model.recall }}%</td>
                            <td class="px-4 py-3">
                                <span class="text-xs px-2.5 py-1 rounded-full font-medium"
                                    :class="model.status === 'Actif' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-600'">
                                    {{ model.status }}
                                </span>
                            </td>
                            <td class="px-4 py-3">
                                <div class="flex items-center justify-center gap-1">
                                    <button class="p-1.5 rounded hover:bg-blue-50 text-blue-600 transition"
                                        title="Rollback">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                        </svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Training Status -->
        <div class="bg-white rounded-xl p-6 border border-slate-100 shadow-md">
            <h3 class="text-sm font-semibold text-slate-700 mb-3">⏳ Dernier entraînement</h3>
            <div class="flex items-center gap-4 text-sm">
                <span class="text-slate-500">Statut:</span>
                <span class="text-emerald-600 font-medium"><i class="fas fa-check-circle mr-1"></i> Terminé</span>
                <span class="text-slate-300">|</span>
                <span class="text-slate-500">Durée:</span>
                <span class="text-slate-700">4 min 32s</span>
                <span class="text-slate-300">|</span>
                <span class="text-slate-500">Échantillons:</span>
                <span class="text-slate-700">12,847</span>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface ModelVersion {
    version: string
    accuracy: number
    recall: number
    f1: number
    dataSize: string
    lastTrained: string
}

const currentModel = ref<ModelVersion>({
    version: '2.4.1',
    accuracy: 94.7,
    recall: 92.3,
    f1: 93.5,
    dataSize: '12,847',
    lastTrained: '15 sept. 2026, 08:32'
})

const pastModels = ref([
    { version: '2.4.0', date: '10 sept. 2026', accuracy: 93.2, recall: 91.5, status: 'Archivé' },
    { version: '2.3.2', date: '5 sept. 2026', accuracy: 91.8, recall: 89.7, status: 'Archivé' },
    { version: '2.3.0', date: '28 août 2026', accuracy: 89.5, recall: 88.2, status: 'Archivé' },
])
</script>