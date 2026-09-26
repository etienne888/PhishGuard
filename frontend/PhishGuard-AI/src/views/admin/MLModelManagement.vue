    <template>
    <div class="space-y-6">

        <!-- Header -->
        <div class="flex items-start justify-between gap-4">
        <div>
            <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100">🤖 {{ t('admin.page.models') }}</h1>
            <p class="text-sm text-slate-500">{{ t('models.subtitle') }}</p>
        </div>
        <div class="flex items-center gap-2">
            <span class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20">
            <span class="relative flex h-2 w-2">
                <span class="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
                <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            <span class="text-xs font-semibold text-emerald-700 dark:text-emerald-400">{{ t('health.operational').toUpperCase() }}</span>
            </span>
        </div>
        </div>

        <!-- Model banner -->
        <div class="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 text-white p-6">
        <div class="pointer-events-none absolute inset-0 opacity-20" style="background-image:radial-gradient(circle at 20% 30%, #22d3ee 0, transparent 40%), radial-gradient(circle at 80% 70%, #3b82f6 0, transparent 40%);" />
        <div class="relative grid grid-cols-1 md:grid-cols-4 gap-6">
            <div class="md:col-span-2">
            <div class="text-[11px] uppercase tracking-wider text-slate-400">{{ t('models.inProduction') }}</div>
            <div class="mt-1 text-3xl font-bold">PhishGuard-XGB <span class="text-cyan-300">v{{ currentModel.version }}</span></div>
            <div class="mt-2 text-sm text-slate-400">{{ t('models.trainedOn', { date: fmt(currentModel.lastTrained, true) }) }} · {{ t('models.production') }}</div>
            <div class="mt-4 flex flex-wrap gap-2">
                <span class="text-[11px] px-2.5 py-1 rounded-full bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">F1 {{ currentModel.f1 }}%</span>
                <span class="text-[11px] px-2.5 py-1 rounded-full bg-cyan-500/15 text-cyan-300 border border-cyan-500/30">{{ t('models.latency', { ms: 143 }) }}</span>
                <span class="text-[11px] px-2.5 py-1 rounded-full bg-blue-500/15 text-blue-300 border border-blue-500/30">82 req/min</span>
                <span class="text-[11px] px-2.5 py-1 rounded-full bg-slate-500/20 text-slate-300 border border-slate-500/30">{{ t('models.errorRate', { n: '0.08' }) }}</span>
            </div>
            </div>
            <div class="md:col-span-2 grid grid-cols-2 gap-3">
            <div class="bg-white/5 rounded-xl p-3 border border-white/10">
                <div class="text-[11px] text-slate-400">{{ t('models.accuracy') }}</div>
                <div class="text-2xl font-bold tabular-nums">{{ currentModel.accuracy }}%</div>
            </div>
            <div class="bg-white/5 rounded-xl p-3 border border-white/10">
                <div class="text-[11px] text-slate-400">{{ t('models.recall') }}</div>
                <div class="text-2xl font-bold tabular-nums">{{ currentModel.recall }}%</div>
            </div>
            <div class="bg-white/5 rounded-xl p-3 border border-white/10">
                <div class="text-[11px] text-slate-400">{{ t('models.trainingData') }}</div>
                <div class="text-2xl font-bold tabular-nums">{{ currentModel.dataSize }}</div>
            </div>
            <div class="bg-white/5 rounded-xl p-3 border border-white/10">
                <div class="text-[11px] text-slate-400">{{ t('models.lastDeploy') }}</div>
                <div class="text-lg font-bold">{{ fmt('2026-09-08') }}</div>
            </div>
            </div>
        </div>
        <div class="relative mt-6 flex flex-wrap gap-2">
            <button @click="retrain" class="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 text-slate-900 text-sm font-semibold rounded-lg transition">
            <i class="fas fa-rotate-right mr-1.5"></i> {{ t('admin.models.retrain') }}
            </button>
            <button @click="viewMetrics" class="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-sm font-medium rounded-lg transition border border-white/10">
            {{ t('models.viewMetrics') }}
            </button>
            <button @click="viewRegistry" class="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-sm font-medium rounded-lg transition border border-white/10">
            {{ t('models.registry') }}
            </button>
        </div>
        </div>

        <!-- Model health + drift -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

        <!-- Health -->
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
            <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200">🧪 {{ t('models.health') }}</h3>
            <span class="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-medium">● {{ t('models.healthy') }}</span>
            </div>
            <div class="space-y-4">
            <div>
                <div class="flex items-center justify-between text-xs mb-1">
                <span class="text-slate-500">{{ t('models.confidence') }}</span>
                <span class="font-semibold text-slate-700 dark:text-slate-200 tabular-nums">92.4%</span>
                </div>
                <div class="h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div class="h-full rounded-full bg-emerald-500 transition-all duration-700" style="width: 92.4%" />
                </div>
            </div>
            <div>
                <div class="flex items-center justify-between text-xs mb-1">
                <span class="text-slate-500">{{ t('models.dataQuality') }}</span>
                <span class="font-semibold text-slate-700 dark:text-slate-200 tabular-nums">88%</span>
                </div>
                <div class="h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div class="h-full rounded-full bg-cyan-500 transition-all duration-700" style="width: 88%" />
                </div>
            </div>
            <div class="grid grid-cols-2 gap-3 pt-2">
                <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div class="text-[11px] text-slate-500">{{ t('models.drift') }}</div>
                <div class="text-lg font-bold text-emerald-600">{{ t('level.low').toUpperCase() }}</div>
                </div>
                <div class="p-3 rounded-lg bg-slate-50 dark:bg-slate-800/40">
                <div class="text-[11px] text-slate-500">{{ t('models.trend') }}</div>
                <div class="text-lg font-bold text-emerald-600">↗ +2.4%</div>
                </div>
            </div>
            </div>
        </div>

        <!-- Drift -->
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
            <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200">📉 {{ t('models.drift') }}</h3>
            <span class="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-medium">{{ t('level.low').toUpperCase() }}</span>
            </div>
            <div class="space-y-4">
            <div v-for="d in drift" :key="d.label">
                <div class="flex items-center justify-between text-xs mb-1">
                <span class="text-slate-500">{{ t('models.driftDays', { n: d.days }) }}</span>
                <span class="font-semibold tabular-nums" :class="d.level === 'low' ? 'text-emerald-600' : d.level === 'medium' ? 'text-amber-600' : 'text-red-600'">{{ d.value }}%</span>
                </div>
                <div class="h-1.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden">
                <div class="h-full rounded-full transition-all duration-700"
                    :class="d.level === 'low' ? 'bg-emerald-500' : d.level === 'medium' ? 'bg-amber-500' : 'bg-red-500'"
                    :style="{ width: d.value + '%' }" />
                </div>
            </div>
            <div class="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20 text-xs">
                <p class="font-semibold text-emerald-800 dark:text-emerald-300">{{ t('models.recommendation') }}</p>
                <p class="text-emerald-700 dark:text-emerald-400 mt-0.5">{{ t('models.recommendationText') }}</p>
            </div>
            </div>
        </div>
        </div>

        <!-- Feedback loop -->
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
        <div class="flex items-center justify-between mb-4">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200">🔄 {{ t('models.feedbackLoop') }}</h3>
            <span class="text-[11px] text-slate-400">{{ t('models.last30') }}</span>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            <div class="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/40 text-center">
            <div class="text-2xl font-bold tabular-nums text-slate-800 dark:text-slate-100">4 281</div>
            <div class="text-[11px] text-slate-500 uppercase tracking-wider mt-1">{{ t('models.reviewed') }}</div>
            </div>
            <div class="p-4 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 text-center">
            <div class="text-2xl font-bold tabular-nums text-emerald-700 dark:text-emerald-300">3 912</div>
            <div class="text-[11px] text-emerald-600 uppercase tracking-wider mt-1">{{ t('models.confirmed') }}</div>
            </div>
            <div class="p-4 rounded-lg bg-amber-50 dark:bg-amber-500/10 text-center">
            <div class="text-2xl font-bold tabular-nums text-amber-700 dark:text-amber-300">219</div>
            <div class="text-[11px] text-amber-600 uppercase tracking-wider mt-1">{{ t('models.falsePositives') }}</div>
            </div>
            <div class="p-4 rounded-lg bg-slate-50 dark:bg-slate-800/40 text-center">
            <div class="text-2xl font-bold tabular-nums text-slate-800 dark:text-slate-100">150</div>
            <div class="text-[11px] text-slate-500 uppercase tracking-wider mt-1">{{ t('models.uncertain') }}</div>
            </div>
        </div>

        <div class="flex items-center gap-2 overflow-x-auto pb-2">
            <div v-for="(step, i) in feedbackFlow" :key="step" class="flex items-center gap-2 flex-shrink-0">
            <span class="px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-200 whitespace-nowrap">{{ t(`models.flow.${step}`) }}</span>
            <svg v-if="i < feedbackFlow.length - 1" class="w-4 h-4 text-slate-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M12 5l7 7-7 7" /></svg>
            </div>
        </div>

        <p class="mt-3 text-[11px] text-slate-500">
            ⓘ {{ t('models.controlled') }}
        </p>
        </div>

        <!-- Model registry -->
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
            <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200">📋 {{ t('models.registry') }}</h3>
            <span class="text-[11px] text-slate-400">{{ t('models.versions', { n: pastModels.length + 1 }) }}</span>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
            <thead class="bg-slate-50 dark:bg-slate-800/50">
                <tr>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">{{ t('models.col.version') }}</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">{{ t('audit.col.status') }}</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">F1</th>
                <th class="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">{{ t('models.col.deployed') }}</th>
                <th class="text-center px-4 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">{{ t('users.col.actions') }}</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
                <tr class="bg-emerald-50/40 dark:bg-emerald-500/5">
                <td class="px-4 py-3 text-sm font-bold text-emerald-700 dark:text-emerald-300">v{{ currentModel.version }}</td>
                <td class="px-4 py-3"><span class="text-xs px-2.5 py-1 rounded-full font-medium bg-emerald-100 text-emerald-700">{{ t('models.production') }}</span></td>
                <td class="px-4 py-3 text-xs text-slate-700 dark:text-slate-300 tabular-nums">{{ currentModel.f1 }}%</td>
                <td class="px-4 py-3 text-xs text-slate-500">{{ fmt('2026-09-08') }}</td>
                <td class="px-4 py-3 text-center"><span class="text-xs text-slate-400">— {{ t('common.active').toLowerCase() }} —</span></td>
                </tr>
                <tr v-for="model in pastModels" :key="model.version" class="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition">
                <td class="px-4 py-3 text-sm font-medium text-slate-700 dark:text-slate-200">v{{ model.version }}</td>
                <td class="px-4 py-3"><span class="text-xs px-2.5 py-1 rounded-full font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">{{ t('models.archived') }}</span></td>
                <td class="px-4 py-3 text-xs text-slate-600 dark:text-slate-400 tabular-nums">{{ model.f1 }}%</td>
                <td class="px-4 py-3 text-xs text-slate-500">{{ fmt(model.date) }}</td>
                <td class="px-4 py-3">
                    <div class="flex items-center justify-center gap-1">
                    <button class="p-1.5 rounded hover:bg-blue-50 dark:hover:bg-blue-500/10 text-blue-600 transition" :title="t('models.compare')">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3H5a2 2 0 0 0-2 2v4M15 3h4a2 2 0 0 1 2 2v4M9 21H5a2 2 0 0 1-2-2v-4M15 21h4a2 2 0 0 0 2-2v-4" /></svg>
                    </button>
                    <button @click="rollback(model)" class="p-1.5 rounded hover:bg-amber-50 dark:hover:bg-amber-500/10 text-amber-600 transition" :title="t('models.rollback')">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4v5h.582m15.356 2A8.001 8.001 0 0 0 4.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 0 1-15.357-2m15.357 2H15" /></svg>
                    </button>
                    <button @click="deploy(model)" class="p-1.5 rounded hover:bg-emerald-50 dark:hover:bg-emerald-500/10 text-emerald-600 transition" :title="t('models.deploy')">
                        <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M5 12l7-7 7 7" /></svg>
                    </button>
                    </div>
                </td>
                </tr>
            </tbody>
            </table>
        </div>
        </div>

        <!-- Last training -->
        <div class="bg-white dark:bg-slate-900 rounded-xl border border-slate-100 dark:border-slate-800 shadow-sm p-6">
        <h3 class="text-sm font-semibold text-slate-700 dark:text-slate-200 mb-3">⏳ {{ t('models.lastTraining') }}</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div><div class="text-xs text-slate-500">{{ t('audit.col.status') }}</div><div class="font-semibold text-emerald-600">✓ {{ t('models.done') }}</div></div>
            <div><div class="text-xs text-slate-500">{{ t('models.duration') }}</div><div class="font-semibold text-slate-700 dark:text-slate-200">4 min 32s</div></div>
            <div><div class="text-xs text-slate-500">{{ t('models.samples') }}</div><div class="font-semibold text-slate-700 dark:text-slate-200 tabular-nums">12 847</div></div>
            <div><div class="text-xs text-slate-500">{{ t('models.environment') }}</div><div class="font-semibold text-slate-700 dark:text-slate-200">{{ t('models.production') }}</div></div>
        </div>
        </div>

    </div>
    </template>

    <script setup lang="ts">
    import { ref } from 'vue'
    import { useI18n } from '@/i18n'

    const { t, intlLocale } = useI18n()

    /** Demo dates are stored as ISO strings and shown in the interface language. */
    function fmt(iso: string, withTime = false) {
    return new Date(iso).toLocaleString(intlLocale.value, withTime ? { dateStyle: 'medium', timeStyle: 'short' } : { dateStyle: 'medium' })
    }

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
    dataSize: '12 847',
    lastTrained: '2026-09-15T08:32:00'
    })

    const pastModels = ref([
    { version: '2.4.0', date: '2026-09-10', accuracy: 93.2, recall: 91.5, f1: 92.3 },
    { version: '2.3.2', date: '2026-09-05', accuracy: 91.8, recall: 89.7, f1: 90.7 },
    { version: '2.3.0', date: '2026-08-28', accuracy: 89.5, recall: 88.2, f1: 88.8 },
    ])

    const drift = [
    { label: 'd7', days: 7, value: 12, level: 'low' },
    { label: 'd30', days: 30, value: 28, level: 'low' },
    { label: 'd90', days: 90, value: 42, level: 'medium' },
    ]

    // Steps are keys under models.flow.*
    const feedbackFlow = ['prediction', 'feedback', 'label', 'dataset', 'evaluation', 'retraining', 'newModel', 'deployment']

    function retrain() {
    if (!confirm(t('models.confirmRetrain'))) return
    alert(`🔄 ${t('models.retrainQueued')}`)
    }
    function viewMetrics() { alert(`📊 ${t('models.metricsAlert')}`) }
    function viewRegistry() { alert(`📋 ${t('models.registry')}`) }
    function rollback(m: any) {
    if (!confirm(t('models.confirmRollback', { v: m.version }))) return
    alert(`↩️ ${t('models.rollbackRequested', { v: m.version })}`)
    }
    function deploy(m: any) {
    if (!confirm(t('models.confirmDeploy', { v: m.version }))) return
    alert(`🚀 ${t('models.deployConfirmed', { v: m.version })}`)
    }
    </script>