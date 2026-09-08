<script setup lang="ts">
import { onMounted, ref, computed, onUnmounted } from 'vue'
import { formatDate } from '@/utils'

// ============================================
// TYPES
// ============================================

interface ThreatIntelItem {
  id: number
  title: string
  summary: string
  category: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  date: string
  source: string
  url: string
  isReal: boolean
  sourceName: string
  country: string
}

interface SourceStatus {
  id: string
  name: string
  isOnline: boolean
  lastCheck: string | null
}

// ============================================
// SOURCES CONFIGURATION
// ============================================

const SOURCES = [
  { id: 'cirt', name: 'CIRT-CM', url: 'https://cirt.cm/feed/', icon: '🛡️', country: '🇨🇲 Cameroun' },
  { id: 'thn', name: 'The Hacker News', url: 'https://feeds.feedburner.com/TheHackersNews', icon: '📰', country: '🌍 International' },
  { id: 'bleeping', name: 'Bleeping Computer', url: 'https://www.bleepingcomputer.com/feed/', icon: '💻', country: '🌍 International' },
  { id: 'cisa', name: 'CISA (USA)', url: 'https://www.cisa.gov/cybersecurity-advisories/all.xml', icon: '🇺🇸', country: '🇺🇸 USA' },
  { id: 'digital', name: 'Digital Business Africa', url: 'https://digitalbusiness.africa/feed/', icon: '🌍', country: '🌍 Afrique' },
  { id: 'obs', name: 'Obs Cybersécurité', url: 'https://obs-cc.org/feed', icon: '👁️', country: '🇨🇲 Cameroun' },
]

// ============================================
// STATE
// ============================================

const items = ref<ThreatIntelItem[]>([])
const isLoading = ref(false)
const lastUpdated = ref<string | null>(null)
const sourceStatuses = ref<SourceStatus[]>([])
const error = ref<string | null>(null)
const isAutoRefresh = ref(true)
let refreshInterval: number | null = null

// ============================================
// COMPUTED
// ============================================

const onlineSources = computed(() => {
  return sourceStatuses.value.filter(s => s.isOnline).length
})

const totalSources = computed(() => SOURCES.length)

const categories = computed(() => {
  const cats = new Set<string>()
  items.value.forEach(item => cats.add(item.category))
  return Array.from(cats)
})

// ============================================
// FETCH FUNCTIONS
// ============================================

async function fetchWithProxy(url: string): Promise<string> {
  const proxies = [
    'https://api.allorigins.win/raw?url=',
    'https://corsproxy.io/?',
    'https://api.codetabs.com/v1/proxy?quest='
  ]

  for (const proxy of proxies) {
    try {
      const fullUrl = proxy + encodeURIComponent(url)
      const response = await fetch(fullUrl, {
        signal: AbortSignal.timeout(10000)
      })
      if (response.ok) {
        return await response.text()
      }
    } catch (e) {
      console.warn(`Proxy failed:`, e.message)
    }
  }
  throw new Error('Tous les proxies ont échoué')
}

function determineCategory(title: string, description: string): string {
  const text = (title + ' ' + description).toLowerCase()
  const categories = {
    'Phishing': ['phishing', 'hameçonnage', 'arnaque', 'fraude', 'scam'],
    'Mobile Money': ['mobile money', 'mtn', 'orange', 'momo', 'transfert'],
    'Ransomware': ['ransomware', 'rançongiciel', 'chiffrement'],
    'Malware': ['malware', 'virus', 'trojan', 'spyware', 'logiciel malveillant'],
    'Social Engineering': ['ingénierie sociale', 'manipulation', 'appel', 'urgence'],
    'Data Breach': ['fuite', 'breach', 'exfiltration', 'données'],
    'Vulnerability': ['vulnérabilité', 'zero-day', 'cve', 'fail'],
    'Cyber Attack': ['attaque', 'cyberattack', 'hack', 'compromis']
  }

  for (const [category, keywords] of Object.entries(categories)) {
    if (keywords.some(kw => text.includes(kw))) {
      return category
    }
  }
  return 'Actualité Cyber'
}

