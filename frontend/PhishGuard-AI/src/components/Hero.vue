    <script setup lang="ts">
    const stats = [
    { value: '1.02 Md', label: 'FCFA perdus en 2025' },
    { value: '471', label: 'cas de phishing signalés' },
    { value: '99%', label: "précision de détection" }
    ]
    </script>

    <template>
    <section class="hero-gradient pt-28 pb-20 px-4 relative overflow-hidden">
        <div class="absolute inset-0 scan-line animate-scan pointer-events-none"></div>
        <div class="max-w-6xl mx-auto relative z-10">
        <div class="grid md:grid-cols-2 gap-12 items-center">
            <div>
            <div class="inline-flex items-center gap-2 bg-emerald-50/80 border border-emerald-200/50 rounded-full px-4 py-1.5 text-sm font-medium text-emerald-700 mb-4">
                <span class="h-1.5 w-1.5 rounded-full bg-emerald-500"></span>
                Adopté par des citoyens partout au Cameroun
            </div>
            <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.08] tracking-tight text-slate-800 font-display">
                Détectez le phishing<br />
                <span class="gradient-text">avant qu'il ne soit trop tard</span>
            </h1>
            <p class="mt-4 text-lg text-slate-600 max-w-lg leading-relaxed">
                Collez un SMS, un email ou un message suspect pour savoir instantanément s'il s'agit d'une arnaque.
                <span class="font-medium text-slate-700">Propulsé par l'IA</span> — pensé pour le Cameroun.
            </p>

            <div class="mt-6 flex flex-wrap gap-6">
                <div v-for="stat in stats" :key="stat.label">
                <span class="text-2xl font-bold text-slate-800 font-display">{{ stat.value }}</span>
                <span class="text-sm text-slate-500 block">{{ stat.label }}</span>
                </div>
            </div>

            <div class="mt-8 flex flex-wrap gap-3">
                <a
                href="#analyze"
                class="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 transition hover:scale-[1.02] active:scale-[0.98]"
                >
                Lancer une analyse
                </a>
                <a
                href="#education"
                class="px-8 py-3.5 bg-white/80 backdrop-blur-sm border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-white hover:shadow-md transition"
                >
                Voir les menaces
                </a>
            </div>
            </div>

            <div class="relative hidden md:block">
            <div class="relative mx-auto max-w-md">
                <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 p-5 rotate-1 hover:rotate-0 transition">
                <div class="flex items-center gap-2 text-xs text-slate-400 mb-3">
                    <span class="h-2 w-2 rounded-full bg-red-400"></span>
                    <span class="h-2 w-2 rounded-full bg-yellow-400"></span>
                    <span class="h-2 w-2 rounded-full bg-green-400"></span>
                    <span class="ml-2">PhishGuard-AI · Analyse en direct</span>
                </div>

                <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
                    <p class="text-sm text-slate-700 leading-relaxed">
                    « Cher client MTN, votre compte Mobile Money a été
                    <span class="text-red-500 font-medium">bloqué</span>. Cliquez ici pour le réactiver :
                    <span class="text-red-500 underline">http://mtn-secure-cm.tk</span> »
                    </p>
                </div>

                <div class="mt-3 space-y-2">
                    <span class="inline-flex items-center gap-1.5 text-sm font-bold text-red-600">
                    92% de risque détecté
                    </span>

                    <div class="flex flex-wrap gap-2">
                    <span class="text-xs bg-red-100 text-red-700 px-2.5 py-1 rounded-full border border-red-200">
                        Domaine suspect (.tk)
                    </span>
                    <span class="text-xs bg-orange-100 text-orange-700 px-2.5 py-1 rounded-full border border-orange-200">
                        Urgence détectée
                    </span>
                    <span class="text-xs bg-purple-100 text-purple-700 px-2.5 py-1 rounded-full border border-purple-200">
                        Fraude Mobile Money
                    </span>
                    </div>
                </div>
                </div>

                <div class="absolute -bottom-4 -right-6 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-2 shadow-lg rotate-3">
                <span class="text-sm font-semibold text-emerald-700">Vérifié par l'IA</span>
                </div>
                <div class="absolute -top-4 -left-6 bg-blue-50 border border-blue-200 rounded-xl px-4 py-2 shadow-lg -rotate-3">
                <span class="text-sm font-semibold text-blue-700">Moteur à règles</span>
                </div>
            </div>
            </div>
        </div>
        </div>
    </section>
    </template>
