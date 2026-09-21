    <template>
    <div class="space-y-6">

        <!-- HERO: SOC STATUS -->
        <div class="relative overflow-hidden rounded-2xl bg-slate-900 text-white p-6 md:p-8">
        <div class="pointer-events-none absolute inset-0 motion-safe:animate-[scan-sweep_5s_linear_infinite] bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent -translate-x-full" />
        <div class="relative flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
            <div class="flex items-center gap-4">
            <div class="relative flex h-16 w-16 flex-shrink-0 items-center justify-center">
                <span class="absolute inline-flex h-full w-full rounded-full bg-cyan-400/20 motion-safe:animate-[radar-pulse_2.4s_ease-out_infinite]" />
                <span class="absolute inline-flex h-full w-full rounded-full bg-cyan-400/10 motion-safe:animate-[radar-pulse_2.4s_ease-out_infinite] [animation-delay:0.6s]" />
                <div class="relative flex h-14 w-14 items-center justify-center rounded-full bg-slate-800 ring-1 ring-cyan-400/40">
                <svg viewBox="0 0 24 24" class="h-7 w-7" fill="none" stroke="#22d3ee" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                    <path d="M9 12l2 2 4-4" />
                </svg>
                </div>
            </div>
            <div>
                <div class="flex items-center gap-2 text-xs font-medium text-emerald-400">
                <span class="relative flex h-2 w-2">
                    <span class="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                    <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
                </span>
                {{ t('admin.overview.status') }}
                </div>
                <h1 class="mt-1 text-2xl md:text-3xl font-bold tracking-tight">{{ t('admin.overview.title') }}</h1>
                <p class="text-slate-400 text-sm mt-0.5">{{ t('admin.overview.lastUpdate') }} {{ lastUpdate }}</p>
            </div>
            </div>

            <div class="grid grid-cols-3 gap-4 text-center">
            <div>
                <div class="text-2xl font-bold tabular-nums text-emerald-400">{{ uptime }}%</div>
                <div class="text-[11px] text-slate-400 uppercase tracking-wider">Uptime 30j</div>
            </div>
            <div>
                <div class="text-2xl font-bold tabular-nums text-cyan-300">{{ aiLatency }}ms</div>
                <div class="text-[11px] text-slate-400 uppercase tracking-wider">Latence IA</div>
            </div>
            <div>
                <div class="text-2xl font-bold tabular-nums text-amber-300">{{ activeIncidents }}</div>
                <div class="text-[11px] text-slate-400 uppercase tracking-wider">Incidents actifs</div>
            </div>
            </div>
        </div>
        </div>

        <!-- KPI ROW -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div v-for="kpi in kpis" :key="kpi.label" class="relative bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm p-5 overflow-hidden">
            <div class="absolute inset-x-0 top-0 h-0.5" :class="kpi.accent" />
            <div class="flex items-center justify-between">
            <span class="text-2xl">{{ kpi.icon }}</span>
            <span v-if="kpi.trend !== null" class="text-xs font-semibold inline-flex items-center gap-0.5"
                :class="kpi.trend > 0 ? 'text-emerald-600' : 'text-red-600'">
                {{ kpi.trend > 0 ? '▲' : '▼' }} {{ Math.abs(kpi.trend) }}%
            </span>
            </div>
            <div class="text-2xl font-bold text-slate-800 dark:text-slate-100 mt-3 tabular-nums">{{ kpi.value }}</div>
            <div class="text-sm text-slate-500 mt-1">{{ kpi.label }}</div>
            <div v-if="kpi.hint" class="text-[11px] text-slate-400 mt-2">{{ kpi.hint }}</div>
        </div>
        </div>

        <!-- LIVE ACTIVITY + CHART -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

        <!-- Live threat feed -->
        <div class="lg:col-span-2 bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
            <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2">
                <span class="relative flex h-2 w-2">
                <span class="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-75" />
                <span class="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
                </span>
                {{ t('admin.overview.liveActivity') }}
            </h3>
            <span class="text-[11px] text-slate-400 font-mono">LIVE</span>
            </div>
            <div class="space-y-2 max-h-[420px] overflow-y-auto">
            <div v-for="event in liveThreats" :key="event.id"
                class="flex items-center gap-3 p-3 rounded-lg border transition hover:border-slate-300 dark:hover:border-slate-700"
                :class="event.severity === 'critical' ? 'bg-red-50/60 border-red-100 dark:bg-red-500/5 dark:border-red-500/20' : event.severity === 'high' ? 'bg-amber-50/60 border-amber-100 dark:bg-amber-500/5 dark:border-amber-500/20' : 'bg-slate-50 border-slate-100 dark:bg-slate-800/40 dark:border-slate-800'">
                <span class="text-[11px] font-mono text-slate-400 tabular-nums w-16 flex-shrink-0">{{ event.time }}</span>
                <span class="w-1.5 h-1.5 rounded-full flex-shrink-0"
                :class="event.severity === 'critical' ? 'bg-red-500' : event.severity === 'high' ? 'bg-amber-500' : 'bg-slate-400'" />
                <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200 truncate">{{ event.type }}</p>
                <p class="text-xs text-slate-500 truncate">{{ event.source }}</p>
                </div>
                <span class="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full flex-shrink-0"
                :class="event.severity === 'critical' ? 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-300' : event.severity === 'high' ? 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'">
                {{ event.severity }}
                </span>
            </div>
            </div>
        </div>

        <!-- Right column: chart + activity -->
        <div class="space-y-6">
            <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">📈 {{ t('admin.overview.analytics') }}</h3>
            <div class="h-40 flex items-end gap-2">
                <div v-for="(bar, i) in chartBars" :key="i" class="flex-1 flex flex-col items-center gap-1">
                <div class="w-full rounded-t-md bg-gradient-to-t from-blue-600 to-cyan-500 transition-all duration-500"
                    :style="{ height: bar.value + '%' }" :title="`${bar.label}: ${bar.value}`" />
                <span class="text-[10px] text-slate-400">{{ bar.label }}</span>
                </div>
            </div>
            </div>

            <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-4">🕒 {{ t('admin.overview.recentActivity') }}</h3>
            <div class="relative space-y-4 pl-4 before:absolute before:left-[3px] before:top-1 before:bottom-1 before:w-px before:bg-slate-200 dark:before:bg-slate-800">
                <div v-for="activity in activities" :key="activity.id" class="relative flex gap-3">
                <span class="absolute -left-4 top-1.5 h-2 w-2 rounded-full ring-4 ring-white dark:ring-slate-900"
                    :style="{ backgroundColor: activity.dot }" />
                <span class="text-base">{{ activity.icon }}</span>
                <div class="min-w-0">
                    <p class="text-sm text-slate-700 dark:text-slate-200">{{ activity.action }}</p>
                    <p class="text-xs text-slate-400">{{ activity.time }}</p>
                </div>
                </div>
            </div>
            </div>
        </div>
        </div>

        <!-- EXECUTIVE SUMMARY -->
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200">🧭 {{ t('admin.overview.summary') }}</h3>
            <span class="text-[11px] text-slate-400">Mis à jour {{ lastUpdate }}</span>
        </div>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
            <p class="text-xs text-slate-500">Posture globale</p>
            <p class="text-lg font-bold text-emerald-600">BONNE</p>
            </div>
            <div>
            <p class="text-xs text-slate-500">Niveau de menace</p>
            <p class="text-lg font-bold text-amber-600">MOYEN</p>
            </div>
            <div>
            <p class="text-xs text-slate-500">Santé infra</p>
            <p class="text-lg font-bold text-slate-800 dark:text-slate-100">99.8%</p>
            </div>
            <div>
            <p class="text-xs text-slate-500">AI Engine</p>
            <p class="text-lg font-bold text-emerald-600">SAIN</p>
            </div>
        </div>
        <div class="mt-4 p-3 rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-100 dark:border-amber-500/20 text-sm">
            <p class="font-medium text-amber-800 dark:text-amber-300">Préoccupation principale</p>
            <p class="text-amber-700 dark:text-amber-400 text-xs mt-0.5">Le phishing Mobile Money a augmenté de 18% cette semaine — recommander un renforcement de la sensibilisation.</p>
        </div>
        </div>

    </div>
    </template>

    <script setup lang="ts">
    import { ref } from 'vue'
    import { useI18n } from '@/i18n'

    const { t } = useI18n()

    const lastUpdate = ref('08:42:31')
    const uptime = ref(99.8)
    const aiLatency = ref(143)
    const activeIncidents = ref(3)

    const kpis = [
    { icon: '👥', label: 'Utilisateurs protégés', value: '1 284', trend: 4, accent: 'bg-blue-500', hint: 'Tous synchronisés' },
    { icon: '🔍', label: 'Emails analysés', value: '284 521', trend: 12, accent: 'bg-cyan-500', hint: 'Temps réel' },
    { icon: '🚨', label: 'Menaces détectées', value: '8 421', trend: -8, accent: 'bg-red-500', hint: '7 912 bloquées · 509 en quarantaine' },
    { icon: '📋', label: 'Incidents ouverts', value: '3', trend: null, accent: 'bg-amber-500', hint: '1 critique · 2 élevés' }
    ]

    const liveThreats = ref([
    { id: 1, time: '08:42:31', type: 'Credential Phishing', source: 'support@mtn-secure.tk', severity: 'critical' },
    { id: 2, time: '08:42:26', type: 'Malicious URL', source: 'orange-verif-cm.tk/verify', severity: 'high' },
    { id: 3, time: '08:42:19', type: 'Suspicious Attachment', source: 'invoice_2026.docm', severity: 'high' },
    { id: 4, time: '08:42:12', type: 'Impersonation', source: 'dir@afriland-secure.ga', severity: 'medium' },
    { id: 5, time: '08:41:58', type: 'Business Email Compromise', source: 'ceo@cameroon-corp.ga', severity: 'critical' },
    { id: 6, time: '08:41:47', type: 'Malware', source: 'update-camtel.zip', severity: 'high' },
    ])

    const chartBars = [
    { label: 'Lun', value: 40 }, { label: 'Mar', value: 65 }, { label: 'Mer', value: 50 },
    { label: 'Jeu', value: 80 }, { label: 'Ven', value: 70 }, { label: 'Sam', value: 30 }, { label: 'Dim', value: 45 }
    ]

    const activities = [
    { id: 1, icon: '🚨', action: 'Nouveau signalement confirmé par admin@phishguard.cm', time: 'Il y a 10 min', dot: '#ef4444' },
    { id: 2, icon: '👤', action: 'Utilisateur suspendu: fraude@suspect.cm', time: 'Il y a 1 heure', dot: '#f59e0b' },
    { id: 3, icon: '🤖', action: 'Modèle ML v2.4.1 déployé en production', time: 'Il y a 3 heures', dot: '#22d3ee' },
    { id: 4, icon: '🧠', action: 'Nouvelle catégorie de menace: SMS Banking', time: 'Il y a 5 heures', dot: '#8b5cf6' }
    ]
    </script>