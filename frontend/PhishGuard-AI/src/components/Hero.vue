    <script setup lang="ts">
    import { useI18n } from '@/i18n'
    const { t } = useI18n()
    const stats = [
    { value: 'landing.hero.statLossesValue', label: 'landing.hero.statLosses' },
    { value: '471', label: 'landing.hero.statReports' },
    { value: '99%', label: 'landing.hero.statAccuracy' }
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
                {{ t('landing.hero.adopted') }}
            </div>
            <h1 class="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.08] tracking-tight text-slate-800 font-display">
                {{ t('landing.hero.title') }}<br />
                <span class="gradient-text">{{ t('landing.hero.subtitle') }}</span>
            </h1>
            <p class="mt-4 text-lg text-slate-600 max-w-lg leading-relaxed">
                {{ t('landing.hero.description') }}
                <span class="font-medium text-slate-700">{{ t('landing.hero.poweredBy') }}</span>
            </p>

            <div class="mt-6 flex flex-wrap gap-6">
                <div v-for="stat in stats" :key="stat.label">
                <span class="text-2xl font-bold text-slate-800 font-display">{{ stat.value.startsWith('landing.') ? t(stat.value) : stat.value }}</span>
                <span class="text-sm text-slate-500 block">{{ t(stat.label) }}</span>
                </div>
            </div>

            <div class="mt-8 flex flex-wrap gap-3">
                <a
                href="#analyze"
                class="px-8 py-3.5 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50 transition hover:scale-[1.02] active:scale-[0.98]"
                >
                {{ t('landing.hero.ctaAnalyze') }}
                </a>
                <a
                href="#education"
                class="px-8 py-3.5 bg-white/80 backdrop-blur-sm border border-slate-200 text-slate-700 font-semibold rounded-xl hover:bg-white hover:shadow-md transition"
                >
                {{ t('landing.hero.ctaThreats') }}
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
                    <span class="ml-2">PhishGuard-AI · {{ t('landing.hero.liveAnalysis') }}</span>
                </div>

                <div class="bg-slate-50 rounded-xl p-4 border border-slate-100">
                    <p class="text-sm text-slate-700 leading-relaxed">
                    « {{ t('landing.hero.sampleStart') }}
                    <span class="text-red-500 font-medium">{{ t('landing.hero.sampleBlocked') }}</span>. {{ t('landing.hero.sampleClick') }}
                    <span class="text-red-500 underline">http://mtn-secure-cm.tk</span> »
                    </p>
                </div>

                <div class="mt-3 space-y-2">
                    <span class="inline-flex items-center gap-1.5 text-sm font-bold text-red-600">
                    92% {{ t('landing.hero.riskDetected') }}
                    </span>

                    <div class="flex flex-wrap gap-2">
                    <span class="text-xs bg-red-100 text-red-700 px-2.5 py-1 rounded-full border border-red-200">
                        {{ t('landing.hero.suspiciousDomain') }}
                    </span>
                    <span class="text-xs bg-orange-100 text-orange-700 px-2.5 py-1 rounded-full border border-orange-200">
                        {{ t('landing.hero.urgency') }}
                    </span>
                    <span class="text-xs bg-purple-100 text-purple-700 px-2.5 py-1 rounded-full border border-purple-200">
                        {{ t('landing.hero.mobileMoneyFraud') }}
                    </span>
                    </div>
                </div>
                </div>

                <div class="absolute -bottom-4 -right-6 bg-emerald-50 border border-emerald-200 rounded-xl px-4 py-2 shadow-lg rotate-3">
                <span class="text-sm font-semibold text-emerald-700">{{ t('landing.hero.verifiedByAi') }}</span>
                </div>
                <div class="absolute -top-4 -left-6 bg-blue-50 border border-blue-200 rounded-xl px-4 py-2 shadow-lg -rotate-3">
                <span class="text-sm font-semibold text-blue-700">{{ t('landing.hero.ruleEngine') }}</span>
                </div>
            </div>
            </div>
        </div>
        </div>
    </section>
    </template>
