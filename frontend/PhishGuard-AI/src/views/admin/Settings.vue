    <template>
    <div class="space-y-6">
        <div>
        <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">⚙️ {{ t('admin.settings.title') }}</h1>
        <p class="text-sm text-slate-500">Configuration de la plateforme PhishGuard-AI</p>
        </div>

        <!-- Tabs -->
        <div class="flex gap-1 border-b border-slate-200 dark:border-slate-800">
        <button v-for="tab in tabs" :key="tab.key" @click="activeTab = tab.key"
            class="px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition"
            :class="activeTab === tab.key ? 'border-blue-600 text-blue-600' : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'">
            {{ tab.label }}
        </button>
        </div>

        <!-- ============ PROFILE TAB ============ -->
        <div v-if="activeTab === 'profile'" class="grid gap-6 lg:grid-cols-3">
        <div class="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-100 dark:border-slate-800 shadow-sm space-y-4">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200">👤 Profil administrateur</h3>
            <div class="grid sm:grid-cols-2 gap-4">
            <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Nom complet</label>
                <input v-model="fullNameInput" type="text" placeholder="Votre nom"
                class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500/30" />
            </div>
            <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Email</label>
                <input :value="profile.email" type="email" disabled
                class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800/50 rounded-lg text-sm outline-none text-slate-400" />
            </div>
            <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Téléphone</label>
                <input v-model="profile.phone" type="text" placeholder="+237 6 00 00 00 00"
                class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500/30" />
            </div>
            <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Rôle</label>
                <input :value="profile.role === 'admin' ? 'Administrateur' : 'Utilisateur'" disabled
                class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800/50 rounded-lg text-sm outline-none text-slate-400" />
            </div>
            </div>
            <div class="flex justify-end">
            <button @click="saveProfile" :disabled="savingProfile" class="px-5 py-2 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-semibold rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition disabled:opacity-50">
                <i class="fas fa-save mr-2"></i> {{ savingProfile ? 'Enregistrement…' : 'Enregistrer le profil' }}
            </button>
            </div>
        </div>

        <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-100 dark:border-slate-800 shadow-sm">
            <div class="flex flex-col items-center text-center gap-3">
            <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white text-2xl font-bold">
                {{ profileInitials }}
            </div>
            <div>
                <p class="font-bold text-slate-800 dark:text-slate-100">{{ fullNameInput || profile.email }}</p>
                <p class="text-xs text-slate-500">{{ profile.email }}</p>
            </div>
            <span class="text-xs font-semibold px-2.5 py-1 rounded-full" :class="profile.mfa_enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'">
                {{ profile.mfa_enabled ? '✓ MFA activé' : '⚠ MFA désactivé' }}
            </span>
            </div>
        </div>
        </div>

        <!-- ============ SECURITY TAB ============ -->
        <div v-if="activeTab === 'security'" class="grid gap-6 lg:grid-cols-2">
        <p v-if="settingsError" class="lg:col-span-2 text-sm text-red-600 bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 rounded-lg px-4 py-2">{{ settingsError }}</p>

        <!-- Access control -->
        <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-100 dark:border-slate-800 shadow-sm">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">🔐 Contrôle des accès</h3>
            <div class="space-y-4">
            <label class="flex items-center justify-between cursor-pointer">
                <div>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">Autoriser les nouvelles inscriptions</p>
                <p class="text-xs text-slate-400">Désactiver pour bloquer tout nouveau signup</p>
                </div>
                <input type="checkbox" v-model="settings.allow_signup" class="sr-only peer" />
                <div class="relative w-11 h-6 bg-slate-200 dark:bg-slate-700 rounded-full peer-checked:bg-blue-600 transition-colors after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full" />
            </label>
            <label class="flex items-center justify-between cursor-pointer">
                <div>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">Vérification email obligatoire</p>
                <p class="text-xs text-slate-400">Bloquer la connexion tant que l'email n'est pas vérifié</p>
                </div>
                <input type="checkbox" v-model="settings.require_email_verification" class="sr-only peer" />
                <div class="relative w-11 h-6 bg-slate-200 dark:bg-slate-700 rounded-full peer-checked:bg-blue-600 transition-colors after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full" />
            </label>
            <label class="flex items-center justify-between cursor-pointer">
                <div>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">MFA obligatoire pour tous</p>
                <p class="text-xs text-slate-400">Forcer la double authentification à la connexion</p>
                </div>
                <input type="checkbox" v-model="settings.mfa_required" class="sr-only peer" />
                <div class="relative w-11 h-6 bg-slate-200 dark:bg-slate-700 rounded-full peer-checked:bg-blue-600 transition-colors after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full" />
            </label>
            </div>
        </div>

        <!-- Login policy -->
        <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-100 dark:border-slate-800 shadow-sm">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">🛡️ Politique de connexion</h3>
            <div class="grid grid-cols-1 gap-4">
            <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Tentatives avant verrouillage</label>
                <input v-model.number="settings.max_login_attempts" type="number" min="1" max="20" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" />
            </div>
            <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Durée de verrouillage</label>
                <input v-model.number="settings.lockout_duration_min" type="number" min="1" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" /><p class="text-xs text-slate-400 mt-1">minutes</p>
            </div>
            <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Expiration de session</label>
                <input v-model.number="settings.session_timeout_min" type="number" min="5" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" /><p class="text-xs text-slate-400 mt-1">minutes d'inactivité</p>
            </div>
            </div>
        </div>

        <!-- Password policy -->
        <div class="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-100 dark:border-slate-800 shadow-sm">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">🔑 Politique de mot de passe</h3>
            <div class="grid sm:grid-cols-2 gap-4">
            <div>
                <label class="text-xs font-medium text-slate-600 block mb-1">Longueur minimale</label>
                <input v-model.number="settings.password_min_length" type="number" min="6" max="64" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" />
            </div>
            <div class="space-y-2 flex flex-col justify-center">
                <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300"><input type="checkbox" v-model="settings.password_require_upper" class="rounded border-slate-300 text-blue-600" /> Majuscule requise</label>
                <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300"><input type="checkbox" v-model="settings.password_require_number" class="rounded border-slate-300 text-blue-600" /> Chiffre requis</label>
                <label class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300"><input type="checkbox" v-model="settings.password_require_symbol" class="rounded border-slate-300 text-blue-600" /> Symbole requis</label>
            </div>
            </div>
        </div>

        <div class="lg:col-span-2 flex justify-end">
            <button @click="saveSettings" :disabled="savingSettings" class="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50">
            <i class="fas fa-save mr-2"></i> {{ savingSettings ? 'Enregistrement…' : t('admin.settings.save') }}
            </button>
        </div>
        </div>

        <!-- ============ PLATFORM TAB (SMTP / features / limits — visual reference, static) ============ -->
        <div v-if="activeTab === 'platform'" class="grid gap-6 lg:grid-cols-2">

        <!-- SMTP -->
        <div class="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-100 dark:border-slate-800 shadow-sm">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">📧 Configuration SMTP</h3>
            <div class="grid sm:grid-cols-2 gap-4">
            <div><label class="text-xs font-medium text-slate-600 block mb-1">Serveur</label><input type="text" value="smtp.phishguard.cm" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" /></div>
            <div><label class="text-xs font-medium text-slate-600 block mb-1">Port</label><input type="text" value="587" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" /></div>
            <div><label class="text-xs font-medium text-slate-600 block mb-1">Utilisateur</label><input type="text" value="noreply@phishguard.cm" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" /></div>
            <div><label class="text-xs font-medium text-slate-600 block mb-1">Mot de passe</label><input type="password" value="••••••••" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" /></div>
            </div>
            <div class="flex items-center gap-3 mt-3">
            <span class="text-xs text-emerald-600 inline-flex items-center gap-1"><i class="fas fa-check-circle"></i> Connecté</span>
            <button class="text-xs text-blue-600 hover:underline font-medium">{{ t('admin.settings.testConnection') }}</button>
            </div>
        </div>

        <!-- Feature flags -->
        <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-100 dark:border-slate-800 shadow-sm">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">🚀 Fonctionnalités</h3>
            <div class="space-y-4">
            <label v-for="flag in flags" :key="flag.key" class="flex items-center justify-between cursor-pointer">
                <div>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ flag.label }}</p>
                <p class="text-xs text-slate-400">{{ flag.hint }}</p>
                </div>
                <input type="checkbox" v-model="flag.enabled" @change="onFlagChange(flag)" class="sr-only peer" />
                <div class="relative w-11 h-6 bg-slate-200 dark:bg-slate-700 rounded-full peer-checked:bg-blue-600 transition-colors after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full" />
            </label>
            </div>
        </div>

        <!-- Rate limits -->
        <div class="bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-100 dark:border-slate-800 shadow-sm">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">⏱️ Limites de taux</h3>
            <div class="grid grid-cols-1 gap-4">
            <div><label class="text-xs font-medium text-slate-600 block mb-1">Analyses par utilisateur</label><input type="number" value="100" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" /><p class="text-xs text-slate-400 mt-1">par jour</p></div>
            <div><label class="text-xs font-medium text-slate-600 block mb-1">Tentatives de connexion</label><input type="number" :value="settings.max_login_attempts" disabled class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800/50 rounded-lg text-sm outline-none text-slate-400" /><p class="text-xs text-slate-400 mt-1">Défini dans l'onglet Sécurité</p></div>
            <div><label class="text-xs font-medium text-slate-600 block mb-1">Signalements</label><input type="number" value="20" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" /><p class="text-xs text-slate-400 mt-1">par utilisateur/jour</p></div>
            </div>
        </div>

        <!-- Threat response policy -->
        <div class="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-100 dark:border-slate-800 shadow-sm">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">🛡️ Politique de réponse aux menaces</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div class="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20 text-center">
                <div class="text-xs text-emerald-700 font-semibold uppercase tracking-wider">Risque 0–49</div>
                <div class="mt-1 text-lg font-bold text-emerald-700">AUTORISER</div>
            </div>
            <div class="p-4 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-100 dark:border-amber-500/20 text-center">
                <div class="text-xs text-amber-700 font-semibold uppercase tracking-wider">Risque 50–69</div>
                <div class="mt-1 text-lg font-bold text-amber-700">AVERTIR</div>
            </div>
            <div class="p-4 rounded-lg bg-orange-50 dark:bg-orange-500/10 border border-orange-100 dark:border-orange-500/20 text-center">
                <div class="text-xs text-orange-700 font-semibold uppercase tracking-wider">Risque 70–89</div>
                <div class="mt-1 text-lg font-bold text-orange-700">QUARANTAINE</div>
            </div>
            <div class="p-4 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 text-center">
                <div class="text-xs text-red-700 font-semibold uppercase tracking-wider">Risque 90–100</div>
                <div class="mt-1 text-lg font-bold text-red-700">BLOQUER</div>
            </div>
            </div>
        </div>

        <!-- Automation engine -->
        <div class="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl p-6 border border-slate-100 dark:border-slate-800 shadow-sm">
            <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200">🤖 Automation des rapports</h3>
            <span class="text-[11px] text-slate-400">Fuseau : Africa/Douala (UTC+1)</span>
            </div>
            <div class="space-y-4">
            <div v-for="task in automations" :key="task.id" class="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
                <div class="flex items-start justify-between gap-3">
                <div>
                    <div class="flex items-center gap-2">
                    <span class="text-sm font-semibold text-slate-700 dark:text-slate-200">{{ task.label }}</span>
                    <span class="text-[10px] font-semibold px-2 py-0.5 rounded-full" :class="task.enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-200 text-slate-500'">{{ task.enabled ? 'ACTIVÉ' : 'DÉSACTIVÉ' }}</span>
                    </div>
                    <div class="mt-2 grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                    <div><div class="text-slate-500">Fréquence</div><div class="font-medium text-slate-700 dark:text-slate-200">{{ task.freq }}</div></div>
                    <div><div class="text-slate-500">Heure</div><div class="font-medium text-slate-700 dark:text-slate-200 font-mono">{{ task.time }}</div></div>
                    <div class="col-span-2"><div class="text-slate-500">Destinataires</div><div class="font-medium text-slate-700 dark:text-slate-200 truncate">{{ task.recipients }}</div></div>
                    </div>
                </div>
                <input type="checkbox" v-model="task.enabled" class="mt-1 rounded border-slate-300 text-blue-600 focus:ring-blue-500" />
                </div>
            </div>
            </div>
        </div>
        </div>
    </div>
    </template>

    <script setup lang="ts">
    import { ref, onMounted, computed } from 'vue'
    import { useRoute } from 'vue-router'
    import { useI18n } from '@/i18n'
    import { adminService, type AdminUser, type PlatformSettings } from '@/services'
    import { useNotificationsStore } from '@/stores/notifications'

    const { t } = useI18n()
    const route = useRoute()
    const notifications = useNotificationsStore()

    const tabs = [
    { key: 'profile', label: '👤 Profil' },
    { key: 'security', label: '🔐 Sécurité' },
    { key: 'platform', label: '⚙️ Plateforme' },
    ] as const
    const activeTab = ref<typeof tabs[number]['key']>(route.query.tab === 'security' ? 'security' : 'profile')

    const profile = ref<AdminUser>({
    id: 0, name: '', email: '', phone: null, role: 'admin', status: 'active',
    mfa_enabled: false, email_verified: false, auth_provider: 'password',
    created_at: null, last_login: null, locked: false, threat_count: 0, analyses_count: 0,
    })
    const fullNameInput = ref('')
    const savingProfile = ref(false)

    const profileInitials = computed(() => {
    const label = fullNameInput.value || profile.value.name || profile.value.email
    const parts = label.split(' ')
    return `${parts[0]?.charAt(0) ?? ''}${parts[1]?.charAt(0) ?? ''}`.toUpperCase() || 'A'
    })

    const settings = ref<PlatformSettings>({
    allow_signup: true,
    require_email_verification: true,
    mfa_required: false,
    session_timeout_min: 30,
    max_login_attempts: 5,
    lockout_duration_min: 15,
    password_min_length: 12,
    password_require_upper: true,
    password_require_number: true,
    password_require_symbol: true,
    })
    const savingSettings = ref(false)
    const settingsError = ref<string | null>(null)

    async function loadProfile() {
    try {
        profile.value = await adminService.getProfile()
        fullNameInput.value = profile.value.name
    } catch {
        notifications.push('Impossible de charger le profil.', 'error')
    }
    }

    async function saveProfile() {
    savingProfile.value = true
    try {
        profile.value = await adminService.updateProfile({
        full_name: fullNameInput.value,
        phone: profile.value.phone ?? undefined,
        })
        fullNameInput.value = profile.value.name
        notifications.push('Profil mis à jour.', 'success')
    } catch {
        notifications.push('Impossible de mettre à jour le profil.', 'error')
    } finally {
        savingProfile.value = false
    }
    }

    async function loadSettings() {
    try {
        settings.value = await adminService.getSettings()
    } catch {
        settingsError.value = "Impossible de charger les paramètres de sécurité."
    }
    }

    async function saveSettings() {
    savingSettings.value = true
    settingsError.value = null
    try {
        settings.value = await adminService.updateSettings(settings.value)
        notifications.push('Paramètres de sécurité enregistrés.', 'success')
    } catch {
        settingsError.value = "Échec de l'enregistrement des paramètres."
    } finally {
        savingSettings.value = false
    }
    }

    const flags = ref([
    { key: 'mfa', label: 'MFA obligatoire', hint: 'Forcer l\'authentification à deux facteurs pour tous les utilisateurs', enabled: true },
    { key: 'report', label: 'Signalement public', hint: 'Permettre aux utilisateurs de signaler des tentatives', enabled: true },
    { key: 'export', label: 'Exportation des données', hint: 'Permettre aux administrateurs d\'exporter les données', enabled: false },
    ])

    const automations = ref([
    { id: 1, label: 'Rapport de sécurité quotidien', enabled: true, freq: 'Quotidien', time: '08:00', recipients: 'security@phishguard.cm' },
    { id: 2, label: 'Rapport exécutif hebdomadaire', enabled: true, freq: 'Lundi', time: '08:30', recipients: 'direction@phishguard.cm' },
    { id: 3, label: 'Rapport mensuel complet', enabled: false, freq: '1er du mois', time: '07:00', recipients: 'board@phishguard.cm' },
    ])

    function onFlagChange(flag: any) {
    if (flag.key === 'export' && flag.enabled) {
        if (!confirm('Activer l\'exportation des données utilisateur ? Cette action a des implications de confidentialité.')) {
        flag.enabled = false
        }
    }
    }

    onMounted(() => {
    loadProfile()
    loadSettings()
    })
    </script>