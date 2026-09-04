    <script setup lang="ts">
    interface StatItem {
    label: string;
    value: string;
    tone: string;
    }

    const props = defineProps<{ stats: StatItem[] }>();
    </script>

    <template>
    <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <div
        v-for="stat in props.stats"
        :key="stat.label"
        class="rounded-2xl border border-slate-200 bg-white p-5 shadow-card"
        >
        <div :class="['text-2xl font-bold', stat.tone]">{{ stat.value }}</div>
        <div class="mt-2 text-sm text-slate-500">{{ stat.label }}</div>
        </div>
    </div>
    </template>
