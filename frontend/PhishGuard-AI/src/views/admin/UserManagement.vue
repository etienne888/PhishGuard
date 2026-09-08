<template>
    <div class="space-y-6">
        <!-- Page Header -->
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-2xl font-bold text-slate-800 font-display">👥 Utilisateurs</h1>
                <p class="text-sm text-slate-500">Gestion des utilisateurs de la plateforme</p>
            </div>
            <button
                class="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition hover:scale-[1.02] active:scale-[0.98]">
                <i class="fas fa-user-plus mr-1.5"></i> Ajouter
            </button>
        </div>

        <!-- Filters -->
        <div class="flex flex-wrap gap-3">
            <input type="text" placeholder="Rechercher un utilisateur..."
                class="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition w-full sm:w-64" />
            <select
                class="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white">
                <option>Tous les rôles</option>
                <option>Admin</option>
                <option>Utilisateur</option>
                <option>Modérateur</option>
            </select>
            <select
                class="px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white">
                <option>Tous les statuts</option>
                <option>Actif</option>
                <option>Suspendu</option>
            </select>
        </div>

        <!-- Table -->
        <div class="bg-white rounded-xl border border-slate-100 shadow-md overflow-hidden">
            <div class="overflow-x-auto">
                <table class="w-full text-sm">
                    <thead class="bg-slate-50 border-b border-slate-200">
                        <tr>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Utilisateur</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Rôle</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Statut</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                MFA</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Inscrit</th>
                            <th
                                class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Dernière connexion</th>
                            <th
                                class="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                                Actions</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-100">
                        <tr v-for="user in users" :key="user.id" class="hover:bg-slate-50/50 transition">
                            <td class="px-4 py-3">
                                <div class="flex items-center gap-3">
                                    <div
                                        class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white text-xs font-bold">
                                        {{ user.name.charAt(0) }}
                                    </div>
                                    <div>
                                        <p class="font-medium text-slate-800">{{ user.name }}</p>
                                        <p class="text-xs text-slate-400">{{ user.email }}</p>
                                    </div>
                                </div>
                            </td>
                            <td class="px-4 py-3">
                                <span class="text-xs px-2.5 py-1 rounded-full font-medium"
                                    :class="user.role === 'Admin' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'">
                                    {{ user.role }}
                                </span>
                            </td>
                            <td class="px-4 py-3">
                                <span class="text-xs px-2.5 py-1 rounded-full font-medium"
                                    :class="user.status === 'Actif' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'">
                                    {{ user.status }}
                                </span>
                            </td>
                            <td class="px-4 py-3">
                                <span class="text-xs" :class="user.mfa ? 'text-emerald-600' : 'text-slate-400'">
                                    {{ user.mfa ? '✅ Activé' : '❌ Désactivé' }}
                                </span>
                            </td>
                            <td class="px-4 py-3 text-xs text-slate-500">{{ user.createdAt }}</td>
                            <td class="px-4 py-3 text-xs text-slate-500">{{ user.lastLogin }}</td>
                            <td class="px-4 py-3">
                                <div class="flex items-center justify-center gap-1">
                                    <button @click="viewUser(user)"
                                        class="p-1.5 rounded hover:bg-blue-50 text-blue-600 transition"
                                        title="Voir détails">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                        </svg>
                                    </button>
                                    <button
                                        :class="user.status === 'Actif' ? 'hover:bg-orange-50 text-orange-600' : 'hover:bg-emerald-50 text-emerald-600'"
                                        class="p-1.5 rounded transition" title="Suspendre/Réactiver">
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                                d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
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
            <!-- Pagination -->
            <div class="flex items-center justify-between px-4 py-3 border-t border-slate-200">
                <p class="text-xs text-slate-500">Affichage 1-10 sur 48 utilisateurs</p>
                <div class="flex gap-1">
                    <button
                        class="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 transition">Précédent</button>
                    <button class="px-3 py-1 text-xs bg-blue-600 text-white rounded">1</button>
                    <button
                        class="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 transition">2</button>
                    <button
                        class="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 transition">3</button>
                    <button
                        class="px-3 py-1 text-xs border border-slate-200 rounded hover:bg-slate-50 transition">Suivant</button>
                </div>
            </div>
        </div>

        <!-- User Detail Modal -->
        <div v-if="selectedUser"
            class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
            <div class="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold text-slate-800 font-display">Détails utilisateur</h3>
                    <button @click="selectedUser = null"
                        class="text-slate-400 hover:text-slate-600 transition">✕</button>
                </div>
                <div class="space-y-3 text-sm">
                    <p><span class="font-medium text-slate-600">Nom:</span> {{ selectedUser.name }}</p>
                    <p><span class="font-medium text-slate-600">Email:</span> {{ selectedUser.email }}</p>
                    <p><span class="font-medium text-slate-600">Rôle:</span> {{ selectedUser.role }}</p>
                    <p><span class="font-medium text-slate-600">Statut:</span> {{ selectedUser.status }}</p>
                    <p><span class="font-medium text-slate-600">MFA:</span> {{ selectedUser.mfa ? 'Activé' : 'Désactivé'
                        }}</p>
                    <p><span class="font-medium text-slate-600">Inscrit:</span> {{ selectedUser.createdAt }}</p>
                    <p><span class="font-medium text-slate-600">Dernière connexion:</span> {{ selectedUser.lastLogin }}
                    </p>
                    <div class="pt-3 border-t border-slate-200">
                        <p class="font-medium text-slate-600 mb-2">Historique des analyses</p>
                        <div class="space-y-1 max-h-32 overflow-y-auto">
                            <div v-for="analysis in userAnalyses" :key="analysis.id"
                                class="flex items-center justify-between text-xs p-2 bg-slate-50 rounded">
                                <span>{{ analysis.date }}</span>
                                <span :class="analysis.verdict === 'Phishing' ? 'text-red-600' : 'text-emerald-600'">{{
                                    analysis.verdict }}</span>
                                <span>{{ analysis.score }}%</span>
                            </div>
                        </div>
                    </div>
                </div>
                <button @click="selectedUser = null"
                    class="mt-4 w-full py-2 bg-slate-100 hover:bg-slate-200 rounded-lg text-sm font-medium transition">Fermer</button>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface User {
    id: number
    name: string
    email: string
    role: string
    status: string
    mfa: boolean
    createdAt: string
    lastLogin: string
}

