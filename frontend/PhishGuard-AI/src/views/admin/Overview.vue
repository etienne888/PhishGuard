<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import TrafficChart from '@/components/admin/TrafficChart.vue'
import ThreatMap from '@/components/admin/ThreatMap.vue'
import ReviewDrawer from '@/components/admin/ReviewDrawer.vue'
import { adminOpsService, adminService } from '@/services/admin.service'
import { useAdminOpsStore } from '@/stores/adminOps'
import { useNotificationsStore } from '@/stores/notifications'
import { STATUS_META, formatDate, timeAgo } from '@/utils/risk'

/** Command centre: everything happening on the platform, live, with direct controls. */
const REFRESH_MS = 15_000

const router = useRouter()
const ops = useAdminOpsStore()
const toast = useNotificationsStore()
const data = computed(() => ops.overview)

const live = ref(true)
const lastRefresh = ref<Date | null>(null)
const selected = ref<number | null>(null)
const freshIds = ref<Set<number>>(new Set())
let timer: number | undefined

async function refresh() {
  const before = new Set(data.value?.latest.map((a) => a.id) ?? [])
  await ops.load()
  lastRefresh.value = new Date()
  // Flash analyses that arrived since the previous refresh
  if (before.size) freshIds.value = new Set(data.value?.latest.filter((a) => !before.has(a.id)).map((a) => a.id) ?? [])
}

function schedule() {
  window.clearInterval(timer)
  if (live.value) timer = window.setInterval(refresh, REFRESH_MS)
}
watch(live, schedule)
onMounted(() => { void refresh(); schedule() })
onBeforeUnmount(() => window.clearInterval(timer))

const kpis = computed(() => {
  const d = data.value
  if (!d) return []
  return [
    { label: "Analyses aujourd'hui", value: d.analyses.today, hint: `${d.analyses.last_7_days} sur 7 jours`, tone: 'text-slate-800 dark:text-white' },
    { label: 'Menaces détectées', value: d.analyses.phishing, hint: `${d.analyses.phishing_rate}% des analyses`, tone: 'text-red-600 dark:text-red-400' },
    { label: 'Messages suspects', value: d.analyses.suspicious, hint: 'à surveiller', tone: 'text-amber-600 dark:text-amber-400' },
    { label: 'À examiner', value: d.review.pending, hint: `${d.review.reported} signalés par les usagers`, tone: 'text-blue-600 dark:text-blue-400', to: '/admin/reports' },
    { label: 'Utilisateurs', value: d.users.total, hint: `+${d.users.new_7_days} cette semaine`, tone: 'text-slate-800 dark:text-white', to: '/admin/users' },
    { label: 'Comptes protégés OTP', value: `${d.users.mfa_rate}%`, hint: `${d.users.suspended} compte(s) suspendu(s)`, tone: 'text-emerald-600 dark:text-emerald-400' },
  ]
})

async function toggleUser(user: { id: number; status: string; email: string }) {
  const suspend = user.status !== 'suspended'
  if (suspend && !confirm(`Suspendre le compte ${user.email} ?`)) return
  try {
    await (suspend ? adminService.suspendUser(user.id) : adminService.reactivateUser(user.id))
    toast.push(suspend ? 'Compte suspendu.' : 'Compte réactivé.', 'success')
    await refresh()
  } catch { /* toast shown by apiFetch */ }
}

const QUICK_ACTIONS = [
  { label: 'Examiner les signalements', icon: '🚩', to: '/admin/reports' },
  { label: 'Gérer la liste blanche', icon: '🏛️', to: '/admin/whitelist' },
  { label: 'Gérer les utilisateurs', icon: '👥', to: '/admin/users' },
  { label: 'Paramètres de sécurité', icon: '⚙️', to: '/admin/settings' },
]
</script>

