<template>
    <div class="space-y-6">
        <!-- Page Header -->
        <div>
            <h1 class="text-2xl font-bold text-slate-800 font-display">⚙️ Paramètres</h1>
            <p class="text-sm text-slate-500">Configuration de la plateforme PhishGuard-AI</p>
        </div>

        <div class="grid gap-6">

            <!-- SMTP Settings -->
            <div class="bg-white rounded-xl p-6 border border-slate-100 shadow-md">
                <h3 class="text-sm font-semibold text-slate-700 mb-4">📧 Configuration SMTP</h3>
                <div class="grid sm:grid-cols-2 gap-4">
                    <div>
                        <label class="text-xs font-medium text-slate-600 block mb-1">Serveur</label>
                        <input type="text" value="smtp.phishguard.cm"
                            class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
                    </div>
                    <div>
                        <label class="text-xs font-medium text-slate-600 block mb-1">Port</label>
                        <input type="text" value="587"
                            class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
                    </div>
                    <div>
                        <label class="text-xs font-medium text-slate-600 block mb-1">Utilisateur</label>
                        <input type="text" value="noreply@phishguard.cm"
                            class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
                    </div>
                    <div>
                        <label class="text-xs font-medium text-slate-600 block mb-1">Mot de passe</label>
                        <input type="password" value="••••••••"
                            class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
                    </div>
                </div>
                <div class="flex items-center gap-2 mt-3">
                    <span class="text-xs text-emerald-600"><i class="fas fa-check-circle mr-1"></i> Connecté</span>
                    <button class="text-xs text-blue-600 hover:underline font-medium">Tester la connexion</button>
                </div>
            </div>

            <!-- Feature Flags -->
            <div class="bg-white rounded-xl p-6 border border-slate-100 shadow-md">
                <h3 class="text-sm font-semibold text-slate-700 mb-4">🚀 Fonctionnalités</h3>
                <div class="space-y-3">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-700">MFA obligatoire</p>
                            <p class="text-xs text-slate-400">Forcer l'authentification à deux facteurs pour tous les
                                utilisateurs</p>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked class="sr-only peer" />
                            <div
                                class="w-11 h-6 bg-slate-200 peer-focus:ring-2 peer-focus:ring-blue-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600">
                            </div>
                        </label>
                    </div>
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-700">Signalement public</p>
                            <p class="text-xs text-slate-400">Permettre aux utilisateurs de signaler des tentatives de
                                phishing</p>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked class="sr-only peer" />
                            <div
                                class="w-11 h-6 bg-slate-200 peer-focus:ring-2 peer-focus:ring-blue-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600">
                            </div>
                        </label>
                    </div>
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-sm font-medium text-slate-700">Exportation des données</p>
                            <p class="text-xs text-slate-400">Permettre aux administrateurs d'exporter les données
                                utilisateur</p>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" class="sr-only peer" />
                            <div
                                class="w-11 h-6 bg-slate-200 peer-focus:ring-2 peer-focus:ring-blue-500/30 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600">
                            </div>
                        </label>
                    </div>
                </div>
            </div>

            <!-- Rate Limits -->
            <div class="bg-white rounded-xl p-6 border border-slate-100 shadow-md">
                <h3 class="text-sm font-semibold text-slate-700 mb-4">⏱️ Limites de taux</h3>
                <div class="grid sm:grid-cols-3 gap-4">
                    <div>
                        <label class="text-xs font-medium text-slate-600 block mb-1">Analyses par utilisateur</label>
                        <input type="number" value="100"
                            class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
                        <p class="text-xs text-slate-400 mt-1">par jour</p>
                    </div>
                    <div>
                        <label class="text-xs font-medium text-slate-600 block mb-1">Tentatives de connexion</label>
                        <input type="number" value="5"
                            class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
                        <p class="text-xs text-slate-400 mt-1">avant verrouillage</p>
                    </div>
                    <div>
                        <label class="text-xs font-medium text-slate-600 block mb-1">Signalements</label>
                        <input type="number" value="20"
                            class="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white" />
                        <p class="text-xs text-slate-400 mt-1">par utilisateur/jour</p>
                    </div>
                </div>
            </div>

            <!-- Save Button -->
            <div class="flex justify-end">
                <button
                    class="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition hover:scale-[1.02] active:scale-[0.98]">
                    <i class="fas fa-save mr-2"></i> Enregistrer les modifications
                </button>
            </div>

        </div>
    </div>
</template>