function determineSeverity(title: string, description: string): ThreatIntelItem['severity'] {
  const text = (title + ' ' + description).toLowerCase()
  if (text.includes('critical') || text.includes('zero-day') || text.includes('exploit') ||
      text.includes('active attack') || text.includes('emergency') || text.includes('urgent')) {
    return 'critical'
  }
  if (text.includes('warning') || text.includes('alert') || text.includes('vulnerability') ||
      text.includes('threat') || text.includes('danger') || text.includes('high risk')) {
    return 'high'
  }
  if (text.includes('update') || text.includes('patch') || text.includes('new') ||
      text.includes('discovered') || text.includes('found') || text.includes('report')) {
    return 'medium'
  }
  return 'low'
}

function formatDateFromRSS(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return new Date().toISOString()
    return date.toISOString()
  } catch {
    return new Date().toISOString()
  }
}

function getTimeAgo(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    if (isNaN(date.getTime())) return 'Date inconnue'
    const now = new Date()
    const diff = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diff < 60) return 'À l\'instant'
    if (diff < 3600) return `Il y a ${Math.floor(diff / 60)} min`
    if (diff < 86400) return `Il y a ${Math.floor(diff / 3600)}h`
    if (diff < 604800) return `Il y a ${Math.floor(diff / 86400)}j`
    return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
  } catch {
    return 'Date inconnue'
  }
}

function getSeverityBadge(severity: ThreatIntelItem['severity']): string {
  const badges = {
    critical: '🔴 Critique',
    high: '🟠 Élevée',
    medium: '🟡 Moyenne',
    low: '🔵 Faible'
  }
  return badges[severity] || '⚪ Inconnue'
}

function getSeverityColor(severity: ThreatIntelItem['severity']): string {
  const colors = {
    critical: 'bg-red-100 text-red-700 border-red-200',
    high: 'bg-orange-100 text-orange-700 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    low: 'bg-blue-100 text-blue-700 border-blue-200'
  }
  return colors[severity] || 'bg-slate-100 text-slate-700 border-slate-200'
}

// ============================================
// FETCH REAL ARTICLES
// ============================================

