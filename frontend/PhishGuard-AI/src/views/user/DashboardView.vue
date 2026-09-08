<script setup lang="ts">
import { ref, computed } from 'vue';
import Navbar from "@/components/Navbar.vue";
import DashboardStats from "@/components/DashboardStats.vue";

// ============ STATE ============
const loading = ref(false);
const activeTab = ref('messages');

// ============ MESSAGES DATA ============
const messages = ref([
  {
    id: 1,
    sender: 'banque@cameroun.net',
    subject: 'Vérification de compte urgente',
    received: '2024-01-15 14:32',
    status: 'suspicious',
    score: 85,
    preview: 'Cliquez sur ce lien pour vérifier votre compte bancaire...'
  },
  {
    id: 2,
    sender: 'service@orange.cm',
    subject: 'Offre spéciale de fin d\'année',
    received: '2024-01-14 10:15',
    status: 'safe',
    score: 12,
    preview: 'Profitez de 50% de réduction sur vos recharges...'
  },
  {
    id: 3,
    sender: 'cnps@cameroun.com',
    subject: 'Mise à jour de votre dossier CNPS',
    received: '2024-01-13 09:45',
    status: 'phishing',
    score: 94,
    preview: 'Votre dossier CNPS nécessite une mise à jour immédiate...'
  }
]);

// ============ THREAT STATISTICS ============
const threatStats = computed(() => ({
  total: messages.value.length,
  phishing: messages.value.filter(m => m.status === 'phishing').length,
  suspicious: messages.value.filter(m => m.status === 'suspicious').length,
  safe: messages.value.filter(m => m.status === 'safe').length,
  avgScore: Math.round(messages.value.reduce((acc, m) => acc + m.score, 0) / messages.value.length)
}));

// ============ RECENT ACTIVITY ============
const activities = ref([
  {
    id: 1,
    action: 'Message suspect détecté',
    details: 'Banque Internationale du Cameroun (BIC)',
    time: 'Il y a 5 min',
    type: 'threat'
  },
  {
    id: 2,
    action: 'Signalement envoyé aux autorités',
    details: 'Campagne de phishing contre Orange Cameroun',
    time: 'Il y a 2 heures',
    type: 'report'
  },
  {
    id: 3,
    action: 'Analyse terminée',
    details: '15 messages analysés aujourd\'hui',
    time: 'Il y a 4 heures',
    type: 'analysis'
  }
]);

// ============ ACTIONS ============
const analyzeMessage = () => {
  loading.value = true;
  setTimeout(() => {
    loading.value = false;
    alert('🔄 Analyse en cours... (Intégration avec l\'API à venir)');
  }, 1500);
};

const reportThreat = (messageId: number) => {
  if (confirm('Voulez-vous signaler ce message aux autorités ?')) {
    alert('✅ Signalement envoyé aux autorités compétentes.');
  }
};

const checkSecurity = () => {
  alert('🔐 Vérification de la sécurité de votre compte...\n- Mot de passe: Fort ✅\n- 2FA: Activé ✅\n- Sessions actives: 1');
};

const getStatusColor = (status: string) => {
  const colors = {
    phishing: 'text-red-600 bg-red-50 border-red-200',
    suspicious: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    safe: 'text-green-600 bg-green-50 border-green-200'
  };
  return colors[status as keyof typeof colors] || 'text-gray-600 bg-gray-50 border-gray-200';
};

const getStatusIcon = (status: string) => {
  const icons = {
    phishing: '🚨',
    suspicious: '⚠️',
    safe: '✅'
  };
  return icons[status as keyof typeof icons] || 'ℹ️';
};

const getScoreColor = (score: number) => {
  if (score >= 80) return 'text-red-600';
  if (score >= 50) return 'text-yellow-600';
  return 'text-green-600';
};

// ============ STATS FOR DASHBOARD ============
const stats = computed(() => [
  { 
    label: "Messages analysés", 
    value: threatStats.value.total.toString(), 
    tone: "text-blue-600" 
  },
  { 
    label: "Menaces détectées", 
    value: threatStats.value.phishing.toString(), 
    tone: "text-red-600" 
  },
  { 
    label: "Signalements envoyés", 
    value: activities.value.filter(a => a.type === 'report').length.toString(), 
    tone: "text-emerald-600" 
  },
  { 
    label: "Score de vigilance", 
    value: `${100 - threatStats.value.avgScore}%`, 
    tone: "text-purple-600" 
  }
]);
</script>

