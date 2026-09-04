    <script setup lang="ts">
    import type { ThreatCategory } from '@/types'

    defineProps<{ category: ThreatCategory }>()
    defineEmits<{ close: [] }>()
    </script>

    <template>
    <div class="mt-10">
        <div class="bg-white rounded-2xl shadow-xl border border-slate-100 p-6 sm:p-8">
        <div class="flex items-start justify-between gap-4">
            <div>
            <span class="inline-block text-xs font-semibold px-3 py-1 rounded-full mb-2 bg-blue-50 text-blue-700">
                Menace n°{{ category.priority }}
            </span>
            <h3 class="text-2xl font-bold text-slate-800 font-display">{{ category.name }}</h3>
            <p class="text-slate-600 mt-2 max-w-2xl">{{ category.description }}</p>
            </div>
            <button class="text-slate-400 hover:text-slate-600 transition shrink-0" aria-label="Fermer" @click="$emit('close')">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" />
            </svg>
            </button>
        </div>
        <div class="grid sm:grid-cols-2 gap-4 mt-6">
            <div class="bg-slate-50 rounded-xl p-4">
            <span class="text-xs font-semibold text-slate-400">Mécanisme</span>
            <p class="text-sm text-slate-700 mt-1">{{ category.mechanism }}</p>
            </div>
            <div class="bg-slate-50 rounded-xl p-4">
            <span class="text-xs font-semibold text-slate-400">Signaux d'alerte</span>
            <p class="text-sm text-slate-700 mt-1">{{ category.warningSigns }}</p>
            </div>
            <div class="bg-slate-50 rounded-xl p-4 sm:col-span-2">
            <span class="text-xs font-semibold text-slate-400">Que faire</span>
            <p class="text-sm text-slate-700 mt-1">{{ category.recommendedAction }}</p>
            </div>
        </div>
        </div>
    </div>
    </template>