async function fetchRealArticles(): Promise<ThreatIntelItem[]> {
  const allArticles: ThreatIntelItem[] = []
  
  // Initialize source statuses
  sourceStatuses.value = SOURCES.map(s => ({
    id: s.id,
    name: s.name,
    isOnline: false,
    lastCheck: null
  }))

  for (const source of SOURCES) {
    try {
      const xmlText = await fetchWithProxy(source.url)
      
      if (!xmlText) {
        updateSourceStatus(source.id, false)
        continue
      }

      const parser = new DOMParser()
      const xml = parser.parseFromString(xmlText, 'text/xml')

      if (xml.querySelector('parsererror')) {
        updateSourceStatus(source.id, false)
        continue
      }

      const items = xml.querySelectorAll('item')
      let found = false

      if (items.length > 0) {
        items.forEach((item, index) => {
          if (index < 12) {
            const title = item.querySelector('title')?.textContent || ''
            const link = item.querySelector('link')?.textContent || ''
            const description = item.querySelector('description')?.textContent || ''
            const pubDate = item.querySelector('pubDate')?.textContent || ''

            if (title) {
              const cleanTitle = title.replace(/<[^>]+>/g, '').trim()
              const cleanDesc = description.replace(/<[^>]+>/g, '').trim()
              
              allArticles.push({
                id: Date.now() + index + Math.random() * 1000,
                title: cleanTitle || 'Sans titre',
                summary: cleanDesc.slice(0, 300) || 'Lire l\'article complet...',
                category: determineCategory(cleanTitle, cleanDesc),
                severity: determineSeverity(cleanTitle, cleanDesc),
                date: formatDateFromRSS(pubDate),
                source: source.id,
                url: link || '#',
                isReal: true,
                sourceName: source.name,
                country: source.country
              })
              found = true
            }
          }
        })
      } else {
        // Try Atom entries
        const entries = xml.querySelectorAll('entry')
        if (entries.length > 0) {
          entries.forEach((entry, index) => {
            if (index < 12) {
              const title = entry.querySelector('title')?.textContent || ''
              const link = entry.querySelector('link')?.getAttribute('href') || entry.querySelector('link')?.textContent || ''
              const summary = entry.querySelector('summary')?.textContent || entry.querySelector('description')?.textContent || ''
              const pubDate = entry.querySelector('published')?.textContent || entry.querySelector('pubDate')?.textContent || ''

              if (title) {
                const cleanTitle = title.replace(/<[^>]+>/g, '').trim()
                const cleanDesc = summary.replace(/<[^>]+>/g, '').trim()
                
                allArticles.push({
                  id: Date.now() + index + Math.random() * 1000,
                  title: cleanTitle || 'Sans titre',
                  summary: cleanDesc.slice(0, 300) || 'Lire l\'article complet...',
                  category: determineCategory(cleanTitle, cleanDesc),
                  severity: determineSeverity(cleanTitle, cleanDesc),
                  date: formatDateFromRSS(pubDate),
                  source: source.id,
                  url: link || '#',
                  isReal: true,
                  sourceName: source.name,
                  country: source.country
                })
                found = true
              }
            }
          })
        }
      }

      if (found) {
        updateSourceStatus(source.id, true)
      } else {
        updateSourceStatus(source.id, false)
      }

    } catch (error) {
      console.warn(`❌ Erreur pour ${source.name}:`, error)
      updateSourceStatus(source.id, false)
    }
  }

  // Sort by date (newest first)
  allArticles.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
  
  return allArticles
}

function updateSourceStatus(sourceId: string, isOnline: boolean) {
  const status = sourceStatuses.value.find(s => s.id === sourceId)
  if (status) {
    status.isOnline = isOnline
    status.lastCheck = new Date().toISOString()
  }
}

// ============================================
// GENERATE MOCK ARTICLES (FALLBACK)
// ============================================

function generateMockArticles(): ThreatIntelItem[] {
  const mockData = [
    { title: '🔴 Nouvelle campagne de phishing cible les utilisateurs de Mobile Money au Cameroun', source: 'cirt', category: 'Mobile Money', severity: 'critical' as const },
    { title: 'Microsoft alerte sur une faille zero-day exploitée activement', source: 'thn', category: 'Vulnerability', severity: 'high' as const },
    { title: 'Les cybercriminels utilisent l\'IA pour des attaques de phishing hyper-ciblées', source: 'bleeping', category: 'Phishing', severity: 'high' as const },
    { title: 'Orange Money : alerte sur une nouvelle arnaque au SIM swapping', source: 'digital', category: 'Mobile Money', severity: 'critical' as const },
    { title: 'CISA ajoute 5 nouvelles vulnérabilités à son catalogue des failles', source: 'cisa', category: 'Vulnerability', severity: 'medium' as const },
    { title: 'Le Cameroun renforce sa cybersécurité avec un nouveau SOC', source: 'obs', category: 'Cyber Attack', severity: 'low' as const },
    { title: 'INTERPOL lance une opération contre les botnets en Afrique', source: 'digital', category: 'Cyber Attack', severity: 'medium' as const },
    { title: 'Google renforce la protection Gmail contre le phishing', source: 'thn', category: 'Phishing', severity: 'low' as const },
    { title: 'Le Cameroun adopte une nouvelle loi sur la protection des données', source: 'cirt', category: 'Data Breach', severity: 'low' as const },
    { title: 'Les ransomwares : les PME camerounaises particulièrement vulnérables', source: 'obs', category: 'Ransomware', severity: 'high' as const },
  ]

  const sourceMap = Object.fromEntries(SOURCES.map(s => [s.id, s]))

  return mockData.map((item, index) => ({
    id: Date.now() + index,
    title: item.title,
    summary: 'Description détaillée de cette actualité cyber. Restez informé des dernières menaces.',
    category: item.category,
    severity: item.severity,
    date: new Date(Date.now() - index * 3600000 * (Math.random() * 5 + 1)).toISOString(),
    source: item.source,
    url: '#',
    isReal: false,
    sourceName: sourceMap[item.source]?.name || 'Inconnu',
    country: sourceMap[item.source]?.country || '🌍'
  }))
}

