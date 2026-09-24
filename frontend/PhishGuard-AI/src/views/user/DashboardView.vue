<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import Navbar from "@/components/Navbar.vue";
import DashboardStats from "@/components/DashboardStats.vue";
import Analyzer from '@/components/Analyzer.vue';
import EmptyState from '@/components/states/EmptyState.vue';
import ErrorState from '@/components/states/ErrorState.vue';
import LoadingState from '@/components/states/LoadingState.vue';
import { useI18n } from '@/i18n';
import { useNotificationsStore } from '@/stores/notifications';
import { useUserDashboardStore } from '@/stores/userDashboard';

/* ============================================================
   STATE & CORE DATA (unchanged logic)
   ============================================================ */
const activeTab = ref('overview');
const { t } = useI18n();
const notifications = useNotificationsStore();
const dashboardStore = useUserDashboardStore();
const loading = computed(() => dashboardStore.isLoading);
const messages = computed(() => dashboardStore.messages);
const activities = computed(() => dashboardStore.activities);
const timeline = computed(() => dashboardStore.timeline);

const sidebarOpen = ref(false);
const toggleSidebar = () => (sidebarOpen.value = !sidebarOpen.value);
const closeSidebar = () => (sidebarOpen.value = false);

const threatStats = computed(() => ({
  total: dashboardStore.overview?.emails_analyzed_today ?? 0,
  phishing: dashboardStore.overview?.threats_today ?? 0,
  suspicious: dashboardStore.overview?.suspicious_today ?? 0,
  safe: dashboardStore.overview?.safe_today ?? 0,
  avgScore: 100 - (dashboardStore.overview?.vigilance_score ?? 0)
}));

/* ---- Today's email security strip ---- */
const todayEmailSecurity = computed(() => {
  const total = threatStats.value.total;
  const safe = threatStats.value.safe;
  const suspicious = threatStats.value.suspicious;
  const threats = threatStats.value.phishing;
  const quarantined = threats;
  return { total, safe, suspicious, threats, quarantined };
});

interface AiExplanation {
  subject: string
  sender: string
  riskScore: number
  confidence: number
  severity: string
  indicators: Array<{ label: string; weight: number }>
}

const aiExplanation = ref<AiExplanation | null>(null);