<template>
  <div class="space-y-5">
    <!-- Command bar -->
    <section class="relative overflow-hidden rounded-2xl bg-slate-900 p-5 text-white">
      <div class="scan" aria-hidden="true"></div>
      <div class="relative flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div class="flex items-center gap-2 text-xs font-semibold">
            <span class="relative flex h-2.5 w-2.5">
              <span v-if="live" class="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
              <span class="relative inline-flex h-2.5 w-2.5 rounded-full" :class="live ? 'bg-emerald-400' : 'bg-slate-500'"></span>
            </span>
            <span :class="live ? 'text-emerald-300' : 'text-slate-400'">{{ live ? 'EN DIRECT' : 'EN PAUSE' }}</span>
            <span class="text-slate-500">· mis à jour {{ lastRefresh ? lastRefresh.toLocaleTimeString('fr-FR') : '…' }}</span>
          </div>
          <h1 class="mt-1 text-2xl font-bold">Centre de commande</h1>
          <p class="text-sm text-slate-400">Toutes les opérations de la plateforme, en temps réel.</p>
        </div>
        <div class="flex flex-wrap items-center gap-2 text-xs">
          <span class="rounded-lg border border-cyan-400/40 bg-cyan-400/10 px-3 py-1.5 font-mono font-semibold text-cyan-200">⚙️ {{ data?.engine.name ?? 'PhishGuard' }}</span>
          <span class="chip" :class="data ? 'ok' : 'off'">🗄️ Base de données</span>
          <span v-for="c in data?.engine.components ?? []" :key="c.key" class="chip" :class="c.active ? 'ok' : 'off'" :title="c.note ?? ''">
            {{ c.active ? '●' : '○' }} {{ c.label }}<template v-if="c.note"> · {{ c.note }}</template>
          </span>
          <span class="chip ok">🏛️ {{ data?.engine.whitelist_domains ?? '…' }} domaines officiels</span>
          <button class="rounded-lg border border-slate-600 px-3 py-1.5 font-medium hover:border-slate-400" @click="live = !live">{{ live ? '⏸ Pause' : '▶ Reprendre' }}</button>
          <button class="rounded-lg bg-cyan-400 px-3 py-1.5 font-semibold text-slate-900 hover:bg-cyan-300" :disabled="ops.isLoading" @click="refresh">↻ Actualiser</button>
        </div>
      </div>
    </section>

    <p v-if="ops.error" class="rounded-xl bg-red-50 p-4 text-sm text-red-700 dark:bg-red-500/10 dark:text-red-300">{{ ops.error }}</p>

    <!-- Priority alert -->
    <button v-if="data?.review.reported" class="flex w-full items-center gap-3 rounded-2xl border border-red-200 bg-red-50 p-4 text-left transition hover:bg-red-100 dark:border-red-500/30 dark:bg-red-500/10"
            @click="router.push('/admin/reports')">
      <span class="text-2xl">🚩</span>
      <span class="flex-1">
        <span class="block font-semibold text-red-800 dark:text-red-200">{{ data.review.reported }} signalement(s) d'usagers en attente de décision</span>
        <span class="text-sm text-red-700/80 dark:text-red-300/80">Confirmez ou rejetez-les : chaque décision améliore le modèle.</span>
      </span>
      <span class="text-sm font-semibold text-red-700 dark:text-red-300">Traiter →</span>
    </button>

    <!-- KPIs -->
    <section class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
      <component :is="k.to ? 'button' : 'div'" v-for="k in kpis" :key="k.label" class="card p-4 text-left" :class="{ 'transition hover:border-blue-300': k.to }"
                 @click="k.to && router.push(k.to)">
        <p class="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{{ k.label }}</p>
        <p class="mt-1 text-2xl font-bold tabular-nums" :class="k.tone">{{ k.value }}</p>
        <p class="text-xs text-slate-400">{{ k.hint }}</p>
      </component>
    </section>

    <!-- Live threat map -->
    <ThreatMap @open="(id) => (selected = id)" />

    <div class="grid gap-5 xl:grid-cols-3">
      <!-- Traffic -->
      <section class="card p-5 xl:col-span-2">
        <h2 class="font-semibold">Trafic d'analyses · 14 derniers jours</h2>
        <p class="mb-3 text-xs text-slate-500">{{ data?.analyses.total ?? 0 }} analyses au total · {{ data?.analyses.anonymous_share ?? 0 }}% faites par des visiteurs non connectés</p>
        <TrafficChart v-if="data" :series="data.series" />
      </section>

      <!-- Live feed -->
      <section class="card flex flex-col">
        <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-800">
          <h2 class="font-semibold">Flux en direct</h2>
          <span class="text-[11px] text-slate-400">actualisé toutes les 15 s</span>
        </div>
        <p v-if="data && !data.latest.length" class="p-6 text-center text-sm text-slate-400">Aucune analyse pour le moment.</p>
        <ul class="flex-1 divide-y divide-slate-100 dark:divide-slate-800">
          <li v-for="a in data?.latest ?? []" :key="a.id" :class="{ fresh: freshIds.has(a.id) }">
            <button class="flex w-full items-center gap-3 px-4 py-2.5 text-left hover:bg-slate-50 dark:hover:bg-slate-800/60" @click="selected = a.id">
              <span class="h-2.5 w-2.5 flex-shrink-0 rounded-full" :class="STATUS_META[a.status].dot"></span>
              <span class="min-w-0 flex-1">
                <span class="block truncate text-sm">{{ a.preview }}</span>
                <span class="block truncate text-[11px] text-slate-400">{{ a.source }} · {{ timeAgo(a.received_at) }}</span>
              </span>
              <span class="text-xs font-semibold tabular-nums" :class="STATUS_META[a.status].text">{{ Math.round(a.score) }}</span>
            </button>
          </li>
        </ul>
      </section>
    </div>

    <div class="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
      <!-- Top brands -->
      <section class="card p-5">
        <h2 class="font-semibold">Marques usurpées</h2>
        <p class="mb-3 text-xs text-slate-500">14 derniers jours</p>
        <p v-if="!data?.top_brands.length" class="text-sm text-slate-400">Aucune usurpation détectée.</p>
        <ul class="space-y-2">
          <li v-for="b in data?.top_brands ?? []" :key="b.brand">
            <div class="flex justify-between text-sm"><span class="truncate">{{ b.brand }}</span><b class="tabular-nums">{{ b.count }}</b></div>
            <div class="mt-1 h-1.5 rounded-full bg-slate-100 dark:bg-slate-800"><div class="h-full rounded-full bg-slate-500" :style="{ width: (b.count / (data?.top_brands[0]?.count || 1)) * 100 + '%' }"></div></div>
          </li>
        </ul>
      </section>

      <!-- Top domains -->
      <section class="card p-5">
        <h2 class="font-semibold">Domaines malveillants</h2>
        <p class="mb-3 text-xs text-slate-500">Liens trouvés dans les messages dangereux ou suspects</p>
        <p v-if="!data?.top_domains.length" class="text-sm text-slate-400">Aucun domaine suspect.</p>
        <ul class="space-y-1.5">
          <li v-for="d in data?.top_domains ?? []" :key="d.domain" class="flex items-center justify-between gap-2 text-sm">
            <code class="truncate rounded bg-slate-100 px-1.5 py-0.5 text-xs dark:bg-slate-800">{{ d.domain }}</code><b class="tabular-nums">{{ d.count }}</b>
          </li>
        </ul>
      </section>

      <!-- Users control -->
      <section class="card p-5">
        <div class="mb-3 flex items-center justify-between">
          <h2 class="font-semibold">Activité des comptes</h2>
          <button class="text-xs text-blue-600 hover:underline dark:text-blue-400" @click="router.push('/admin/users')">Tous →</button>
        </div>
        <ul class="space-y-2.5">
          <li v-for="u in data?.users.recent ?? []" :key="u.id" class="flex items-center gap-2 text-sm">
            <span class="grid h-8 w-8 flex-shrink-0 place-items-center rounded-full bg-slate-100 text-xs font-bold dark:bg-slate-800">{{ (u.name || u.email).slice(0, 2).toUpperCase() }}</span>
            <span class="min-w-0 flex-1">
              <span class="block truncate">{{ u.name || u.email }} <span v-if="u.is_admin" class="text-[10px] text-blue-600">ADMIN</span></span>
              <span class="block text-[11px] text-slate-400">{{ u.last_login ? `connecté ${timeAgo(u.last_login)}` : `inscrit le ${formatDate(u.created_at)}` }}</span>
            </span>
            <button v-if="!u.is_admin" class="rounded-md px-2 py-1 text-[11px] font-medium"
                    :class="u.status === 'suspended' ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10' : 'bg-slate-100 text-slate-600 hover:bg-red-50 hover:text-red-600 dark:bg-slate-800'"
                    @click="toggleUser(u)">{{ u.status === 'suspended' ? 'Réactiver' : 'Suspendre' }}</button>
          </li>
        </ul>
      </section>

      <!-- Quick actions -->
      <section class="card p-5">
        <h2 class="mb-3 font-semibold">Actions rapides</h2>
        <div class="space-y-2">
          <button v-for="a in QUICK_ACTIONS" :key="a.to" class="flex w-full items-center gap-3 rounded-xl border border-slate-200 px-3 py-2.5 text-left text-sm transition hover:border-blue-300 hover:bg-blue-50/50 dark:border-slate-700 dark:hover:bg-slate-800"
                  @click="router.push(a.to)">
            <span>{{ a.icon }}</span><span class="flex-1">{{ a.label }}</span><span class="text-slate-400">→</span>
          </button>
          <a :href="adminOpsService.exportUrl" class="flex items-center gap-3 rounded-xl border border-slate-200 px-3 py-2.5 text-sm transition hover:border-blue-300 dark:border-slate-700">
            <span>📥</span><span class="flex-1">Exporter les données étiquetées (CSV)</span>
          </a>
        </div>
      </section>
    </div>

    <ReviewDrawer :analysis-id="selected" @close="selected = null" @decided="refresh" />
  </div>
</template>

<style scoped>
.card { border-radius: 1rem; border: 1px solid #e2e8f0; background: white; }
:global(.dark) .card { border-color: #1e293b; background: #0f172a; }
.chip { border-radius: 9999px; padding: 0.3rem 0.7rem; font-weight: 600; }
.chip.ok { background: rgba(16, 185, 129, 0.15); color: #6ee7b7; }
.chip.off { background: rgba(148, 163, 184, 0.15); color: #94a3b8; }
.scan {
  position: absolute; inset: 0; transform: translateX(-100%);
  background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.12), transparent);
  animation: scan 5s linear infinite;
}
.fresh { animation: fresh 2.5s ease-out; }
@keyframes scan { to { transform: translateX(100%); } }
@keyframes fresh { from { background: rgba(59, 130, 246, 0.18); } to { background: transparent; } }
@media (prefers-reduced-motion: reduce) { .scan, .fresh { animation: none; } }
</style>