// ============================================
// REFRESH FUNCTION
// ============================================

async function refresh() {
  isLoading.value = true
  error.value = null
  
  try {
    const realArticles = await fetchRealArticles()
    
    if (realArticles.length > 0) {
      items.value = realArticles
      lastUpdated.value = new Date().toISOString()
    } else {
      // Fallback to mock data
      items.value = generateMockArticles()
      lastUpdated.value = new Date().toISOString()
      error.value = '⚠️ Sources indisponibles - Mode simulation'
    }
  } catch (err) {
    console.error('❌ Erreur:', err)
    items.value = generateMockArticles()
    lastUpdated.value = new Date().toISOString()
    error.value = '⚠️ Erreur de connexion - Mode simulation'
  } finally {
    isLoading.value = false
  }
}

// ============================================
// AUTO REFRESH
// ============================================

function startAutoRefresh() {
  if (refreshInterval) clearInterval(refreshInterval)
  refreshInterval = setInterval(() => {
    if (isAutoRefresh.value) {
      refresh()
    }
  }, 60000) // Toutes les 60 secondes
}

function toggleAutoRefresh() {
  isAutoRefresh.value = !isAutoRefresh.value
  if (isAutoRefresh.value) {
    startAutoRefresh()
  } else {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }
}

// ============================================
// LIFECYCLE
// ============================================

onMounted(() => {
  refresh()
  startAutoRefresh()
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
    refreshInterval = null
  }
})
</script>

