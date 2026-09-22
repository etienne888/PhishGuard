    <template>
    <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-start justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">👥 {{ t('admin.users.title') }}</h1>
            <p class="text-sm text-slate-500">Gestion RBAC · {{ users.length }} comptes</p>
        </div>
        <button @click="refresh" :disabled="loading" class="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-medium rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50">
            <i class="fas fa-rotate mr-1.5" :class="{ 'fa-spin': loading }"></i> Actualiser
        </button>
        </div>

        <p v-if="loadError" class="text-sm text-red-600 bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 rounded-lg px-4 py-2">{{ loadError }}</p>

        <!-- Role summary -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div v-for="role in roles" :key="role.name" class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 p-4">
            <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: role.color }" />
            <span class="text-xs font-semibold text-slate-600 dark:text-slate-300 uppercase tracking-wider">{{ role.name }}</span>
            </div>
            <div class="mt-1 text-xl font-bold text-slate-800 dark:text-slate-100 tabular-nums">{{ role.count }}</div>
        </div>
        </div>

        <!-- Filters -->
        <div class="flex flex-wrap gap-3">
        <div class="relative flex-1 min-w-[200px]">
            <svg class="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4.35-4.35" /></svg>
            <input v-model="searchQuery" type="text" :placeholder="t('admin.users.search')"
            class="w-full pl-9 pr-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500" />
        </div>
        <select v-model="roleFilter" class="px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg text-sm outline-none">
            <option value="">Tous les rôles</option>
            <option value="admin">Administrateur</option>
            <option value="user">Utilisateur</option>
        </select>
        <select v-model="statusFilter" class="px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-900 rounded-lg text-sm outline-none">
            <option value="">Tous les statuts</option>
            <option value="active">Actif</option>
            <option value="suspended">Suspendu</option>
        </select>
        </div>

        <!-- Table -->
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden">
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800">
                <tr>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Utilisateur</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Rôle</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Protection</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Menaces</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">MFA</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Dernière activité</th>
                <th class="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Actions</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                <tr v-if="loading">
                <td colspan="7" class="px-4 py-8 text-center text-sm text-slate-400">Chargement des utilisateurs…</td>
                </tr>
                <tr v-else-if="filteredUsers.length === 0">
                <td colspan="7" class="px-4 py-8 text-center text-sm text-slate-400">Aucun utilisateur ne correspond à vos filtres</td>
                </tr>
                <tr v-for="user in filteredUsers" :key="user.id" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                <td class="px-4 py-3">
                    <div class="flex items-center gap-3">
                    <div class="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                        {{ initials(user.name) }}
                    </div>
                    <div class="min-w-0">
                        <p class="font-medium text-slate-800 dark:text-slate-200 truncate">{{ user.name }}</p>
                        <p class="text-xs text-slate-400 truncate">{{ user.email }}</p>
                    </div>
                    </div>
                </td>
                <td class="px-4 py-3">
                    <span class="text-xs px-2.5 py-1 rounded-full font-medium" :class="roleBadge(user.role)">{{ roleLabel(user.role) }}</span>
                </td>
                <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                    <span class="relative flex h-1.5 w-1.5">
                        <span v-if="user.status === 'active'" class="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
                        <span class="relative inline-flex h-1.5 w-1.5 rounded-full" :class="user.status === 'active' ? 'bg-emerald-500' : 'bg-slate-400'" />
                    </span>
                    <span class="text-xs" :class="user.status === 'active' ? 'text-emerald-600 font-medium' : 'text-slate-400'">
                        {{ user.status === 'active' ? '● Actif' : 'Suspendu' }}
                    </span>
                    </div>
                </td>
                <td class="px-4 py-3">
                    <div class="flex items-center gap-2">
                    <span class="text-xs font-semibold tabular-nums" :class="user.threat_count > 5 ? 'text-red-600' : user.threat_count > 0 ? 'text-amber-600' : 'text-slate-400'">
                        {{ user.threat_count }}
                    </span>
                    <span v-if="user.threat_count > 5" class="text-[10px] uppercase tracking-wide px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-semibold">attention</span>
                    </div>
                </td>
                <td class="px-4 py-3">
                    <span class="text-xs" :class="user.mfa_enabled ? 'text-emerald-600' : 'text-amber-600'">
                    {{ user.mfa_enabled ? '✓ Activé' : '⚠ Désactivé' }}
                    </span>
                </td>
                <td class="px-4 py-3 text-xs text-slate-500">{{ formatDate(user.last_login) }}</td>
                <td class="px-4 py-3">
                    <div class="flex items-center justify-center gap-1">
                    <button @click="viewUser(user)" class="p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-500/10 text-blue-600 transition" title="Profil sécurité">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0z" /><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                    </button>
                    <button @click="toggleSuspend(user)" :disabled="actioningId === user.id" :class="user.status === 'active' ? 'hover:bg-orange-50 text-orange-600' : 'hover:bg-emerald-50 text-emerald-600'" class="p-1.5 rounded transition disabled:opacity-40" :title="user.status === 'active' ? 'Suspendre' : 'Réactiver'">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.364 18.364A9 9 0 0 0 5.636 5.636m12.728 12.728A9 9 0 0 1 5.636 5.636m12.728 12.728L5.636 5.636" /></svg>
                    </button>
                    <button @click="removeUser(user)" :disabled="actioningId === user.id" class="p-1.5 rounded hover:bg-red-50 text-red-600 transition disabled:opacity-40" title="Supprimer">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 7l-.867 12.142A2 2 0 0 1 16.138 21H7.862a2 2 0 0 1-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v3M4 7h16" /></svg>
                    </button>
                    </div>
                </td>
                </tr>
            </tbody>
            </table>
        </div>
        </div>

        <!-- Security profile modal -->
        <div v-if="selectedUser" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm" @click.self="selectedUser = null">
        <div class="bg-white dark:bg-slate-900 rounded-2xl max-w-2xl w-full shadow-2xl max-h-[90vh] overflow-y-auto">
            <div class="sticky top-0 bg-white/90 dark:bg-slate-900/90 backdrop-blur px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between z-10">
            <div>
                <h3 class="text-lg font-bold text-slate-800 dark:text-slate-100">Profil sécurité utilisateur</h3>
                <p class="text-xs text-slate-500">{{ selectedUser.email }}</p>
            </div>
            <button @click="selectedUser = null" class="text-slate-400 hover:text-slate-600 transition">✕</button>
            </div>

            <div class="p-6 space-y-6">
            <!-- Headline -->
            <div class="flex items-center gap-4">
                <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white text-lg font-bold">
                {{ initials(selectedUser.name) }}
                </div>
                <div>
                <p class="text-lg font-bold text-slate-800 dark:text-slate-100">{{ selectedUser.name }}</p>
                <p class="text-xs text-slate-500">{{ roleLabel(selectedUser.role) }} · inscrit {{ formatDate(selectedUser.created_at) }}</p>
                </div>
            </div>

            <!-- KPI grid -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div class="text-[11px] text-slate-500">Protection</div>
                <div class="text-sm font-bold" :class="selectedUser.status === 'active' ? 'text-emerald-600' : 'text-slate-400'">● {{ selectedUser.status === 'active' ? 'Actif' : 'Suspendu' }}</div>
                </div>
                <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div class="text-[11px] text-slate-500">Vérification email</div>
                <div class="text-sm font-bold text-slate-800 dark:text-slate-100">{{ selectedUser.email_verified ? 'Vérifié' : 'Non vérifié' }}</div>
                </div>
                <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div class="text-[11px] text-slate-500">Analyses effectuées</div>
                <div class="text-sm font-bold text-slate-800 dark:text-slate-100 tabular-nums">{{ selectedUser.analyses_count }}</div>
                </div>
                <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div class="text-[11px] text-slate-500">Menaces détectées</div>
                <div class="text-sm font-bold text-red-600 tabular-nums">{{ selectedUser.threat_count }}</div>
                </div>
            </div>
            </div>

            <div class="sticky bottom-0 bg-white/90 dark:bg-slate-900/90 backdrop-blur px-6 py-3 border-t border-slate-200 dark:border-slate-800 flex justify-end gap-2">
            <button @click="selectedUser = null" class="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-sm font-medium rounded-lg transition">{{ t('admin.users.close') }}</button>
            <button @click="forceLogout(selectedUser)" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition">Forcer la déconnexion</button>
            </div>
        </div>
        </div>
    </div>
    </template>

    <script setup lang="ts">
    import { ref, computed, onMounted } from 'vue'
    import { useI18n } from '@/i18n'
    import { adminService, type AdminUser } from '@/services'
    import { useNotificationsStore } from '@/stores/notifications'

    const { t } = useI18n()
    const notifications = useNotificationsStore()

    const users = ref<AdminUser[]>([])
    const loading = ref(false)
    const loadError = ref<string | null>(null)
    const actioningId = ref<number | null>(null)

    const selectedUser = ref<AdminUser | null>(null)
    const searchQuery = ref('')
    const roleFilter = ref('')
    const statusFilter = ref('')

    const roles = computed(() => [
    { name: 'Administrateur', color: '#8b5cf6', count: users.value.filter(u => u.role === 'admin').length },
    { name: 'Utilisateur', color: '#64748b', count: users.value.filter(u => u.role === 'user').length },
    { name: 'Actifs', color: '#10b981', count: users.value.filter(u => u.status === 'active').length },
    { name: 'Suspendus', color: '#f59e0b', count: users.value.filter(u => u.status === 'suspended').length },
    ])

    const filteredUsers = computed(() => {
    const q = searchQuery.value.toLowerCase()
    return users.value.filter(u => {
        const matchQ = !q || u.name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
        const matchRole = !roleFilter.value || u.role === roleFilter.value
        const matchStatus = !statusFilter.value || u.status === statusFilter.value
        return matchQ && matchRole && matchStatus
    })
    })

    async function refresh() {
    loading.value = true
    loadError.value = null
    try {
        const res = await adminService.listUsers()
        users.value = res.items
    } catch {
        loadError.value = "Impossible de charger les utilisateurs. Vérifiez votre connexion à l'API."
    } finally {
        loading.value = false
    }
    }

    function viewUser(user: AdminUser) { selectedUser.value = user }

    async function toggleSuspend(user: AdminUser) {
    const next = user.status === 'active' ? 'suspendre' : 'réactiver'
    if (!confirm(`Voulez-vous ${next} ${user.name} ?`)) return
    actioningId.value = user.id
    try {
        const updated = user.status === 'active' ? await adminService.suspendUser(user.id) : await adminService.reactivateUser(user.id)
        const idx = users.value.findIndex(u => u.id === user.id)
        if (idx !== -1) users.value[idx] = updated
        notifications.push(`${user.name} est maintenant ${updated.status === 'active' ? 'actif' : 'suspendu'}.`, 'success')
    } catch {
        notifications.push('Action impossible.', 'error')
    } finally {
        actioningId.value = null
    }
    }

    async function removeUser(user: AdminUser) {
    if (!confirm(`Supprimer définitivement le compte de ${user.name} ? Cette action est irréversible.`)) return
    actioningId.value = user.id
    try {
        await adminService.deleteUser(user.id)
        users.value = users.value.filter(u => u.id !== user.id)
        notifications.push(`Compte de ${user.name} supprimé.`, 'success')
    } catch {
        notifications.push('Suppression impossible.', 'error')
    } finally {
        actioningId.value = null
    }
    }

    async function forceLogout(user: AdminUser) {
    try {
        await adminService.forceLogout(user.id)
        notifications.push(`Sessions de ${user.name} révoquées.`, 'success')
    } catch {
        notifications.push('Action impossible.', 'error')
    }
    }

    function initials(name: string) {
    const parts = name.split(' ')
    return `${parts[0]?.charAt(0) ?? ''}${parts[1]?.charAt(0) ?? ''}`.toUpperCase()
    }
    function roleLabel(role: string) { return role === 'admin' ? 'Administrateur' : 'Utilisateur' }
    function roleBadge(role: string) { return role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600' }
    function formatDate(value: string | null) {
    if (!value) return 'Jamais'
    return new Date(value).toLocaleString('fr-FR', { dateStyle: 'medium', timeStyle: 'short' })
    }

    onMounted(refresh)
    </script>