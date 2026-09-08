<template>
    <div class="space-y-6">
        <!-- Page Header -->
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-2xl font-bold text-slate-800 font-display">🧠 Menaces & Catégories</h1>
                <p class="text-sm text-slate-500">Gestion des catégories de menaces et campagnes de phishing</p>
            </div>
            <button @click="showForm = true"
                class="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition">
                <i class="fas fa-plus mr-1.5"></i> Nouvelle catégorie
            </button>
        </div>

        <!-- Table -->
        <div class="bg-white rounded-xl border border-slate-100 shadow-md overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead class="bg-slate-50 border-b border-slate-200">
                        <tr>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Nom</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Description</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Sévérité</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Région</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Actif</th>
                            <th
                                class="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <tr v-for="category in categories" :key="category.id" class="hover:bg-slate-50/50 transition">
                            <td class="px-4 py-3 text-sm font-medium text-slate-800">{{ category.name }}</td>
                            <td class="px-4 py-3 text-xs text-slate-500 max-w-xs truncate">{{ category.description }}
                            </td>
                            <td class="px-4 py-3">
                                <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="category.severity === 'Critique' ? 'bg-red-100 text-red-700' :
                                        category.severity === 'Élevée' ? 'bg-orange-100 text-orange-700' :
                                            category.severity === 'Moyenne' ? 'bg-yellow-100 text-yellow-700' :
                                                'bg-blue-100 text-blue-700'
                                    ">
                                    {{ category.severity }}
                                </span>
                            </td>
                            <td class="px-4 py-3 text-xs text-slate-500">{{ category.region }}</td>
                            <td class="px-4 py-3">
                                <span class="text-xs" :class="category.active ? 'text-emerald-600' : 'text-slate-400'">
                                    {{ category.active ? '✅ Actif' : '❌ Inactif' }}
                                </span>
                            </td>
                            <td class="px-4 py-3">
                                <div class="flex items-center justify-center gap-1">
                                    <button @click="editCategory(category)"
                                        class="p-1.5 rounded hover:bg-blue-50 text-blue-600 transition"
                                        title="Modifier">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                        </svg>
                                    </button>
                                    <button class="p-1.5 rounded hover:bg-red-50 text-red-600 transition"
                                        title="Supprimer">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Create/Edit Modal -->
        <div v-if="showForm"
            class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
            <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold text-slate-800 font-display">{{ editingId ? 'Modifier' : 'Nouvelle' }}
                        catégorie</h3>
                    <button @click="showForm = false" class="text-slate-400 hover:text-slate-600 transition">✕</button>
                </div>
                <form class="space-y-4" @submit.prevent="saveCategory">
                    <div>
                        <label class="text-xs font-medium text-slate-600 block mb-1">Nom *</label>
                        <input v-model="formData.name" type="text"
                            class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition"
                            required />
                    </div>
                    <div>
                        <label class="text-xs font-medium text-slate-600 block mb-1">Description</label>
                        <textarea v-model="formData.description" rows="2"
                            class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition resize-none"></textarea>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="text-xs font-medium text-slate-600 block mb-1">Sévérité *</label>
                            <select v-model="formData.severity"
                                class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white">
                                <option>Critique</option>
                                <option>Élevée</option>
                                <option>Moyenne</option>
                                <option>Faible</option>
                            </select>
                        </div>
                        <div>
                            <label class="text-xs font-medium text-slate-600 block mb-1">Région</label>
                            <select v-model="formData.region"
                                class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white">
                                <option>Cameroun</option>
                                <option>Afrique de l'Ouest</option>
                                <option>Afrique Centrale</option>
                                <option>International</option>
                            </select>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <input type="checkbox" v-model="formData.active"
                            class="rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                        <label class="text-sm text-slate-600">Actif</label>
                    </div>
                    <div class="flex gap-2 pt-2">
                        <button type="submit"
                            class="flex-1 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition">
                            {{ editingId ? 'Mettre à jour' : 'Créer' }}
                        </button>
                        <button type="button" @click="showForm = false"
                            class="flex-1 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-sm font-medium rounded-lg transition">Annuler</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface ThreatCategory {
    id: number
    name: string
    description: string
    severity: string
    region: string
    active: boolean
}

const categories = ref<ThreatCategory[]>([
    { id: 1, name: 'Phishing Mobile Money', description: 'Tentatives de phishing ciblant les utilisateurs de MTN/Orange Money', severity: 'Critique', region: 'Cameroun', active: true },
    { id: 2, name: 'Ingénierie sociale', description: 'Manipulation psychologique pour obtenir des informations sensibles', severity: 'Élevée', region: 'Cameroun', active: true },
    { id: 3, name: 'SIM swapping', description: 'Transfert frauduleux de numéro de téléphone', severity: 'Élevée', region: 'Afrique de l\'Ouest', active: true },
    { id: 4, name: 'Deepfake / IA', description: 'Utilisation de l\'IA pour créer des contenus frauduleux', severity: 'Moyenne', region: 'International', active: false },
])

const showForm = ref(false)
const editingId = ref<number | null>(null)

const formData = ref({
    name: '',
    description: '',
    severity: 'Moyenne',
    region: 'Cameroun',
    active: true
})

const editCategory = (category: ThreatCategory) => {
    editingId.value = category.id
    formData.value = { ...category }
    showForm.value = true
}

const saveCategory = () => {
    if (editingId.value) {
        const index = categories.value.findIndex(c => c.id === editingId.value)
        if (index !== -1) {
            categories.value[index] = { ...formData.value, id: editingId.value }
        }
    } else {
        categories.value.push({
            ...formData.value,
            id: Math.max(...categories.value.map(c => c.id)) + 1
        })
    }
    showForm.value = false
    editingId.value = null
    formData.value = { name: '', description: '', severity: 'Moyenne', region: 'Cameroun', active: true }
}
</script>