const formatDateTime = (value: string | null) => value
  ? new Intl.DateTimeFormat('fr-FR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
  : '—';

/* ---- Actions ---- */
const showAnalyzer = ref(false);
const analyzeMessage = () => {
  activeTab.value = 'overview';
  showAnalyzer.value = !showAnalyzer.value;
};
// The analysis is saved under the logged-in user; reload stats so it shows up at once
const onAnalyzed = () => dashboardStore.load(selectedPeriod.value, true);

const reportThreat = async (messageId: number) => {
  if (confirm('Voulez-vous signaler ce message aux autorités ?')) {
    try {
      await dashboardStore.reportMessage(messageId);
      notifications.push('Signalement envoyé aux autorités compétentes.', 'success');
    } catch {
      notifications.push('Le signalement a échoué.', 'error');
    }
  }
};

const checkSecurity = async () => {
  try {
    const result = await dashboardStore.checkSecurity();
    notifications.push(result.account_locked ? 'Le compte est verrouillé.' : 'Vérification de sécurité terminée.', result.account_locked ? 'error' : 'success');
  } catch {
    notifications.push('La vérification de sécurité a échoué.', 'error');
  }
};

/* ---- Helpers ---- */
const statusMeta = (status: string) => {
  const map: Record<string, { cls: string; dot: string; label: string }> = {
    phishing: { cls: 'text-red-700 bg-red-50 border-red-200', dot: '#ef4444', label: 'Phishing' },
    suspicious: { cls: 'text-amber-700 bg-amber-50 border-amber-200', dot: '#f59e0b', label: 'Suspect' },
    safe: { cls: 'text-emerald-700 bg-emerald-50 border-emerald-200', dot: '#10b981', label: 'Sûr' },
  };
  return map[status] || { cls: 'text-slate-600 bg-slate-50 border-slate-200', dot: '#64748b', label: status };
};

const getScoreColor = (score: number) => {
  if (score >= 80) return 'text-red-600';
  if (score >= 50) return 'text-amber-600';
  return 'text-emerald-600';
};

const vigilanceScore = computed(() => dashboardStore.score ?? dashboardStore.overview?.vigilance_score ?? 0);

const stats = computed(() => [
  { label: "Messages analysés", value: threatStats.value.total.toString(), tone: "text-blue-600", icon: 'orders' as const, progress: 100 },
  { label: "Menaces détectées", value: threatStats.value.phishing.toString(), tone: "text-rose-600", icon: 'alert' as const, progress: threatStats.value.total ? Math.round((threatStats.value.phishing / threatStats.value.total) * 100) : 0, pulse: threatStats.value.phishing > 0 },
  { label: "Signalements envoyés", value: activities.value.filter(a => a.type === 'report').length.toString(), tone: "text-emerald-600", icon: 'shield' as const, progress: threatStats.value.total ? Math.round((activities.value.filter(a => a.type === 'report').length / threatStats.value.total) * 100) : 0 },
  { label: "Score de vigilance", value: `${vigilanceScore.value}%`, tone: "text-purple-600", icon: 'growth' as const, progress: vigilanceScore.value }
]);

const tabs = [
  { id: 'overview', label: 'Vue d\'ensemble', icon: 'grid' },
  { id: 'messages', label: 'Messages', icon: 'mail' },
  { id: 'threats', label: 'Menaces', icon: 'alert' },
  { id: 'reports', label: 'Signalements', icon: 'file' },
  { id: 'settings', label: 'Paramètres', icon: 'user' },
];

const quickActions = [
  { icon: 'scan', label: 'Analyser un message', action: analyzeMessage },
  { icon: 'flag', label: 'Signaler une menace', action: () => { activeTab.value = 'threats'; closeSidebar(); } },
  { icon: 'file', label: 'Rapport mensuel', action: () => { activeTab.value = 'reports'; closeSidebar(); } },
  { icon: 'users', label: 'Sensibilisation', action: () => {} },
];

const initials = (email?: string) =>
  (email ?? '').split('@')[0]?.slice(0, 2).toUpperCase() || 'NA';

/* ==================== UPGRADES ==================== */

const scoreReasons = computed(() => dashboardStore.scoreReasons);

const quarantineBreakdown = computed(() => {
  const flagged = messages.value.filter(m => m.status !== 'safe');
  return {
    total: flagged.length,
    critical: flagged.filter(m => m.score >= 90).length,
    high: flagged.filter(m => m.score >= 70 && m.score < 90).length,
    medium: flagged.filter(m => m.score < 70).length,
  };
});

const threatTypeLabel = (status: string) => {
  const map: Record<string, string> = {
    phishing: 'Hameçonnage d\u2019identifiants',
    suspicious: 'Domaine suspect',
    safe: 'Aucune menace',
  };
  return map[status] || 'Autre';
};

const explainMode = ref<'simple' | 'technical'>('simple');

const periods = [
  { id: 'today', label: "Aujourd'hui" },
  { id: '7d', label: '7 jours' },
  { id: '30d', label: '30 jours' },
  { id: '90d', label: '90 jours' },
];
const selectedPeriod = ref('today');

/* ==================== OVERVIEW / SUMMARY DATA ==================== */

const platformProcesses = computed(() => [
  {
    id: 'ingest',
    icon: 'inbox',
    title: 'Collecte des messages',
    description: 'Réception et normalisation des e-mails entrants depuis les passerelles de messagerie.',
    status: 'active',
    metric: `${threatStats.value.total} messages`,
    tone: 'cyan',
  },
  {
    id: 'analyze',
    icon: 'cpu',
    title: 'Analyse IA multi-signaux',
    description: 'Détection d\'URL suspectes, usurpation de domaine, langage d\'urgence et pièces jointes.',
    status: 'active',
    metric: `${Math.round(threatStats.value.avgScore)} / 100 risque moyen`,
    tone: 'violet',
  },
  {
    id: 'score',
    icon: 'gauge',
    title: 'Scoring & classification',
    description: 'Attribution d\'un score de risque et catégorisation (sûr, suspect, phishing).',
    status: 'active',
    metric: `${threatStats.value.total} classifiés`,
    tone: 'amber',
  },
  {
    id: 'quarantine',
    icon: 'shield',
    title: 'Quarantaine & blocage',
    description: 'Isolation automatique des menaces critiques avant livraison à l\'utilisateur.',
    status: 'active',
    metric: `${dashboardStore.overview?.quarantined_today ?? 0} bloqué(s)`,
    tone: 'red',
  },
  {
    id: 'report',
    icon: 'flag',
    title: 'Signalement & sensibilisation',
    description: 'Transmission aux autorités compétentes et campagnes de sensibilisation ciblées.',
    status: 'active',
    metric: `${activities.value.filter((activity) => activity.type === 'report').length} signalement(s)`,
    tone: 'emerald',
  },
]);

const platformSummary = computed(() => ({
  totalProcessed: threatStats.value.total,
  threatsNeutralized: threatStats.value.phishing,
  vigilance: vigilanceScore.value,
  lastSync: dashboardStore.overview?.last_sync_at ? new Intl.DateTimeFormat('fr-FR', { hour: '2-digit', minute: '2-digit' }).format(new Date(dashboardStore.overview.last_sync_at)) : 'Aucune analyse',
}));

const pipelineHealth = computed(() => [
  { label: 'Analyses aujourd’hui', value: String(threatStats.value.total), tone: 'emerald' },
  { label: 'Menaces détectées', value: String(threatStats.value.phishing), tone: threatStats.value.phishing ? 'amber' : 'emerald' },
  { label: 'Signalements envoyés', value: String(activities.value.filter((activity) => activity.type === 'report').length), tone: 'emerald' },
  { label: 'Quarantaines', value: String(dashboardStore.overview?.quarantined_today ?? 0), tone: 'emerald' },
]);

/* ==================== SIDEBAR NAV ==================== */
const navItems = computed(() => [
  { id: 'overview', label: "Vue d'ensemble", icon: 'grid', badge: null },
  { id: 'messages', label: 'Messages', icon: 'mail', badge: dashboardStore.messagesTotal },
  { id: 'threats', label: 'Menaces', icon: 'alert', badge: threatStats.value.phishing },
  { id: 'reports', label: 'Signalements', icon: 'file', badge: null },
  { id: 'settings', label: 'Paramètres', icon: 'user', badge: null },
]);

const selectTab = (id: string) => {
  activeTab.value = id;
  closeSidebar();
};

watch(selectedPeriod, (range) => {
  void dashboardStore.changeRange(range);
});

onMounted(() => {
  void dashboardStore.load(selectedPeriod.value);
});
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <Navbar />

    <!-- ============================================================
         SIDEBAR (fixed, responsive drawer on mobile)
         ============================================================ -->
    <aside
      class="fixed top-0 bottom-0 left-0 z-40 w-72 bg-white border-r border-slate-200 shadow-sm transition-transform duration-300 ease-out
             lg:translate-x-0 pt-24 lg:pt-24"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
    >
      <!-- Brand -->
      <div class="px-5 pb-4 border-b border-slate-100">
        <div class="flex items-center gap-3">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[#0D47A1] to-[#1e5bbf] text-white font-bold text-sm">
            PG
          </div>
          <div>
            <div class="font-bold text-slate-900 leading-tight">PhishGuard</div>
            <div class="text-[10px] uppercase tracking-wider text-slate-400">AI Security</div>
          </div>
        </div>
      </div>

      <!-- Nav -->
      <nav class="px-3 py-4 space-y-1 overflow-y-auto" style="max-height: calc(100vh - 16rem);">
        <button
          v-for="item in navItems"
          :key="item.id"
          @click="selectTab(item.id)"
          class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition relative"
          :class="activeTab === item.id
            ? 'bg-indigo-50 text-[#0D47A1] font-semibold'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'"
        >
          <span
            v-if="activeTab === item.id"
            class="absolute -left-3 top-1/2 -translate-y-1/2 h-6 w-1 rounded-r-full bg-[#0D47A1]"
          />
          <svg v-if="item.icon === 'grid'" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
          <svg v-else-if="item.icon === 'mail'" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 7l10 6 10-6"/></svg>
          <svg v-else-if="item.icon === 'alert'" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4M12 17h.01"/></svg>
          <svg v-else-if="item.icon === 'file'" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/></svg>
          <svg v-else viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="4"/><path d="M4 21v-1a8 8 0 0 1 16 0v1"/></svg>
          <span class="flex-1 text-left">{{ item.label }}</span>
          <span v-if="item.badge" class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 text-slate-600">{{ item.badge }}</span>
        </button>
      </nav>

      <!-- Footer -->
      <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-100 bg-white">
        <div class="text-[11px] text-slate-400">Version 2.0.1 · © 2025</div>
      </div>
    </aside>

    <!-- Mobile overlay -->
    <div
      v-if="sidebarOpen"
      @click="closeSidebar"
      class="fixed inset-0 z-30 bg-slate-900/30 backdrop-blur-sm lg:hidden"
    />

    <!-- ============================================================
         MAIN CONTENT
         ============================================================ -->
    <main class="lg:pl-72 pt-24 pb-16 px-4 transition-all">
      <div class="max-w-7xl mx-auto">

        <!-- Mobile menu toggle -->
        <button
          @click="toggleSidebar"
          class="lg:hidden mb-4 flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-slate-200 text-sm font-medium text-slate-700 shadow-sm"
        >
          <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 12h18M3 6h18M3 18h18"/></svg>
          Menu
        </button>

        <!-- ===================== OVERVIEW (LANDING / SUMMARY) ===================== -->
        <LoadingState v-if="loading && !dashboardStore.overview" message="Chargement du tableau de bord..." :rows="4" />
        <ErrorState
          v-else-if="dashboardStore.error"
          :message="dashboardStore.error"
          hint="Réessayez ou contactez le support avec l’identifiant de la requête."
          :on-retry="() => dashboardStore.load(selectedPeriod, true)"
        />
        <div v-else-if="activeTab === 'overview'" class="space-y-6">

          <!-- Protection hero (unchanged logic) -->
          <div class="relative overflow-hidden rounded-2xl bg-slate-900 text-white p-6 md:p-8">
            <div class="pointer-events-none absolute inset-0 motion-safe:animate-[scan-sweep_4s_linear_infinite] bg-gradient-to-r from-transparent via-cyan-400/10 to-transparent -translate-x-full" />
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
                    Protection active
                    <span class="text-slate-500">•</span>
                    <span class="text-slate-400">{{ platformSummary.lastSync }}</span>
                  </div>
                  <h1 class="mt-1 text-2xl md:text-3xl font-bold tracking-tight">Synthèse de la plateforme</h1>
                  <p class="text-slate-400 text-sm mt-0.5">Analyse et résumé des processus de protection anti-phishing</p>
                </div>
              </div>

              <div class="flex items-center gap-6">
                <div class="text-right">
                  <div class="text-3xl font-bold tabular-nums text-cyan-300">{{ vigilanceScore }}%</div>
                  <div class="text-xs text-slate-400">Score de vigilance</div>
                </div>
                <div class="h-10 w-px bg-slate-700 hidden sm:block" />
                <div class="flex items-center gap-3">
                  <button @click="checkSecurity" class="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-cyan-500 text-slate-900 font-semibold hover:bg-cyan-400 transition">
                    <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                    {{ t('user.dashboard.checkSecurity') }}
                  </button>
                  <button @click="analyzeMessage" :disabled="loading" class="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-slate-700 text-slate-200 hover:border-cyan-400 hover:text-cyan-300 transition disabled:opacity-50">
                    <svg :class="['h-4 w-4', { 'motion-safe:animate-spin': loading }]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>
                    Analyser
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- ===== IN-DASHBOARD ANALYZER (v2 pipeline) ===== -->
          <div v-if="showAnalyzer" class="rounded-2xl bg-white border border-slate-200 p-5">
            <div class="flex items-center justify-between mb-3">
              <h2 class="text-lg font-bold text-slate-800">Analyser un message</h2>
              <button class="text-sm text-slate-400 hover:text-slate-600" @click="showAnalyzer = false">Fermer ✕</button>
            </div>
            <Analyzer embedded @analyzed="onAnalyzed" />
          </div>

          <!-- ===== PLATFORM SUMMARY KPIs ===== -->
          <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <div class="rounded-xl bg-white border border-slate-200 p-5">
              <div class="text-xs uppercase tracking-wide text-slate-400 font-semibold">Messages traités</div>
              <div class="mt-1 text-3xl font-bold text-slate-800 tabular-nums">{{ platformSummary.totalProcessed }}</div>
              <div class="text-xs text-slate-500 mt-0.5">Cycle complet</div>
            </div>
            <div class="rounded-xl bg-white border border-slate-200 p-5">
              <div class="text-xs uppercase tracking-wide text-emerald-600 font-semibold flex items-center gap-1.5">
                <span class="h-1.5 w-1.5 rounded-full bg-emerald-500" /> Menaces neutralisées
              </div>
              <div class="mt-1 text-3xl font-bold text-slate-800 tabular-nums">{{ platformSummary.threatsNeutralized }}</div>
              <div class="text-xs text-slate-500 mt-0.5">Bloquées en quarantaine</div>
            </div>
            <div class="rounded-xl bg-white border border-slate-200 p-5">
              <div class="text-xs uppercase tracking-wide text-purple-600 font-semibold">Score de vigilance</div>
              <div class="mt-1 text-3xl font-bold text-slate-800 tabular-nums">{{ platformSummary.vigilance }}%</div>
              <div class="text-xs text-slate-500 mt-0.5">Posture actuelle</div>
            </div>
            <div class="rounded-xl bg-white border border-slate-200 p-5">
              <div class="text-xs uppercase tracking-wide text-slate-400 font-semibold">Dernière synchro</div>
              <div class="mt-1 text-3xl font-bold text-slate-800">{{ platformSummary.lastSync }}</div>
              <div class="text-xs text-slate-500 mt-0.5">Temps quasi réel</div>
            </div>
          </div>

          <!-- ===== PLATFORM PROCESSES (analysis & summary of pipeline) ===== -->
          <div class="rounded-2xl bg-white border border-slate-200 p-6">
            <div class="flex items-center justify-between mb-5">
              <div>
                <h2 class="font-semibold text-slate-800 text-base">Processus de la plateforme</h2>
                <p class="text-xs text-slate-500 mt-0.5">Vue synthétique du pipeline d'analyse et de protection</p>
              </div>
              <span class="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
                <span class="relative flex h-2 w-2">
                  <span class="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                Pipeline opérationnel
              </span>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-3">
              <div
                v-for="(process, idx) in platformProcesses"
                :key="process.id"
                class="relative rounded-xl border border-slate-200 bg-slate-50/40 p-4 hover:bg-white hover:shadow-sm transition"
              >
                <!-- Step number -->
                <div class="flex items-start justify-between mb-3">
                  <span class="flex h-9 w-9 items-center justify-center rounded-lg bg-white border border-slate-200 shadow-sm">
                    <svg v-if="process.icon === 'inbox'" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="#0891b2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>
                    <svg v-else-if="process.icon === 'cpu'" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="#7c3aed" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M1 9h3M1 15h3M20 9h3M20 15h3"/></svg>
                    <svg v-else-if="process.icon === 'gauge'" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 14l4-4"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L12 12"/></svg>
                    <svg v-else-if="process.icon === 'shield'" viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M9 12l2 2 4-4"/></svg>
                    <svg v-else viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="#059669" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><path d="M4 22V15"/></svg>
                  </span>
                  <span class="text-[10px] font-mono font-bold text-slate-300">0{{ idx + 1 }}</span>
                </div>

                <h3 class="text-sm font-semibold text-slate-800 leading-snug">{{ process.title }}</h3>
                <p class="text-xs text-slate-500 mt-1 leading-relaxed">{{ process.description }}</p>

                <div class="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
                  <span class="text-[11px] text-slate-400">Statut</span>
                  <span class="inline-flex items-center gap-1 text-[11px] font-semibold" :class="{
                    'text-cyan-700': process.tone === 'cyan',
                    'text-violet-700': process.tone === 'violet',
                    'text-amber-700': process.tone === 'amber',
                    'text-red-700': process.tone === 'red',
                    'text-emerald-700': process.tone === 'emerald',
                  }">
                    <span class="h-1.5 w-1.5 rounded-full" :class="{
                      'bg-cyan-500': process.tone === 'cyan',
                      'bg-violet-500': process.tone === 'violet',
                      'bg-amber-500': process.tone === 'amber',
                      'bg-red-500': process.tone === 'red',
                      'bg-emerald-500': process.tone === 'emerald',
                    }" />
                    {{ process.status === 'active' ? 'Actif' : process.status }}
                  </span>
                </div>
                <div class="mt-1.5 text-[11px] font-semibold text-slate-700 tabular-nums">{{ process.metric }}</div>
              </div>
            </div>
          </div>

          <!-- ===== PIPELINE HEALTH + ACTIVITY ===== -->
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <!-- Pipeline health -->
            <div class="lg:col-span-1 rounded-2xl bg-white border border-slate-200 p-6">
              <h3 class="font-semibold text-slate-700 text-sm mb-4">Santé du pipeline</h3>
              <ul class="space-y-3">
                <li v-for="h in pipelineHealth" :key="h.label" class="flex items-center justify-between text-sm">
                  <span class="text-slate-600">{{ h.label }}</span>
                  <span class="font-semibold tabular-nums" :class="h.tone === 'emerald' ? 'text-emerald-600' : 'text-amber-600'">{{ h.value }}</span>
                </li>
              </ul>
            </div>

            <!-- Today's email security strip (kept) -->
            <div class="lg:col-span-2 rounded-2xl bg-white border border-slate-200 p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-semibold text-slate-700 text-sm">Sécurité des e-mails</h3>
                <div class="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
                  <button
                    v-for="p in periods" :key="p.id"
                    @click="selectedPeriod = p.id"
                    class="px-2.5 py-1 rounded-md text-xs font-medium transition"
                    :class="selectedPeriod === p.id ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                  >
                    {{ p.label }}
                  </button>
                </div>
              </div>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div class="rounded-xl bg-slate-50 border border-slate-200 p-4">
                  <div class="text-xs uppercase tracking-wide text-slate-400 font-semibold">Analysés</div>
                  <div class="mt-1 text-2xl font-bold text-slate-800 tabular-nums">{{ todayEmailSecurity.total }}</div>
                </div>
                <div class="rounded-xl bg-emerald-50 border border-emerald-100 p-4">
                  <div class="text-xs uppercase tracking-wide text-emerald-600 font-semibold">Sûrs</div>
                  <div class="mt-1 text-2xl font-bold text-emerald-700 tabular-nums">{{ todayEmailSecurity.safe }}</div>
                </div>
                <div class="rounded-xl bg-amber-50 border border-amber-100 p-4">
                  <div class="text-xs uppercase tracking-wide text-amber-600 font-semibold">Suspects</div>
                  <div class="mt-1 text-2xl font-bold text-amber-700 tabular-nums">{{ todayEmailSecurity.suspicious }}</div>
                </div>
                <div class="rounded-xl bg-red-50 border border-red-100 p-4 relative overflow-hidden">
                  <div class="absolute inset-x-0 top-0 h-0.5 bg-red-500" />
                  <div class="text-xs uppercase tracking-wide text-red-600 font-semibold">Menaces</div>
                  <div class="mt-1 text-2xl font-bold text-red-600 tabular-nums">{{ todayEmailSecurity.threats }}</div>
                </div>
              </div>
            </div>
          </div>

          <!-- ===== AI EXPLANATION + TIMELINE (kept for overview) ===== -->
          <div class="grid grid-cols-1 lg:grid-cols-5 gap-4">
            <!-- AI explanation card -->
            <div v-if="aiExplanation" class="lg:col-span-3 bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between gap-3">
                <div class="flex items-center gap-2 min-w-0">
                  <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900 text-cyan-400 flex-shrink-0">
                    <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a3 3 0 0 0-3 3v1a3 3 0 0 0-3 3v1a3 3 0 0 0 0 6v1a3 3 0 0 0 3 3v1a3 3 0 0 0 6 0v-1a3 3 0 0 0 3-3v-1a3 3 0 0 0 0-6v-1a3 3 0 0 0-3-3V5a3 3 0 0 0-3-3z"/></svg>
                  </span>
                  <div class="min-w-0">
                    <h3 class="text-sm font-semibold text-slate-800">Analyse IA — Explication</h3>
                    <p class="text-xs text-slate-500 truncate max-w-md">{{ aiExplanation.subject }} — {{ aiExplanation.sender }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-2 flex-shrink-0">
                  <div class="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
                    <button @click="explainMode = 'simple'" class="px-2 py-1 rounded-md text-[11px] font-medium transition" :class="explainMode === 'simple' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500'">Simple</button>
                    <button @click="explainMode = 'technical'" class="px-2 py-1 rounded-md text-[11px] font-medium transition" :class="explainMode === 'technical' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500'">Technique</button>
                  </div>
                  <span class="text-[11px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full border"
                    :class="aiExplanation.severity === 'CRITIQUE' ? 'text-red-700 bg-red-50 border-red-200' : 'text-amber-700 bg-amber-50 border-amber-200'">
                    {{ aiExplanation.severity }}
                  </span>
                </div>
              </div>
              <div class="p-6">
                <div class="grid grid-cols-3 gap-3 mb-5">
                  <div class="rounded-lg bg-red-50 border border-red-100 p-3">
                    <div class="text-[11px] uppercase tracking-wide text-red-600 font-semibold">Risque</div>
                    <div class="text-xl font-bold text-red-600 tabular-nums">{{ aiExplanation.riskScore }}<span class="text-sm text-red-400">/100</span></div>
                  </div>
                  <div class="rounded-lg bg-slate-50 border border-slate-200 p-3">
                    <div class="text-[11px] uppercase tracking-wide text-slate-500 font-semibold">Confiance</div>
                    <div class="text-xl font-bold text-slate-700 tabular-nums">{{ aiExplanation.confidence }}%</div>
                  </div>
                  <div class="rounded-lg bg-slate-900 border border-slate-800 p-3">
                    <div class="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">Action</div>
                    <div class="text-xl font-bold text-cyan-300">BLOQUÉ</div>
                  </div>
                </div>
                <p v-if="explainMode === 'simple'" class="text-sm text-slate-600 leading-relaxed">
                  PhishGuard-AI a détecté plusieurs signes couramment associés au phishing dans ce message : un lien suspect, une tentative d'usurpation d'identité et un ton urgent typique des arnaques. Par précaution, le message a été bloqué avant d'atteindre votre boîte de réception.
                </p>
                <div v-else class="space-y-2">
                  <div v-for="ind in aiExplanation.indicators" :key="ind.label" class="flex items-center gap-3">
                    <span class="w-56 text-xs text-slate-600 truncate">{{ ind.label }}</span>
                    <div class="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                      <div class="h-full rounded-full bg-gradient-to-r from-amber-400 to-red-500" :style="{ width: `${(ind.weight / 30) * 100}%` }" />
                    </div>
                    <span class="w-10 text-right text-xs font-semibold text-slate-700 tabular-nums">+{{ ind.weight }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Threat timeline -->
            <div class="lg:col-span-2 bg-white rounded-xl border border-slate-200 p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-semibold text-slate-700 flex items-center gap-2 text-sm">
                  <svg viewBox="0 0 24 24" class="h-4 w-4 text-cyan-600" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                  Chronologie des menaces
                </h3>
                <span class="text-[11px] text-slate-400">Aujourd'hui</span>
              </div>
              <ol class="relative space-y-4 pl-4 before:absolute before:left-[3px] before:top-1 before:bottom-1 before:w-px before:bg-slate-200">
                <li v-for="event in timeline" :key="event.id" class="relative group">
                  <span class="absolute -left-4 top-1.5 h-2 w-2 rounded-full ring-4 ring-white" :style="{ backgroundColor: event.tone === 'critical' ? '#ef4444' : '#f59e0b' }" />
                  <div class="flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <div class="flex items-center gap-2">
                        <span class="text-xs font-mono text-slate-400 tabular-nums">{{ event.time }}</span>
                        <span class="text-xs font-semibold uppercase tracking-wide" :class="event.tone === 'critical' ? 'text-red-600' : 'text-amber-600'">Risque {{ event.risk }}</span>
                      </div>
                      <p class="text-sm text-slate-700 truncate">{{ event.title }}</p>
                      <p class="text-xs text-slate-500">Action : {{ event.action }}</p>
                    </div>
                  </div>
                </li>
                <li v-if="timeline.length === 0">
                  <EmptyState message="Aucune menace pour cette période." />
                </li>
              </ol>
            </div>
          </div>

          <!-- ===== ACTIVITY LOG (terminal) ===== -->
          <div class="bg-slate-900 rounded-xl p-6 text-slate-200">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold flex items-center gap-2 text-sm text-slate-300">
                <svg viewBox="0 0 24 24" class="h-4 w-4" fill="none" stroke="#22d3ee" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>
                Journal d'activité
              </h3>
              <div class="flex items-center gap-2 text-xs text-slate-500">
                <span class="relative flex h-1.5 w-1.5">
                  <span class="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-400" />
                </span>
                Temps réel • Dernières 24h
              </div>
            </div>
            <div class="relative space-y-4 pl-4 before:absolute before:left-[3px] before:top-1 before:bottom-1 before:w-px before:bg-slate-700">
              <div v-for="activity in activities" :key="activity.id" class="relative flex items-start gap-3">
                <span class="absolute -left-4 top-1.5 h-2 w-2 rounded-full ring-4 ring-slate-900" :style="{ backgroundColor: activity.type === 'threat' ? '#ef4444' : activity.type === 'report' ? '#10b981' : '#22d3ee' }" />
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-slate-100">{{ activity.action }}</p>
                  <p class="text-xs text-slate-400">{{ activity.details }}</p>
                </div>
                <span class="text-xs text-slate-500 font-mono tabular-nums whitespace-nowrap">{{ formatDateTime(activity.occurred_at) }}</span>
              </div>
              <EmptyState v-if="activities.length === 0" message="Aucune activité récente." />
            </div>
          </div>

          <!-- Tip -->
          <div class="p-4 bg-white rounded-xl border border-slate-200 flex items-start gap-3">
            <svg viewBox="0 0 24 24" class="h-5 w-5 mt-0.5 flex-shrink-0" fill="none" stroke="#8b5cf6" stroke-width="2"><path d="M9 18h6M10 22h4M12 2a6 6 0 0 0-4 10.47c.51.47.8 1.13.8 1.83V15h6.4v-.7c0-.7.29-1.36.8-1.83A6 6 0 0 0 12 2z"/></svg>
            <div>
              <p class="text-sm font-semibold text-slate-700">Conseil de sécurité</p>
              <p class="text-xs text-slate-600 mt-0.5">Ne cliquez jamais sur les liens dans les e-mails suspects. Vérifiez toujours l'expéditeur avant de partager des informations personnelles.</p>
            </div>
          </div>
        </div>

        <!-- ===================== MESSAGES TAB ===================== -->
        <div v-else-if="activeTab === 'messages'" class="space-y-4">
          <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <!-- Protection + Score + Quarantine (reused from overview summary) -->
            <div class="bg-white rounded-xl border border-slate-200 p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-semibold text-slate-700 text-sm">Protection</h3>
                <span class="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700">
                  <span class="h-1.5 w-1.5 rounded-full bg-[#00C853]" /> Protégé
                </span>
              </div>
              <ul class="space-y-2.5 text-sm">
                <li class="flex items-center justify-between"><span class="text-slate-600">Analyse des e-mails</span><span class="text-xs font-semibold text-emerald-600">Active</span></li>
                <li class="flex items-center justify-between"><span class="text-slate-600">Protection des URL</span><span class="text-xs font-semibold text-emerald-600">Active</span></li>
                <li class="flex items-center justify-between"><span class="text-slate-600">Protection des pièces jointes</span><span class="text-xs font-semibold text-emerald-600">Active</span></li>
                <li class="flex items-center justify-between"><span class="text-slate-600">Détection en temps réel</span><span class="text-xs font-semibold text-emerald-600">Active</span></li>
                <li class="flex items-center justify-between"><span class="text-slate-600">Renseignement sur les menaces</span><span class="text-xs font-semibold text-emerald-600">Active</span></li>
              </ul>
            </div>

            <div class="bg-white rounded-xl border border-slate-200 p-6 flex flex-col items-center text-center">
              <h3 class="font-semibold text-slate-700 text-sm self-start mb-2">Score de sécurité</h3>
              <div class="relative h-32 w-32 my-1">
                <svg viewBox="0 0 120 120" class="h-32 w-32 -rotate-90">
                  <circle cx="60" cy="60" r="52" fill="none" stroke="#f1f5f9" stroke-width="10" />
                  <circle cx="60" cy="60" r="52" fill="none" stroke="#0D47A1" stroke-width="10" stroke-linecap="round"
                    :stroke-dasharray="2 * Math.PI * 52"
                    :stroke-dashoffset="2 * Math.PI * 52 * (1 - vigilanceScore / 100)"
                    class="transition-all duration-700" />
                </svg>
                <div class="absolute inset-0 flex flex-col items-center justify-center">
                  <span class="text-2xl font-bold text-slate-800 tabular-nums">{{ vigilanceScore }}</span>
                  <span class="text-[11px] text-slate-400">/100</span>
                </div>
              </div>
              <p class="text-xs text-slate-500 mb-3">
                {{ vigilanceScore >= 80 ? 'Bonne posture de sécurité' : vigilanceScore >= 50 ? 'Posture correcte, restez vigilant' : 'Posture à améliorer' }}
              </p>
              <ul v-if="scoreReasons.length" class="w-full space-y-1.5 text-left">
                <li v-for="(reason, i) in scoreReasons" :key="i" class="flex items-center justify-between text-xs gap-2">
                  <span class="text-slate-600 truncate">{{ reason.label }}</span>
                  <span class="font-semibold tabular-nums flex-shrink-0" :class="reason.delta >= 0 ? 'text-emerald-600' : 'text-red-600'">
                    {{ reason.delta >= 0 ? '+' : '' }}{{ reason.delta }}
                  </span>
                </li>
              </ul>
            </div>

            <div class="bg-white rounded-xl border border-slate-200 p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-semibold text-slate-700 text-sm">Quarantaine</h3>
                <span class="text-xs font-semibold text-slate-500">{{ quarantineBreakdown.total }} élément(s)</span>
              </div>
              <div v-if="quarantineBreakdown.total > 0" class="space-y-2.5 text-sm">
                <div class="flex items-center justify-between"><span class="text-slate-600">Critique</span><span class="font-semibold text-red-600 tabular-nums">{{ quarantineBreakdown.critical }}</span></div>
                <div class="flex items-center justify-between"><span class="text-slate-600">Élevé</span><span class="font-semibold text-amber-600 tabular-nums">{{ quarantineBreakdown.high }}</span></div>
                <div class="flex items-center justify-between"><span class="text-slate-600">Moyen</span><span class="font-semibold text-slate-500 tabular-nums">{{ quarantineBreakdown.medium }}</span></div>
              </div>
              <div v-else class="text-center py-6">
                <p class="text-sm font-medium text-slate-600">Quarantaine vide</p>
                <p class="text-xs text-slate-400 mt-1">Aucun message dangereux n'est actuellement isolé.</p>
              </div>
            </div>
          </div>

          <DashboardStats :stats="stats" />

          <div class="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead class="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th class="text-left px-6 py-3 font-medium text-slate-500">Expéditeur</th>
                    <th class="text-left px-6 py-3 font-medium text-slate-500">Sujet</th>
                    <th class="text-left px-6 py-3 font-medium text-slate-500">Type</th>
                    <th class="text-left px-6 py-3 font-medium text-slate-500">Score</th>
                    <th class="text-left px-6 py-3 font-medium text-slate-500">Statut</th>
                    <th class="text-left px-6 py-3 font-medium text-slate-500">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="message in messages" :key="message.id" class="border-b border-slate-100 last:border-0 hover:bg-slate-50/60 transition">
                    <td class="px-6 py-3">
                      <div class="flex items-center gap-3">
                        <span class="flex h-8 w-8 items-center justify-center rounded-full text-[11px] font-bold"
                          :class="message.status === 'phishing' ? 'bg-red-100 text-red-700' : message.status === 'suspicious' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'">
                          {{ initials(message.sender) }}
                        </span>
                        <div class="min-w-0">
                          <div class="font-medium text-slate-700 truncate">{{ message.sender }}</div>
                          <div class="text-[11px] text-slate-400">{{ formatDateTime(message.received_at) }}</div>
                        </div>
                      </div>
                    </td>
                    <td class="px-6 py-3 text-slate-600 max-w-xs">
                      <div class="truncate font-medium text-slate-700">{{ message.subject }}</div>
                      <div class="truncate text-xs text-slate-400">{{ message.preview }}</div>
                    </td>
                    <td class="px-6 py-3"><span class="text-xs text-slate-500">{{ threatTypeLabel(message.status) }}</span></td>
                    <td class="px-6 py-3">
                      <div class="flex items-center gap-2 w-28">
                        <div class="h-1.5 flex-1 rounded-full bg-slate-100 overflow-hidden">
                          <div class="h-full rounded-full" :class="getScoreColor(message.score).replace('text-', 'bg-')" :style="{ width: `${message.score}%` }" />
                        </div>
                        <span class="text-xs font-semibold tabular-nums" :class="getScoreColor(message.score)">{{ message.score }}%</span>
                      </div>
                    </td>
                    <td class="px-6 py-3">
                      <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border" :class="statusMeta(message.status).cls">
                        <span class="relative flex h-1.5 w-1.5">
                          <span v-if="message.status === 'phishing'" class="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full opacity-75" :style="{ backgroundColor: statusMeta(message.status).dot }" />
                          <span class="relative inline-flex h-1.5 w-1.5 rounded-full" :style="{ backgroundColor: statusMeta(message.status).dot }" />
                        </span>
                        {{ statusMeta(message.status).label }}
                      </span>
                    </td>
                    <td class="px-6 py-3">
                      <div class="flex items-center gap-3">
                        <button v-if="message.status !== 'safe'" @click="reportThreat(message.id)" class="text-red-600 hover:text-red-800 text-xs font-semibold">Signaler</button>
                        <button class="text-slate-500 hover:text-slate-800 text-xs font-semibold">Détails</button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="messages.length === 0">
                    <td colspan="6" class="px-6 py-6">
                      <EmptyState message="Aucun message analysé." hint="Analysez un message pour commencer." />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- ===================== THREATS TAB ===================== -->
        <div v-else-if="activeTab === 'threats'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="flex items-center justify-between mb-4">
              <h3 class="font-semibold text-slate-700">Menaces actives</h3>
              <span class="text-xs font-medium text-red-700 bg-red-50 border border-red-200 px-2 py-0.5 rounded-full">{{ threatStats.phishing }} détectées</span>
            </div>
            <div class="space-y-2">
              <div v-for="msg in messages.filter(m => m.status === 'phishing')" :key="msg.id" class="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-100">
                <span class="relative flex h-2 w-2 mt-1.5 flex-shrink-0">
                  <span class="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-red-500 opacity-60" />
                  <span class="relative inline-flex h-2 w-2 rounded-full bg-red-500" />
                </span>
                <div class="flex-1 min-w-0">
                  <p class="font-medium text-sm text-slate-700 truncate">{{ msg.subject }}</p>
                  <p class="text-xs text-slate-500">{{ msg.sender }} · {{ threatTypeLabel(msg.status) }}</p>
                </div>
                <span class="text-xs font-bold tabular-nums text-red-600">{{ msg.score }}%</span>
              </div>
              <p v-if="threatStats.phishing === 0" class="text-center text-slate-500 py-4 text-sm">Aucune menace active détectée</p>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <h3 class="font-semibold text-slate-700 mb-4">Statistiques</h3>
            <div class="space-y-3">
              <div class="flex justify-between items-center text-sm"><span class="text-slate-500">Messages analysés</span><span class="font-semibold text-slate-700 tabular-nums">{{ threatStats.total }}</span></div>
              <div class="flex justify-between items-center text-sm"><span class="text-slate-500">Taux de phishing</span><span class="font-semibold text-red-600 tabular-nums">{{ threatStats.total > 0 ? Math.round(threatStats.phishing / threatStats.total * 100) : 0 }}%</span></div>
              <div class="flex justify-between items-center text-sm"><span class="text-slate-500">Niveau de vigilance</span><span class="font-semibold text-purple-600 tabular-nums">{{ vigilanceScore }}%</span></div>
              <div class="w-full bg-slate-100 rounded-full h-1.5 mt-2">
                <div class="bg-red-500 h-1.5 rounded-full" :style="{ width: `${threatStats.total > 0 ? Math.round(threatStats.phishing / threatStats.total * 100) : 0}%` }" />
              </div>
            </div>
          </div>
        </div>

        <!-- ===================== REPORTS TAB ===================== -->
        <div v-else-if="activeTab === 'reports'" class="bg-white rounded-xl border border-slate-200 p-6">
          <div class="flex items-center justify-between mb-6">
            <h3 class="font-semibold text-slate-700">Historique des signalements</h3>
            <button class="text-sm text-cyan-700 hover:text-cyan-900 font-semibold">Voir tout</button>
          </div>
          <div v-if="activities.filter(a => a.type === 'report').length > 0" class="space-y-3">
            <div v-for="activity in activities.filter(a => a.type === 'report')" :key="activity.id" class="flex items-start gap-4 p-4 bg-emerald-50 rounded-lg border border-emerald-100">
              <svg viewBox="0 0 24 24" class="h-5 w-5 mt-0.5 flex-shrink-0" fill="none" stroke="#059669" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><path d="M22 4L12 14.01l-3-3" /></svg>
              <div>
                <p class="font-medium text-sm text-slate-700">{{ activity.action }}</p>
                <p class="text-sm text-slate-500">{{ activity.details }}</p>
                <p class="text-xs text-slate-400 mt-1">{{ formatDateTime(activity.occurred_at) }}</p>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-slate-400 text-sm">Aucun signalement envoyé</div>
        </div>

        <!-- ===================== SETTINGS TAB ===================== -->
        <div v-else-if="activeTab === 'settings'" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <h3 class="font-semibold text-slate-700 mb-4">Sécurité</h3>
            <div class="space-y-3">
              <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg text-sm">
                <span class="text-slate-600">Authentification à 2 facteurs</span>
                <span class="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs font-semibold rounded-full">Activée</span>
              </div>
              <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg text-sm">
                <span class="text-slate-600">Dernière connexion</span>
                <span class="text-slate-700">Hier, 18:32</span>
              </div>
              <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg text-sm">
                <span class="text-slate-600">Appareils actifs</span>
                <span class="text-slate-700">2</span>
              </div>
              <button class="w-full mt-2 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition text-sm font-medium">Changer le mot de passe</button>
            </div>
          </div>

          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <h3 class="font-semibold text-slate-700 mb-4">À propos</h3>
            <div class="space-y-3 text-sm text-slate-600">
              <p>Protéger les Camerounais contre les attaques de phishing.</p>
              <p>Analyse en temps réel des messages suspects.</p>
              <p>Signalement automatique aux autorités compétentes.</p>
              <p>Soutenu par le Ministère des Postes et Télécommunications.</p>
              <div class="pt-3 border-t border-slate-100 text-xs text-slate-400">Version 2.0.1 • Dernière mise à jour: 15/01/2024</div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@keyframes scan-sweep {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
@keyframes radar-pulse {
  0% { transform: scale(1); opacity: 0.5; }
  100% { transform: scale(1.8); opacity: 0; }
}
</style>