<template>
  <section id="threat-intel" class="py-20 px-4 bg-gradient-to-b from-slate-50 to-white">
    <div class="max-w-7xl mx-auto">
      <div class="text-center mb-12">
        <div class="inline-flex items-center gap-2 bg-blue-50/80 border border-blue-200/50 rounded-full px-4 py-1.5 text-sm font-medium text-blue-700 mb-4">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          Intelligence en direct
        </div>
        
        <h2 class="text-3xl sm:text-4xl font-bold text-slate-800 font-display">🧠 Veille sur les menaces</h2>
        <p class="text-slate-500 mt-2 max-w-2xl mx-auto">
          Alimentée par des flux RSS et des sources de cybersécurité internationales, classée par catégorie.
        </p>
        
        <!-- Controls -->
        <div class="mt-4 flex flex-col items-center gap-2">
          <div class="flex flex-wrap items-center gap-3">
            <button
              :disabled="isLoading"
              class="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition disabled:opacity-60 flex items-center gap-2"
              @click="refresh"
            >
              <span v-if="isLoading" class="h-3.5 w-3.5 rounded-full border-2 border-white/60 border-t-white animate-spin"></span>
              <i v-else class="fas fa-sync-alt"></i>
              {{ isLoading ? 'Actualisation…' : 'Actualiser' }}
            </button>
            
            <button
              @click="toggleAutoRefresh"
              class="px-4 py-2.5 text-sm font-medium rounded-xl transition flex items-center gap-2"
              :class="isAutoRefresh ? 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'"
            >
              <i :class="isAutoRefresh ? 'fas fa-pause' : 'fas fa-play'"></i>
              {{ isAutoRefresh ? 'Auto' : 'Manuel' }}
            </button>
          </div>
          
          <span v-if="lastUpdated && !isLoading" class="text-xs text-slate-400 flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full" :class="onlineSources > 0 ? 'bg-emerald-500' : 'bg-yellow-500'"></span>
            Mis à jour {{ new Date(lastUpdated).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }) }}
            <span class="text-slate-300">•</span>
            {{ onlineSources }}/{{ totalSources }} sources en ligne
          </span>
          
          <p v-if="error" class="text-sm text-yellow-600 bg-yellow-50 px-4 py-2 rounded-lg border border-yellow-200">
            {{ error }}
          </p>
        </div>
      </div>

      <!-- Status Badges -->
      <div class="flex flex-wrap gap-2 justify-center mb-8">
        <span v-for="source in sourceStatuses" :key="source.id" class="text-xs px-3 py-1.5 rounded-full border flex items-center gap-1.5" :class="source.isOnline ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-slate-50 border-slate-200 text-slate-400'">
          <span class="w-1.5 h-1.5 rounded-full" :class="source.isOnline ? 'bg-emerald-500' : 'bg-slate-300'"></span>
          {{ source.name }}
        </span>
      </div>

      <!-- Articles Grid -->
      <div v-if="items.length === 0 && !isLoading" class="text-center py-12">
        <div class="text-4xl mb-4">📡</div>
        <p class="text-slate-500">Aucun article disponible</p>
        <p class="text-xs text-slate-400">Cliquez sur "Actualiser" pour charger les données</p>
      </div>

      <div v-else class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <article
          v-for="item in items"
          :key="item.id"
          class="bg-white rounded-xl border border-slate-100 overflow-hidden transition hover:-translate-y-1 hover:shadow-xl shadow-md group"
        >
          <div class="p-5">
            <!-- Header: Source + Badge -->
            <div class="flex items-start justify-between mb-2">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-slate-600">{{ item.sourceName || 'Inconnu' }}</span>
                <span class="text-xs text-slate-400">{{ item.country || '' }}</span>
              </div>
              <span 
                class="text-[10px] font-semibold px-2.5 py-0.5 rounded-full border"
                :class="getSeverityColor(item.severity)"
              >
                {{ getSeverityBadge(item.severity) }}
              </span>
            </div>

            <!-- Title -->
            <h4 class="text-sm font-semibold text-slate-800 mb-1.5 line-clamp-2 group-hover:text-blue-600 transition">
              <a :href="item.url" target="_blank" rel="noopener" class="hover:underline">
                {{ item.title }}
              </a>
            </h4>

            <!-- Summary -->
            <p class="text-xs text-slate-500 leading-relaxed mb-3 line-clamp-3">{{ item.summary }}</p>

            <!-- Footer -->
            <div class="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400">
              <span class="flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full" :class="item.isReal ? 'bg-emerald-500' : 'bg-yellow-500'"></span>
                <span class="font-medium" :class="item.isReal ? 'text-emerald-600' : 'text-yellow-600'">
                  {{ item.isReal ? 'Live' : 'Simulation' }}
                </span>
              </span>
              <span class="flex items-center gap-1">
                <i class="fas fa-tag text-[10px] text-slate-300"></i>
                {{ item.category }}
              </span>
              <span>{{ getTimeAgo(item.date) }}</span>
            </div>

            <!-- Source Link -->
            <div class="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between">
              <span class="text-[10px] text-slate-400">
                <i class="fas fa-rss text-orange-500 mr-1"></i>
                {{ item.sourceName }}
              </span>
              <a :href="item.url" target="_blank" rel="noopener" class="text-[10px] text-blue-600 hover:underline font-medium">
                Lire <i class="fas fa-arrow-right ml-1"></i>
              </a>
            </div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Animation pour le statut en direct */
@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(2); opacity: 0; }
}

.animate-ping {
  animation: pulse-ring 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
}
</style>