const users = ref<User[]>([
    { id: 1, name: 'Lareine Tracy', email: 'lareine@phishguard.cm', role: 'Admin', status: 'Actif', mfa: true, createdAt: '15 janv. 2026', lastLogin: 'Aujourd\'hui, 14:32' },
    { id: 2, name: 'Jean Dupont', email: 'jean@example.com', role: 'Utilisateur', status: 'Actif', mfa: false, createdAt: '20 févr. 2026', lastLogin: 'Hier, 09:15' },
    { id: 3, name: 'Marie Kamdem', email: 'marie@example.com', role: 'Modérateur', status: 'Actif', mfa: true, createdAt: '5 mars 2026', lastLogin: 'Aujourd\'hui, 08:45' },
    { id: 4, name: 'Paul Nguea', email: 'paul@example.com', role: 'Utilisateur', status: 'Suspendu', mfa: false, createdAt: '12 avr. 2026', lastLogin: '3 mai 2026, 16:20' },
])

const selectedUser = ref<User | null>(null)

const userAnalyses = ref([
    { id: 1, date: '10 sept. 2026', verdict: 'Phishing', score: 92 },
    { id: 2, date: '8 sept. 2026', verdict: 'Légitime', score: 12 },
    { id: 3, date: '5 sept. 2026', verdict: 'Phishing', score: 85 },
])

const viewUser = (user: User) => {
    selectedUser.value = user
}
</script>