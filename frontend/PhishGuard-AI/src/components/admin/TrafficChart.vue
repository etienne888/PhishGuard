  <script setup lang="ts">
  import { computed, ref } from 'vue'
  import type { AdminOverview } from '@/services/admin.service'

  /**
   * 14-day stacked bars of analyses by verdict. Status colours are validated
   * (dataviz validate_palette.js) for light and dark; identity is never colour
   * alone: legend with totals, hover tooltip, and a table view.
   */
  const props = defineProps<{ series: AdminOverview['series'] }>()

  const SERIES = [
    { key: 'phishing', label: 'Dangereux', icon: '🔴' },
    { key: 'suspicious', label: 'Suspects', icon: '🟠' },
    { key: 'safe', label: 'Sans danger', icon: '🟢' },
  ] as const

  const showTable = ref(false)
  const hovered = ref<number | null>(null)

  const max = computed(() => Math.max(1, ...props.series.map((d) => d.phishing + d.suspicious + d.safe)))
  const totals = computed(() => Object.fromEntries(SERIES.map((s) => [s.key, props.series.reduce((n, d) => n + d[s.key], 0)])))
  const dayLabel = (iso: string) => new Date(iso + 'T00:00:00').toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })

  function segments(day: AdminOverview['series'][number]) {
    // Stack bottom-up: safe, suspicious, phishing (the headline sits on top)
    return [...SERIES].reverse()
      .map((s) => ({ ...s, value: day[s.key], pct: (day[s.key] / max.value) * 100 }))
      .filter((s) => s.value > 0)
  }
  </script>

  <template>
    <div>
      <div class="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1">
        <span v-for="s in SERIES" :key="s.key" class="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300">
          <span class="swatch" :class="`c-${s.key}`"></span>{{ s.label }} <b class="tabular-nums">{{ totals[s.key] }}</b>
        </span>
        <button class="ml-auto text-xs text-blue-600 hover:underline dark:text-blue-400" @click="showTable = !showTable">
          {{ showTable ? 'Voir le graphique' : 'Voir en tableau' }}
        </button>
      </div>

      <table v-if="showTable" class="w-full text-xs">
        <thead class="text-left text-slate-500"><tr><th class="py-1">Jour</th><th v-for="s in SERIES" :key="s.key" class="text-right">{{ s.label }}</th></tr></thead>
        <tbody class="tabular-nums text-slate-700 dark:text-slate-300">
          <tr v-for="d in series" :key="d.date" class="border-t border-slate-100 dark:border-slate-800">
            <td class="py-1">{{ dayLabel(d.date) }}</td>
            <td v-for="s in SERIES" :key="s.key" class="text-right">{{ d[s.key] }}</td>
          </tr>
        </tbody>
      </table>

      <div v-else class="relative">
        <div class="flex h-44 items-end gap-1.5 border-b border-slate-200 dark:border-slate-700" role="img"
            :aria-label="`Analyses des 14 derniers jours : ${totals.phishing} dangereuses, ${totals.suspicious} suspectes, ${totals.safe} sans danger`">
          <div v-for="(d, i) in series" :key="d.date" class="relative flex h-full flex-1 cursor-default flex-col justify-end"
              @mouseenter="hovered = i" @mouseleave="hovered = null">
            <div class="flex flex-col-reverse gap-[2px]">
              <div v-for="seg in segments(d)" :key="seg.key" class="bar" :class="`c-${seg.key}`" :style="{ height: `calc(${seg.pct} * 1.76px)` }"></div>
            </div>
            <div v-if="hovered === i" class="tooltip">
              <p class="font-semibold">{{ dayLabel(d.date) }}</p>
              <p v-for="s in SERIES" :key="s.key">{{ s.icon }} {{ s.label }} : <b>{{ d[s.key] }}</b></p>
            </div>
          </div>
        </div>
        <div class="mt-1 flex gap-1.5 text-[10px] text-slate-400">
          <span v-for="(d, i) in series" :key="d.date" class="flex-1 text-center">{{ i % 2 === 0 ? dayLabel(d.date) : '' }}</span>
        </div>
      </div>
    </div>
  </template>

  <style scoped>
  .c-phishing { --c: #dc2626; }
  .c-suspicious { --c: #f59e0b; }
  .c-safe { --c: #10b981; }
  :global(.dark) .c-phishing { --c: #f25555; }
  :global(.dark) .c-suspicious { --c: #e0950a; }
  :global(.dark) .c-safe { --c: #12a877; }
  .swatch { width: 10px; height: 10px; border-radius: 3px; background: var(--c); }
  .bar { background: var(--c); min-height: 2px; }
  .bar:last-child { border-radius: 4px 4px 0 0; }
  .tooltip {
    position: absolute; bottom: calc(100% + 6px); left: 50%; transform: translateX(-50%); z-index: 10;
    white-space: nowrap; padding: 6px 8px; border-radius: 8px; font-size: 11px;
    background: #0f172a; color: #f1f5f9; box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25); pointer-events: none;
  }
  </style>
