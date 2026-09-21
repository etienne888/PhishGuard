    <template>
    <div class="space-y-6">
        <div>
        <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">⚙️ {{ t('admin.settings.title') }}</h1>
        <p class="text-sm text-slate-500">Configuration de la plateforme PhishGuard-AI</p>
        </div>

        <div class="grid gap-6 lg:grid-cols-2">

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
            <div><label class="text-xs font-medium text-slate-600 block mb-1">Tentatives de connexion</label><input type="number" value="5" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" /><p class="text-xs text-slate-400 mt-1">avant verrouillage</p></div>
            <div><label class="text-xs font-medium text-slate-600 block mb-1">Signalements</label><input type="number" value="20" class="w-full px-4 py-2 border border-slate-200 dark:border-slate-800 dark:bg-slate-800 rounded-lg text-sm outline-none" /><p class="text-xs text-slate-400 mt-1">par utilisateur/jour</p></div>
            </div>
        </div>

        <!-- Threat response policy (Section 35) -->
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

        <!-- Automation engine (Section 59) -->
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

        <div class="flex justify-end">
        <button @click="save" class="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition hover:scale-[1.02] active:scale-[0.98]">
            <i class="fas fa-save mr-2"></i> {{ t('admin.settings.save') }}
        </button>
        </div>
    </div>
    </template>

    <script setup lang="ts">
    import { ref } from 'vue'
    import { useI18n } from '@/i18n'

    const { t } = useI18n()

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

    function save() {
    if (!confirm('Enregistrer la configuration ? Cette action sera journalisée.')) return
    alert('✓ Configuration enregistrée.')
    }
    </script>