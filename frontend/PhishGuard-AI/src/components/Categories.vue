    <script setup lang="ts">
    import { computed, onMounted } from "vue";
    import { useCategoriesStore } from "@/stores";
    import CategoryDetail from "./CategoriesDetail.vue";
    import type { ThreatColor } from "@/types";

    const store = useCategoriesStore();

    onMounted(() => {
    if (!store.categories.length) store.fetchCategories();
    });

    const colorClasses: Record<ThreatColor, string> = {
    red: "bg-red-50 text-red-700 border-red-200 hover:bg-red-100",
    orange: "bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100",
    purple: "bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100",
    pink: "bg-pink-50 text-pink-700 border-pink-200 hover:bg-pink-100",
    yellow: "bg-yellow-50 text-yellow-700 border-yellow-200 hover:bg-yellow-100",
    indigo: "bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100",
    teal: "bg-teal-50 text-teal-700 border-teal-200 hover:bg-teal-100",
    rose: "bg-rose-50 text-rose-700 border-rose-200 hover:bg-rose-100",
    gray: "bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100",
    violet: "bg-violet-50 text-violet-700 border-violet-200 hover:bg-violet-100",
    slate: "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100",
    green:
        "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100",
    };

    const activeCategory = computed(
    () => store.categories.find((c) => c.id === store.activeCategoryId) ?? null,
    );
    </script>

    <template>
    <section id="education" class="py-20 px-4 bg-slate-50">
        <div class="max-w-7xl mx-auto">
        <div class="text-center mb-14">
            <h2 class="text-3xl sm:text-4xl font-bold text-slate-800 font-display">
            12 menaces à connaître
            </h2>
            <p class="text-slate-500 mt-2 max-w-2xl mx-auto">
            Chaque catégorie détaille le mécanisme, les signaux d'alerte, et les
            bons réflexes.
            </p>
        </div>

        <div class="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            <button
            v-for="cat in store.categories"
            :key="cat.id"
            class="category-badge text-left rounded-xl border p-4 transition"
            :class="[
                colorClasses[cat.color],
                'hover:-translate-y-0.5 hover:shadow-lg',
            ]"
            @click="store.selectCategory(cat.id)"
            >
            <span class="font-semibold text-sm block">{{ cat.name }}</span>
            <p class="text-xs opacity-80 mt-1">{{ cat.description }}</p>
            </button>
        </div>

        <CategoryDetail
            v-if="activeCategory"
            :category="activeCategory"
            @close="store.clearSelection"
        />
        </div>
    </section>
    </template>

    <style scoped>
    .category-badge {
    transition:
        transform 0.2s ease,
        box-shadow 0.2s ease;
    }
    </style>
