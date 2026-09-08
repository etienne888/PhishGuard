<template>
    <div class="space-y-6">
        <!-- Page Header -->
        <div>
            <h1 class="text-2xl font-bold text-slate-800 font-display">📊 Aperçu</h1>
            <p class="text-sm text-slate-500">Vue d'ensemble de la plateforme PhishGuard-AI</p>
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <div v-for="kpi in kpis" :key="kpi.label" class="bg-white rounded-xl border border-slate-100 shadow-md p-5">
                <div class="flex items-center justify-between">
                    <span class="text-2xl">{{ kpi.icon }}</span>
                    <span v-if="kpi.trend" class="text-xs font-semibold" :class="kpi.trend > 0 ? 'text-emerald-600' : 'text-red-600'">
                        {{ kpi.trend > 0 ? '+' : '' }}{{ kpi.trend }}%
                    </span>
                </div>
                <div class="text-2xl font-bold text-slate-800 mt-3">{{ kpi.value }}</div>
                <div class="text-sm text-slate-500 mt-1">{{ kpi.label }}</div>
            </div>
        </div>

        <!-- Chart + Activity -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Analyses over time (placeholder) -->
            <div class="lg:col-span-2 bg-white rounded-xl border border-slate-100 shadow-md p-6">
                <h3 class="text-sm font-semibold text-slate-700 mb-4">📈 Analyses au fil du temps</h3>
                <div class="h-64 flex items-end gap-2">
                    <div v-for="(bar, i) in chartBars" :key="i" class="flex-1 flex flex-col items-center gap-1">
                        <div class="w-full rounded-t-md bg-gradient-to-t from-blue-600 to-cyan-500"
                            :style="{ height: bar.value + '%' }"></div>
                        <span class="text-[10px] text-slate-400">{{ bar.label }}</span>
                    </div>
                </div>
            </div>

            <!-- Recent activity -->
            <div class="bg-white rounded-xl border border-slate-100 shadow-md p-6">
                <h3 class="text-sm font-semibold text-slate-700 mb-4">🕒 Activité récente</h3>
                <div class="space-y-4">
                    <div v-for="activity in activities" :key="activity.id" class="flex gap-3">
                        <span class="text-lg">{{ activity.icon }}</span>
                        <div>
                            <p class="text-sm text-slate-700">{{ activity.action }}</p>
                            <p class="text-xs text-slate-400">{{ activity.time }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script setup lang="ts">
const kpis = [
    { icon: '👥', label: 'Utilisateurs totaux', value: '1 284', trend: 4 },
    { icon: '🔍', label: 'Analyses effectuées', value: '9 672', trend: 12 },
    { icon: '🚨', label: 'Menaces détectées aujourd\'hui', value: '37', trend: -8 },
    { icon: '📋', label: 'Signalements en attente', value: '12', trend: null }
]

const chartBars = [
    { label: 'Lun', value: 40 },
    { label: 'Mar', value: 65 },
    { label: 'Mer', value: 50 },
    { label: 'Jeu', value: 80 },
    { label: 'Ven', value: 70 },
    { label: 'Sam', value: 30 },
    { label: 'Dim', value: 45 }
]

const activities = [
    { id: 1, icon: '🚨', action: 'Nouveau signalement confirmé par admin@phishguard.cm', time: 'Il y a 10 min' },
    { id: 2, icon: '👤', action: 'Utilisateur suspendu: fraude@suspect.cm', time: 'Il y a 1 heure' },
    { id: 3, icon: '🤖', action: 'Modèle ML v2.3 déployé en production', time: 'Il y a 3 heures' },
    { id: 4, icon: '🧠', action: 'Nouvelle catégorie de menace ajoutée: SMS Banking', time: 'Il y a 5 heures' }
]
</script>
