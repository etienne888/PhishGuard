<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import Analyzer from '@/components/Analyzer.vue'
import AnalysisDetailDrawer from '@/components/dashboard/AnalysisDetailDrawer.vue'
import HistoryPanel from '@/components/dashboard/HistoryPanel.vue'
import NotificationBell from '@/components/dashboard/NotificationBell.vue'
import NotificationList from '@/components/dashboard/NotificationList.vue'
import SettingsPanel from '@/components/dashboard/SettingsPanel.vue'
import ErrorState from '@/components/states/ErrorState.vue'
import LoadingState from '@/components/states/LoadingState.vue'
import { useAuthStore } from '@/stores/auth'
import { useUserDashboardStore } from '@/stores/userDashboard'
import { useUserNotificationsStore } from '@/stores/userNotifications'
import { userAccountService, type UserNotification, type UserProfile } from '@/services/userAccount.service'
import { STATUS_META, timeAgo } from '@/utils/risk'

type Tab = 'home' | 'analyze' | 'history' | 'notifications' | 'settings'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const dashboard = useUserDashboardStore()
const notifications = useUserNotificationsStore()

const TABS: Array<{ id: Tab; label: string; short: string; icon: string }> = [
  { id: 'home', label: 'Accueil', short: 'Accueil', icon: 'M3 11l9-8 9 8M5 10v10h14V10' },
  { id: 'analyze', label: 'Analyser un message', short: 'Analyser', icon: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-4.3-4.3' },
  { id: 'history', label: 'Mes analyses', short: 'Historique', icon: 'M12 8v4l3 2M3.05 11a9 9 0 1 1 .5 4M3 4v5h5' },
  { id: 'notifications', label: 'Notifications', short: 'Alertes', icon: 'M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0' },
  { id: 'settings', label: 'Paramètres', short: 'Profil', icon: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z' },
]

const tab = ref<Tab>(TABS.some((t) => t.id === route.query.tab) ? (route.query.tab as Tab) : 'home')
watch(tab, (next) => router.replace({ query: { ...route.query, tab: next === 'home' ? undefined : next } }))

const profile = ref<UserProfile | null>(null)
const selectedAnalysis = ref<number | null>(null)
const history = ref<InstanceType<typeof HistoryPanel> | null>(null)

const firstName = computed(() => {
  const name = profile.value?.full_name || auth.user?.displayName
  return name ? name.split(' ')[0] : (auth.user?.email ?? '').split('@')[0]
})
const initials = computed(() => (profile.value?.full_name || auth.user?.email || '?').slice(0, 2).toUpperCase())

const stats = computed(() => ({
  analyzed: dashboard.overview?.emails_analyzed_today ?? 0,
  dangerous: dashboard.overview?.threats_today ?? 0,
  suspicious: dashboard.overview?.suspicious_today ?? 0,
  safe: dashboard.overview?.safe_today ?? 0,
}))
const vigilance = computed(() => Math.round(dashboard.score ?? dashboard.overview?.vigilance_score ?? 100))
const vigilanceTone = computed(() => vigilance.value >= 70 ? '#10b981' : vigilance.value >= 40 ? '#f59e0b' : '#ef4444')
const recent = computed(() => dashboard.messages.slice(0, 5))

const TIPS = [
  'Aucun agent MTN ou Orange ne vous demandera jamais votre code PIN.',
  'Un lien raccourci (bit.ly…) cache la vraie adresse : méfiez-vous.',
  'Les concours officiels ne se paient jamais par Mobile Money à un numéro personnel.',
  "L'urgence (« dans les 24h ») est la première arme des arnaqueurs.",
  'Un proche qui vous écrit depuis un nouveau numéro ? Appelez-le sur l’ancien.',
]
const tip = TIPS[new Date().getDate() % TIPS.length]

async function refreshAll() {
  await Promise.all([dashboard.load('today', true), notifications.load()])
  history.value?.reload()
}

function openNotification(n: UserNotification) {
  if (n.analysis_id) selectedAnalysis.value = n.analysis_id
  else if (n.id === 'tip-mfa') tab.value = 'settings'
}

onMounted(async () => {
  void dashboard.load('today')
  void notifications.load()
  try { profile.value = await userAccountService.getProfile() } catch { /* shown by apiFetch */ }
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 pb-20 lg:pb-0">
    <Navbar />

    <!-- Sidebar (desktop) -->
    <aside class="fixed bottom-0 left-0 top-0 z-30 hidden w-64 border-r border-slate-200 bg-white pt-24 lg:block">
      <nav class="space-y-1 px-3">
        <button v-for="t in TABS" :key="t.id" class="relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition"
                :class="tab === t.id ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100'" @click="tab = t.id">
          <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="t.icon" /></svg>
          <span class="flex-1 text-left">{{ t.label }}</span>
          <span v-if="t.id === 'notifications' && notifications.unreadCount" class="rounded-full bg-red-500 px-2 py-0.5 text-[10px] font-bold text-white">{{ notifications.unreadCount }}</span>
        </button>
      </nav>
      <div class="absolute bottom-0 left-0 right-0 m-3 rounded-xl bg-slate-900 p-4 text-xs text-slate-300">
        <p class="font-semibold text-white">Victime d'une arnaque ?</p>
        <p class="mt-1">CIRT-CM : numéro vert <b class="text-white">8202</b><br />alerts@cirt.cm</p>
      </div>
    </aside>

    <main class="px-4 pt-24 lg:pl-72 lg:pr-8">
      <div class="mx-auto max-w-5xl">
        <!-- Header -->
        <header class="mb-6 flex items-center gap-3">
          <img v-if="profile?.avatar_url" :src="profile.avatar_url" alt="" class="h-12 w-12 rounded-full object-cover ring-2 ring-white shadow" />
          <div v-else class="grid h-12 w-12 place-items-center rounded-full bg-gradient-to-br from-blue-600 to-cyan-500 font-bold text-white shadow">{{ initials }}</div>
          <div class="min-w-0 flex-1">
            <p class="text-xs text-slate-500">Mon espace sécurité</p>
            <h1 class="truncate text-xl font-bold text-slate-800">Bonjour {{ firstName }} 👋</h1>
          </div>
          <NotificationBell @open="openNotification" @see-all="tab = 'notifications'" />
          <button class="hidden rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-md shadow-blue-600/20 transition hover:bg-blue-700 sm:block" @click="tab = 'analyze'">
            + Analyser un message
          </button>
        </header>

        <!-- HOME -->
        <template v-if="tab === 'home'">
          <LoadingState v-if="dashboard.isLoading && !dashboard.overview" message="Chargement de votre espace…" :rows="3" />
          <ErrorState v-else-if="dashboard.error" :message="dashboard.error" hint="Vérifiez que le serveur est démarré, puis réessayez." :on-retry="() => dashboard.load('today', true)" />
          <div v-else class="space-y-5">
            <!-- Hero -->
            <section class="relative overflow-hidden rounded-2xl bg-slate-900 p-6 text-white">
              <div class="scanline" aria-hidden="true"></div>
              <div class="relative flex flex-col gap-6 sm:flex-row sm:items-center">
                <div class="gauge" :style="{ '--value': vigilance, '--tone': vigilanceTone }" role="img" :aria-label="`Score de vigilance ${vigilance} sur 100`">
                  <div class="gauge-inner"><span class="text-3xl font-bold tabular-nums">{{ vigilance }}</span><span class="text-[10px] text-slate-400">/ 100</span></div>
                </div>
                <div class="flex-1">
                  <p class="text-xs font-semibold uppercase tracking-wide text-cyan-300">Score de vigilance</p>
                  <h2 class="mt-1 text-lg font-bold">
                    {{ vigilance >= 70 ? 'Vos messages récents semblent sûrs.' : vigilance >= 40 ? 'Soyez prudent : des messages suspects ont été reçus.' : 'Attention : plusieurs messages dangereux récemment.' }}
                  </h2>
                  <p class="mt-1 text-sm text-slate-400">Calculé à partir du risque de vos dernières analyses. Plus il est haut, mieux c'est.</p>
                  <button class="mt-4 rounded-xl bg-cyan-400 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-cyan-300" @click="tab = 'analyze'">
                    🔍 Vérifier un message suspect
                  </button>
                </div>
              </div>
            </section>

            <!-- KPIs (today) -->
            <section class="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div class="kpi"><span class="kpi-label">Analysés aujourd'hui</span><span class="kpi-value">{{ stats.analyzed }}</span></div>
              <div class="kpi"><span class="kpi-label text-red-600">🔴 Dangereux</span><span class="kpi-value">{{ stats.dangerous }}</span></div>
              <div class="kpi"><span class="kpi-label text-amber-600">🟠 Suspects</span><span class="kpi-value">{{ stats.suspicious }}</span></div>
              <div class="kpi"><span class="kpi-label text-emerald-600">🟢 Sans danger</span><span class="kpi-value">{{ stats.safe }}</span></div>
            </section>

            <div class="grid gap-5 lg:grid-cols-5">
              <!-- Recent analyses -->
              <section class="rounded-2xl border border-slate-200 bg-white lg:col-span-3">
                <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
                  <h3 class="font-semibold text-slate-800">Dernières analyses</h3>
                  <button class="text-xs text-blue-600 hover:underline" @click="tab = 'history'">Tout voir →</button>
                </div>
                <div v-if="!recent.length" class="p-8 text-center">
                  <p class="text-3xl">📨</p>
                  <p class="mt-2 text-sm text-slate-600">Vous n'avez encore analysé aucun message.</p>
                  <button class="mt-3 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white" @click="tab = 'analyze'">Collez votre premier message suspect</button>
                </div>
                <ul v-else class="divide-y divide-slate-100">
                  <li v-for="m in recent" :key="m.id">
                    <button class="flex w-full items-center gap-3 px-4 py-3 text-left hover:bg-slate-50" @click="selectedAnalysis = m.id">
                      <span class="h-2.5 w-2.5 flex-shrink-0 rounded-full" :class="STATUS_META[m.status].dot"></span>
                      <span class="min-w-0 flex-1">
                        <span class="block truncate text-sm text-slate-800">{{ m.preview }}</span>
                        <span class="text-xs text-slate-400">{{ timeAgo(m.received_at) }}</span>
                      </span>
                      <span class="rounded-full border px-2.5 py-0.5 text-xs" :class="STATUS_META[m.status].chip">{{ STATUS_META[m.status].label }}</span>
                    </button>
                  </li>
                </ul>
              </section>

              <!-- Side column -->
              <div class="space-y-5 lg:col-span-2">
                <section class="rounded-2xl border border-blue-100 bg-blue-50 p-4">
                  <p class="text-xs font-semibold uppercase tracking-wide text-blue-700">💡 Conseil du jour</p>
                  <p class="mt-1.5 text-sm text-blue-900">{{ tip }}</p>
                </section>
                <section class="rounded-2xl border border-slate-200 bg-white p-4">
                  <p class="font-semibold text-slate-800">J'ai déjà cliqué ou donné mon code…</p>
                  <ol class="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-600">
                    <li>Changez tout de suite votre code PIN / mot de passe.</li>
                    <li>Appelez le service client officiel (agence, ou numéro au dos de votre carte).</li>
                    <li>Gardez des captures d'écran du message.</li>
                    <li>Signalez au CIRT-CM : <b>8202</b> · alerts@cirt.cm</li>
                  </ol>
                </section>
                <section v-if="!auth.user?.mfa_active" class="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                  <p class="text-sm font-semibold text-amber-800">🔒 Protégez votre compte</p>
                  <p class="mt-1 text-sm text-amber-700">Activez la double authentification (code OTP).</p>
                  <button class="mt-2 text-sm font-semibold text-amber-800 underline" @click="tab = 'settings'">Activer maintenant</button>
                </section>
              </div>
            </div>
          </div>
        </template>

        <!-- ANALYZE -->
        <section v-else-if="tab === 'analyze'" class="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 class="text-lg font-bold text-slate-800">Analyser un message</h2>
          <p class="mb-4 text-sm text-slate-500">Collez un SMS, un e-mail ou un message WhatsApp, ou importez un fichier .eml. Le résultat est enregistré dans votre historique.</p>
          <Analyzer embedded @analyzed="refreshAll" />
        </section>

        <!-- HISTORY -->
        <section v-else-if="tab === 'history'">
          <h2 class="mb-3 text-lg font-bold text-slate-800">Mes analyses</h2>
          <HistoryPanel ref="history" @open="(id) => (selectedAnalysis = id)" @analyze="tab = 'analyze'" />
        </section>

        <!-- NOTIFICATIONS -->
        <section v-else-if="tab === 'notifications'" class="rounded-2xl border border-slate-200 bg-white">
          <div class="flex items-center justify-between border-b border-slate-100 px-4 py-3">
            <h2 class="text-lg font-bold text-slate-800">Notifications</h2>
            <button v-if="notifications.unreadCount" class="text-xs text-blue-600 hover:underline" @click="notifications.markAllRead()">Tout marquer comme lu</button>
          </div>
          <NotificationList @open="openNotification" />
        </section>

        <!-- SETTINGS -->
        <section v-else>
          <h2 class="mb-3 text-lg font-bold text-slate-800">Paramètres</h2>
          <SettingsPanel @profile-changed="(p) => (profile = p)" />
        </section>
      </div>
    </main>

    <!-- Bottom tab bar (mobile) -->
    <nav class="fixed bottom-0 left-0 right-0 z-30 grid grid-cols-5 border-t border-slate-200 bg-white lg:hidden" aria-label="Navigation du tableau de bord">
      <button v-for="t in TABS" :key="t.id" class="relative flex flex-col items-center gap-0.5 py-2 text-[11px] font-medium"
              :class="tab === t.id ? 'text-blue-600' : 'text-slate-500'" @click="tab = t.id">
        <svg viewBox="0 0 24 24" class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path :d="t.icon" /></svg>
        {{ t.short }}
        <span v-if="t.id === 'notifications' && notifications.unreadCount" class="absolute right-1/4 top-1 h-2 w-2 rounded-full bg-red-500"></span>
      </button>
    </nav>

    <AnalysisDetailDrawer :analysis-id="selectedAnalysis" @close="selectedAnalysis = null" />
  </div>
</template>

<style scoped>
.kpi { display: flex; flex-direction: column; gap: 0.25rem; padding: 1rem; border-radius: 1rem; background: white; border: 1px solid #e2e8f0; }
.kpi-label { font-size: 0.75rem; font-weight: 600; color: #64748b; }
.kpi-value { font-size: 1.75rem; font-weight: 700; color: #1e293b; font-variant-numeric: tabular-nums; }

.gauge {
  --value: 0;
  --tone: #10b981;
  flex-shrink: 0;
  width: 120px;
  height: 120px;
  border-radius: 9999px;
  display: grid;
  place-items: center;
  background: conic-gradient(var(--tone) calc(var(--value) * 1%), #1e293b 0);
  transition: background 0.6s ease;
}
.gauge-inner {
  width: 96px;
  height: 96px;
  border-radius: 9999px;
  background: #0f172a;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.scanline {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.12), transparent);
  transform: translateX(-100%);
  animation: sweep 4s linear infinite;
}
@keyframes sweep { to { transform: translateX(100%); } }
@media (prefers-reduced-motion: reduce) { .scanline { animation: none; } }
</style>
