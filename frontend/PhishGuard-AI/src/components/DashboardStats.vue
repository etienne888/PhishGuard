    <script setup lang="ts">
    import { ref, onMounted, nextTick } from 'vue';

    type IconKey = 'revenue' | 'users' | 'orders' | 'growth' | 'alert' | 'shield' | 'clock' | 'chart';

    interface StatItem {
    label: string;
    value: string;
    tone: string;
    icon?: IconKey;
    progress?: number; // 0-100
    }

    const props = defineProps<{ stats: StatItem[] }>();

    const toneColor: Record<string, string> = {
    'text-emerald-600': '#10b981',
    'text-rose-600': '#ef4444',
    'text-blue-600': '#3b82f6',
    'text-amber-600': '#f59e0b',
    'text-purple-600': '#8b5cf6',
    'text-slate-600': '#64748b',
    };

    const toneTint: Record<string, string> = {
    'text-emerald-600': '#ecfdf5',
    'text-rose-600': '#fef2f2',
    'text-blue-600': '#eff6ff',
    'text-amber-600': '#fffbeb',
    'text-purple-600': '#f5f3ff',
    'text-slate-600': '#f8fafc',
    };

    const getProgressColor = (tone: string) => toneColor[tone] || '#64748b';
    const getTint = (tone: string) => toneTint[tone] || '#f8fafc';

    // Animated ring values, staggered on mount
    const animatedProgress = ref<number[]>(props.stats.map(() => 0));

    onMounted(async () => {
    await nextTick();
    props.stats.forEach((stat, i) => {
        setTimeout(() => {
        animatedProgress.value[i] = stat.progress || 0;
        }, i * 80);
    });
    });

    const CIRCUMFERENCE = 150.72;
    const dashArray = (progress: number) => `${(progress * CIRCUMFERENCE) / 100} ${CIRCUMFERENCE}`;
    </script>

    <template>
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
        v-for="(stat, i) in props.stats"
        :key="stat.label"
        class="relative rounded-xl bg-white p-5 border border-slate-200/60 hover:border-slate-300 transition-colors duration-300 hover:shadow-lg"
        >
        <div class="flex items-center gap-4">
            <!-- Circular progress with icon on tinted disc -->
            <div class="relative flex-shrink-0 h-14 w-14">
            <svg class="h-14 w-14 -rotate-90 transform" viewBox="0 0 56 56">
                <circle cx="28" cy="28" r="24" fill="none" stroke="#e2e8f0" stroke-width="4" />
                <circle
                cx="28"
                cy="28"
                r="24"
                fill="none"
                :stroke="getProgressColor(stat.tone)"
                stroke-width="4"
                stroke-linecap="round"
                :stroke-dasharray="dashArray(animatedProgress[i] ?? 0)"
                class="transition-[stroke-dasharray] duration-[1200ms] ease-out"
                />
            </svg>

            <!-- tinted disc + icon -->
            <div
                class="absolute inset-[9px] flex items-center justify-center rounded-full"
                :style="{ backgroundColor: getTint(stat.tone) }"
            >
                <!-- Revenue / currency -->
                <svg v-if="stat.icon === 'revenue'" viewBox="0 0 24 24" class="h-5 w-5" fill="none" :stroke="getProgressColor(stat.tone)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                </svg>

                <!-- Users -->
                <svg v-else-if="stat.icon === 'users'" viewBox="0 0 24 24" class="h-5 w-5" fill="none" :stroke="getProgressColor(stat.tone)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
                </svg>

                <!-- Orders / package -->
                <svg v-else-if="stat.icon === 'orders'" viewBox="0 0 24 24" class="h-5 w-5" fill="none" :stroke="getProgressColor(stat.tone)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 8l-9-5-9 5 9 5 9-5z" />
                <path d="M3 8v8l9 5 9-5V8M12 13v8" />
                </svg>

                <!-- Growth / trending up -->
                <svg v-else-if="stat.icon === 'growth'" viewBox="0 0 24 24" class="h-5 w-5" fill="none" :stroke="getProgressColor(stat.tone)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 17l6-6 4 4 8-8" />
                <path d="M17 7h4v4" />
                </svg>

                <!-- Alert -->
                <svg v-else-if="stat.icon === 'alert'" viewBox="0 0 24 24" class="h-5 w-5" fill="none" :stroke="getProgressColor(stat.tone)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <path d="M12 9v4M12 17h.01" />
                </svg>

                <!-- Shield (e.g. fraud / security) -->
                <svg v-else-if="stat.icon === 'shield'" viewBox="0 0 24 24" class="h-5 w-5" fill="none" :stroke="getProgressColor(stat.tone)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                </svg>

                <!-- Clock -->
                <svg v-else-if="stat.icon === 'clock'" viewBox="0 0 24 24" class="h-5 w-5" fill="none" :stroke="getProgressColor(stat.tone)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M12 6v6l4 2" />
                </svg>

                <!-- Default: bar chart -->
                <svg v-else viewBox="0 0 24 24" class="h-5 w-5" fill="none" :stroke="getProgressColor(stat.tone)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 3v18h18" />
                <path d="M7 15v3M12 10v8M17 6v12" />
                </svg>
            </div>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
            <span :class="['block text-xl font-bold tracking-tight', stat.tone || 'text-slate-900']">
                {{ stat.value }}
            </span>
            <p class="mt-0.5 text-xs font-medium text-slate-500 truncate">
                {{ stat.label }}
            </p>
            <div v-if="stat.progress !== undefined" class="mt-1 text-xs text-slate-400">
                {{ stat.progress }}% of goal
            </div>
            </div>
        </div>
        </div>
    </div>
    </template>