<template>
  <Navbar />
  
  <main class="pt-28 pb-16 px-4 min-h-screen bg-gradient-to-br from-slate-50 to-blue-50/50">
    <div class="max-w-7xl mx-auto">
      
      <!-- ========== HEADER ========== -->
      <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 class="text-3xl font-bold text-slate-800 font-display flex items-center gap-3">
            🛡️ Tableau de bord
          </h1>
          <p class="text-slate-500 mt-1">
            Protégez-vous contre le phishing au Cameroun
          </p>
        </div>
        <div class="flex items-center gap-3 flex-wrap">
          <button 
            @click="checkSecurity"
            class="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 transition shadow-lg shadow-blue-200"
          >
            🔐 Sécurité du compte
          </button>
          <button 
            @click="analyzeMessage"
            :disabled="loading"
            class="flex items-center gap-2 px-4 py-2 rounded-lg border border-slate-200 bg-white text-slate-700 hover:border-blue-300 hover:text-blue-600 transition disabled:opacity-50"
          >
            <span :class="{ 'animate-spin': loading }">🔄</span>
            Analyser
          </button>
        </div>
      </div>

      <!-- ========== STATS ========== -->
      <div class="mt-8">
        <DashboardStats :stats="stats" />
      </div>

      <!-- ========== SECURITY QUICK ACTIONS ========== -->
      <div class="mt-6 grid grid-cols-2 md:grid-cols-4 gap-3">
        <button 
          v-for="action in [
            { icon: '🔍', label: 'Analyser un message', color: 'bg-blue-50 text-blue-700' },
            { icon: '🚨', label: 'Signaler une menace', color: 'bg-red-50 text-red-700' },
            { icon: '📊', label: 'Rapport mensuel', color: 'bg-purple-50 text-purple-700' },
            { icon: '👥', label: 'Sensibilisation', color: 'bg-green-50 text-green-700' }
          ]"
          :key="action.label"
          class="p-4 rounded-xl border border-slate-100 hover:shadow-md transition text-center"
          :class="action.color"
        >
          <div class="text-2xl">{{ action.icon }}</div>
          <div class="text-sm font-semibold mt-1">{{ action.label }}</div>
        </button>
      </div>

      <!-- ========== TABS ========== -->
      <div class="mt-8 border-b border-slate-200">
        <div class="flex gap-6 overflow-x-auto">
          <button
            v-for="tab in [
              { id: 'messages', label: 'Messages', icon: '📧' },
              { id: 'threats', label: 'Menaces', icon: '🚨' },
              { id: 'reports', label: 'Signalements', icon: '📄' },
              { id: 'settings', label: 'Paramètres', icon: '👤' }
            ]"
            :key="tab.id"
            @click="activeTab = tab.id"
            class="flex items-center gap-2 pb-3 px-1 font-medium transition border-b-2"
            :class="activeTab === tab.id 
              ? 'border-blue-600 text-blue-600' 
              : 'border-transparent text-slate-500 hover:text-slate-700'"
          >
            <span>{{ tab.icon }}</span>
            {{ tab.label }}
            <span 
              v-if="tab.id === 'messages'" 
              class="ml-1 px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-600"
            >
              {{ messages.length }}
            </span>
          </button>
        </div>
      </div>

      <!-- ========== CONTENT ========== -->
      <div class="mt-6">
        
        <!-- ===== TAB: MESSAGES ===== -->
        <div v-if="activeTab === 'messages'">
          <div class="bg-white rounded-xl border border-slate-100 shadow-card overflow-hidden">
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead class="bg-slate-50 border-b border-slate-100">
                  <tr>
                    <th class="text-left px-6 py-3 font-semibold text-slate-600">Expéditeur</th>
                    <th class="text-left px-6 py-3 font-semibold text-slate-600">Sujet</th>
                    <th class="text-left px-6 py-3 font-semibold text-slate-600">Score</th>
                    <th class="text-left px-6 py-3 font-semibold text-slate-600">Statut</th>
                    <th class="text-left px-6 py-3 font-semibold text-slate-600">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr 
                    v-for="message in messages" 
                    :key="message.id"
                    class="border-b border-slate-50 hover:bg-slate-50/50 transition"
                  >
                    <td class="px-6 py-3 font-medium text-slate-700">
                      {{ message.sender }}
                    </td>
                    <td class="px-6 py-3 text-slate-600 max-w-xs truncate">
                      {{ message.subject }}
                    </td>
                    <td class="px-6 py-3">
                      <span class="font-bold" :class="getScoreColor(message.score)">
                        {{ message.score }}%
                      </span>
                    </td>
                    <td class="px-6 py-3">
                      <span 
                        class="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold border"
                        :class="getStatusColor(message.status)"
                      >
                        {{ getStatusIcon(message.status) }}
                        {{ message.status }}
                      </span>
                    </td>
                    <td class="px-6 py-3">
                      <div class="flex items-center gap-2">
                        <button 
                          @click="reportThreat(message.id)"
                          class="text-red-500 hover:text-red-700 text-xs font-semibold"
                          v-if="message.status !== 'safe'"
                        >
                          Signaler
                        </button>
                        <button 
                          class="text-blue-500 hover:text-blue-700 text-xs font-semibold"
                        >
                          Détails
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="messages.length === 0" class="p-8 text-center text-slate-500">
              <span class="text-4xl block mb-3">📧</span>
              Aucun message analysé pour le moment
            </div>
          </div>
        </div>

        <!-- ===== TAB: THREATS ===== -->
        <div v-if="activeTab === 'threats'">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="bg-white rounded-xl border border-slate-100 shadow-card p-6">
              <div class="flex items-center justify-between mb-4">
                <h3 class="font-semibold text-slate-700">Menaces actives</h3>
                <span class="text-xs font-medium text-red-600 bg-red-50 px-2 py-1 rounded-full">
                  {{ threatStats.phishing }} détectées
                </span>
              </div>
              <div class="space-y-3">
                <div 
                  v-for="msg in messages.filter(m => m.status === 'phishing')" 
                  :key="msg.id"
                  class="flex items-start gap-3 p-3 bg-red-50 rounded-lg border border-red-100"
                >
                  <span class="text-xl flex-shrink-0 mt-0.5">🚨</span>
                  <div>
                    <p class="font-medium text-sm text-slate-700">{{ msg.subject }}</p>
                    <p class="text-xs text-slate-500">{{ msg.sender }}</p>
                  </div>
                  <span class="ml-auto text-xs font-bold text-red-600">{{ msg.score }}%</span>
                </div>
                <p v-if="threatStats.phishing === 0" class="text-center text-slate-500 py-4">
                  ✅ Aucune menace active détectée
                </p>
              </div>
            </div>
            
            <div class="bg-white rounded-xl border border-slate-100 shadow-card p-6">
              <h3 class="font-semibold text-slate-700 mb-4">Statistiques</h3>
              <div class="space-y-3">
                <div class="flex justify-between items-center">
                  <span class="text-sm text-slate-600">Messages analysés</span>
                  <span class="font-bold text-slate-700">{{ threatStats.total }}</span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-slate-600">Taux de phishing</span>
                  <span class="font-bold text-red-600">
                    {{ threatStats.total > 0 ? Math.round(threatStats.phishing / threatStats.total * 100) : 0 }}%
                  </span>
                </div>
                <div class="flex justify-between items-center">
                  <span class="text-sm text-slate-600">Niveau de vigilance</span>
                  <span class="font-bold text-purple-600">{{ 100 - threatStats.avgScore }}%</span>
                </div>
                <div class="w-full bg-slate-200 rounded-full h-2 mt-2">
                  <div 
                    class="bg-red-500 h-2 rounded-full transition-all"
                    :style="{ width: `${threatStats.total > 0 ? Math.round(threatStats.phishing / threatStats.total * 100) : 0}%` }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== TAB: REPORTS ===== -->
        <div v-if="activeTab === 'reports'">
          <div class="bg-white rounded-xl border border-slate-100 shadow-card p-6">
            <div class="flex items-center justify-between mb-6">
              <h3 class="font-semibold text-slate-700">Historique des signalements</h3>
              <button class="text-sm text-blue-600 hover:text-blue-800 font-semibold">
                Voir tout
              </button>
            </div>
            <div v-if="activities.filter(a => a.type === 'report').length > 0" class="space-y-4">
              <div 
                v-for="activity in activities.filter(a => a.type === 'report')" 
                :key="activity.id"
                class="flex items-start gap-4 p-4 bg-emerald-50 rounded-lg border border-emerald-100"
              >
                <span class="text-xl flex-shrink-0 mt-0.5">✅</span>
                <div>
                  <p class="font-medium text-sm text-slate-700">{{ activity.action }}</p>
                  <p class="text-sm text-slate-500">{{ activity.details }}</p>
                  <p class="text-xs text-slate-400 mt-1">{{ activity.time }}</p>
                </div>
              </div>
            </div>
            <div v-else class="text-center py-8 text-slate-500">
              <span class="text-4xl block mb-3">📄</span>
              Aucun signalement envoyé
            </div>
          </div>
        </div>

        <!-- ===== TAB: SETTINGS ===== -->
        <div v-if="activeTab === 'settings'">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white rounded-xl border border-slate-100 shadow-card p-6">
              <h3 class="font-semibold text-slate-700 mb-4 flex items-center gap-2">
                🔐 Sécurité
              </h3>
              <div class="space-y-4">
                <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <span class="text-sm text-slate-600">Authentification à 2 facteurs</span>
                  <span class="px-2 py-1 bg-green-100 text-green-700 text-xs font-semibold rounded-full">Activée</span>
                </div>
                <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <span class="text-sm text-slate-600">Dernière connexion</span>
                  <span class="text-sm text-slate-700">Hier, 18:32</span>
                </div>
                <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <span class="text-sm text-slate-600">Appareils actifs</span>
                  <span class="text-sm text-slate-700">2</span>
                </div>
                <button class="w-full mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                  Changer le mot de passe
                </button>
              </div>
            </div>

            <div class="bg-white rounded-xl border border-slate-100 shadow-card p-6">
              <h3 class="font-semibold text-slate-700 mb-4 flex items-center gap-2">
                ℹ️ À propos
              </h3>
              <div class="space-y-4 text-sm text-slate-600">
                <p>🔒 Protéger les Camerounais contre les attaques de phishing</p>
                <p>📊 Analyse en temps réel des messages suspects</p>
                <p>🚨 Signalement automatique aux autorités compétentes</p>
                <p>🌍 Soutenu par le Ministère des Postes et Télécommunications</p>
                <div class="pt-4 border-t border-slate-100">
                  <p class="text-xs text-slate-400">Version 2.0.1 • Dernière mise à jour: 15/01/2024</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ========== RECENT ACTIVITY (Bottom) ========== -->
      <div class="mt-8 bg-white rounded-xl border border-slate-100 shadow-card p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-semibold text-slate-700 flex items-center gap-2">
            🕐 Activité récente
          </h3>
          <span class="text-xs text-slate-400">Dernières 24h</span>
        </div>
        <div class="space-y-3">
          <div 
            v-for="activity in activities" 
            :key="activity.id"
            class="flex items-center gap-4 p-3 hover:bg-slate-50 rounded-lg transition"
          >
            <div 
              class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 text-xl"
              :class="{
                'bg-red-100': activity.type === 'threat',
                'bg-emerald-100': activity.type === 'report',
                'bg-blue-100': activity.type === 'analysis'
              }"
            >
              <span v-if="activity.type === 'threat'">🚨</span>
              <span v-else-if="activity.type === 'report'">✅</span>
              <span v-else>📊</span>
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium text-slate-700">{{ activity.action }}</p>
              <p class="text-xs text-slate-500">{{ activity.details }}</p>
            </div>
            <span class="text-xs text-slate-400 whitespace-nowrap">{{ activity.time }}</span>
            <span class="text-slate-300">›</span>
          </div>
        </div>
      </div>

      <!-- ========== SECURITY TIPS (Footer) ========== -->
      <div class="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-100">
        <div class="flex items-center gap-3">
          <span class="text-2xl">💡</span>
          <div>
            <p class="text-sm font-semibold text-slate-700">Conseil de sécurité</p>
            <p class="text-xs text-slate-600">
              Ne cliquez jamais sur les liens dans les e-mails suspects. Vérifiez toujours l'expéditeur avant de partager des informations personnelles.
            </p>
          </div>
        </div>
      </div>
    </div>
  </main>
</template>