    <template>
    <div class="min-h-screen bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 transition-colors">
        <!-- ============== SIDEBAR ============== -->
        <aside
        class="fixed top-0 left-0 z-40 h-full bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 shadow-sm transition-all duration-300 ease-in-out"
        :class="[
            isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
            isCollapsed ? 'lg:w-20' : 'lg:w-64',
            'w-64'
        ]"
        >
        <div class="flex flex-col h-full">
            <!-- Sidebar Header -->
            <div class="flex items-center gap-3 px-4 h-16 border-b border-slate-200 dark:border-slate-800">
            <div class="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-md shadow-blue-500/25 flex-shrink-0">
                <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.25" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M9 12l2 2 4-4" />
                </svg>
            </div>
            <template v-if="!isCollapsed">
                <span class="text-base font-extrabold tracking-tight whitespace-nowrap">
                Phish<span class="text-blue-600">Guard</span><span class="text-cyan-500">-AI</span>
                </span>
                <span class="ml-1 text-[10px] font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 dark:bg-blue-500/10 dark:text-blue-400 px-2 py-0.5 rounded-full">SOC</span>
            </template>
            <button
                @click="isCollapsed = !isCollapsed"
                class="ml-auto hidden lg:flex items-center justify-center w-7 h-7 rounded-md text-slate-400 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                :title="isCollapsed ? 'Développer' : 'Réduire'"
            >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path :d="isCollapsed ? 'M9 18l6-6-6-6' : 'M15 18l-6-6 6-6'" />
                </svg>
            </button>
            </div>

            <!-- Navigation -->
            <nav class="flex-1 px-2 py-4 overflow-y-auto">
            <div v-for="(group, gi) in navGroups" :key="gi" class="mb-4">
                <p v-if="!isCollapsed" class="px-3 mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">{{ group.label }}</p>
                <div class="space-y-0.5">
                <router-link
                    v-for="item in group.items"
                    :key="item.path"
                    :to="item.path"
                    :title="isCollapsed ? item.label : ''"
                    class="group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
                    :class="isActive(item.path)
                    ? 'bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300'
                    : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100'"
                >
                    <component :is="item.icon" class="w-[18px] h-[18px] flex-shrink-0" />
                    <span v-if="!isCollapsed" class="truncate">{{ item.label }}</span>
                    <span
                    v-if="item.badge && !isCollapsed"
                    class="ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full"
                    :class="(item as { badgeTone?: string }).badgeTone === 'danger' ? 'bg-red-500 text-white animate-pulse' : 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200'"
                    >{{ item.badge }}</span>
                    <span v-else-if="item.badge && isCollapsed" class="absolute right-3 w-1.5 h-1.5 rounded-full bg-red-500" />
                </router-link>
                </div>
            </div>
            </nav>

            <!-- Bottom: System pulse + Logout -->
            <div class="px-3 py-3 border-t border-slate-200 dark:border-slate-800 space-y-2">
            <div v-if="!isCollapsed" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-50 dark:bg-emerald-500/10">
                <span class="relative flex h-2 w-2">
                <span class="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
                <span class="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                <span class="text-xs font-medium text-emerald-700 dark:text-emerald-400">Infrastructure opérationnelle</span>
            </div>
            <button
                @click="handleLogout"
                class="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition"
            >
                <svg class="w-[18px] h-[18px] flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
                </svg>
                <span v-if="!isCollapsed">Déconnexion</span>
            </button>
            </div>
        </div>
        </aside>

        <!-- Mobile Overlay -->
        <div
        v-if="isSidebarOpen"
        class="fixed inset-0 z-30 bg-slate-900/50 backdrop-blur-sm lg:hidden"
        @click="isSidebarOpen = false"
        />

        <!-- ============== MAIN ============== -->
        <div class="transition-all duration-300" :class="isCollapsed ? 'lg:ml-20' : 'lg:ml-64'">
        <!-- TOP BAR -->
        <header class="sticky top-0 z-20 backdrop-blur-md bg-white/80 dark:bg-slate-950/80 border-b border-slate-200 dark:border-slate-800">
            <div class="flex items-center gap-3 h-16 px-4">
            <!-- Mobile toggle -->
            <button
                @click="isSidebarOpen = !isSidebarOpen"
                class="lg:hidden p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
            >
                <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M4 6h16M4 12h16M4 18h16" />
                </svg>
            </button>

            <!-- Page title -->
            <div class="hidden md:block">
                <div class="text-sm font-semibold">{{ pageTitle }}</div>
                <div class="text-[11px] text-slate-500 dark:text-slate-400">{{ pageSubtitle }}</div>
            </div>

            <!-- Global search -->
            <button
                @click="openSearch"
                class="ml-auto md:ml-6 flex items-center gap-2 w-full max-w-sm px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900 text-sm text-slate-500 hover:border-slate-300 dark:hover:border-slate-700 transition"
            >
                <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="7" /><path d="M21 21l-4.35-4.35" />
                </svg>
                <span class="truncate">Rechercher emails, menaces, utilisateurs…</span>
                <kbd class="ml-auto hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono border border-slate-200 dark:border-slate-700 rounded">Ctrl K</kbd>
            </button>

            <!-- Right cluster -->
            <div class="flex items-center gap-1 ml-auto md:ml-0">
                <!-- System status -->
                <div class="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20">
                <span class="relative flex h-1.5 w-1.5">
                    <span class="motion-safe:animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75" />
                    <span class="relative inline-flex h-1.5 w-1.5 rounded-full bg-emerald-500" />
                </span>
                <span class="text-xs font-medium text-emerald-700 dark:text-emerald-400">Tous systèmes OK</span>
                </div>

                <!-- Theme -->
                <button
                @click="toggleTheme"
                class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                :title="isDark ? 'Mode clair' : 'Mode sombre'"
                >
                <svg v-if="!isDark" class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
                <svg v-else class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
                </svg>
                </button>

                <!-- Notifications -->
                <div class="relative">
                <button
                    @click="showNotifications = !showNotifications"
                    class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition relative"
                >
                    <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
                    </svg>
                    <span class="absolute top-1 right-1 min-w-[16px] h-4 px-1 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center">3</span>
                </button>
                <div v-if="showNotifications" class="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
                    <div class="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800">
                    <span class="text-sm font-semibold">Notifications</span>
                    <button class="text-xs text-blue-600 hover:underline">Tout marquer lu</button>
                    </div>
                    <div class="max-h-80 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
                    <div v-for="n in notifications" :key="n.id" class="p-3 hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <div class="flex items-start gap-2">
                        <span class="w-2 h-2 rounded-full mt-1.5" :class="n.tone === 'critical' ? 'bg-red-500' : n.tone === 'high' ? 'bg-orange-500' : 'bg-blue-500'" />
                        <div class="min-w-0">
                            <p class="text-sm font-medium truncate">{{ n.title }}</p>
                            <p class="text-xs text-slate-500 truncate">{{ n.detail }}</p>
                            <p class="text-[11px] text-slate-400 mt-0.5">{{ n.time }}</p>
                        </div>
                        </div>
                    </div>
                    </div>
                </div>
                </div>

                <!-- Profile -->
                <div class="relative">
                <button
                    @click="showProfile = !showProfile"
                    class="flex items-center gap-2 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                >
                    <div class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white text-xs font-bold">{{ profileInitials }}</div>
                    <div class="hidden md:block text-left">
                    <div class="text-xs font-semibold leading-tight">{{ displayName }}</div>
                    <div class="text-[10px] text-slate-500 leading-tight">Administrateur</div>
                    </div>
                </button>
                <div v-if="showProfile" class="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
                    <div class="px-4 py-3 border-b border-slate-200 dark:border-slate-800">
                    <p class="text-sm font-semibold">{{ displayName }}</p>
                    <p class="text-xs text-slate-500">{{ user?.email }}</p>
                    </div>
                    <div class="p-1.5">
                    <button @click="goToProfile" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-slate-100 dark:hover:bg-slate-800">Mon profil</button>
                    <button @click="goToSecurity" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-slate-100 dark:hover:bg-slate-800">Préférences</button>
                    <button @click="handleLogout" class="w-full text-left px-3 py-2 rounded-md text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10">Déconnexion</button>
                    </div>
                </div>
                </div>
            </div>
            </div>
        </header>

        <!-- PAGE CONTENT -->
        <main class="pt-6 pb-16 px-4">
            <div class="max-w-[1400px] mx-auto">
            <router-view />
            </div>
        </main>
        </div>

        <!-- ============== COMMAND PALETTE ============== -->
        <div
        v-if="searchOpen"
        class="fixed inset-0 z-50 flex items-start justify-center p-4 pt-24 bg-slate-900/60 backdrop-blur-sm"
        @click.self="searchOpen = false"
        >
        <div class="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
            <div class="flex items-center gap-3 px-5 py-3 border-b border-slate-200 dark:border-slate-800">
            <svg class="w-5 h-5 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="11" cy="11" r="7" /><path d="M21 21l-4.35-4.35" />
            </svg>
            <input
                v-model="searchQuery"
                autofocus
                type="text"
                placeholder="Rechercher emails, menaces, utilisateurs, URLs, incidents…"
                class="flex-1 bg-transparent outline-none text-sm placeholder:text-slate-400"
            />
            <kbd class="text-[10px] font-mono px-1.5 py-0.5 border border-slate-200 dark:border-slate-700 rounded">ESC</kbd>
            </div>
            <div class="max-h-96 overflow-y-auto p-2">
            <template v-for="g in searchGroups" :key="g.label">
                <p class="px-3 pt-3 pb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-400">{{ g.label }}</p>
                <button
                v-for="r in g.results"
                :key="r.id"
                class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-left transition"
                >
                <span class="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-xs">{{ r.icon }}</span>
                <div class="min-w-0">
                    <p class="text-sm font-medium truncate">{{ r.title }}</p>
                    <p class="text-xs text-slate-500 truncate">{{ r.subtitle }}</p>
                </div>
                <span class="ml-auto text-xs text-slate-400">{{ r.kind }}</span>
                </button>
            </template>
            <p v-if="searchQuery && searchGroups.length === 0" class="text-center text-sm text-slate-400 py-8">Aucun résultat pour « {{ searchQuery }} »</p>
            <p v-if="!searchQuery" class="text-center text-sm text-slate-400 py-8">Tapez pour rechercher dans toute la plateforme</p>
            </div>
        </div>
        </div>
    </div>
    </template>

    <script setup lang="ts">
    import { ref, computed, onMounted, onBeforeUnmount, h } from 'vue'
    import { useRoute, useRouter } from 'vue-router'
    import { useAuth } from '@/composables'

    const route = useRoute()
    const router = useRouter()
    const { logout, user } = useAuth()

    const displayName = computed(() => user.value?.displayName || user.value?.email?.split('@')[0] || 'Administrateur')
    const profileInitials = computed(() => {
    const parts = displayName.value.split(' ')
    return `${parts[0]?.charAt(0) ?? ''}${parts[1]?.charAt(0) ?? ''}`.toUpperCase() || 'A'
    })

    const isSidebarOpen = ref(false)
    const isCollapsed = ref(false)
    const showNotifications = ref(false)
    const showProfile = ref(false)
    const searchOpen = ref(false)
    const searchQuery = ref('')
    const isDark = ref(false)

    /* ---------- Icon helpers (inline SVG so we don't add deps) ---------- */
    const Icon = (paths: string) => () => h('svg', { viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, paths.split('|').map(d => h('path', { d })))
    const IconOverview = Icon('M3 12h18M3 6h18M3 18h18')
    const IconUsers = Icon('M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2|M9 7a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75')
    const IconReports = Icon('M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z|M12 9v4M12 17h.01')
    const IconIntel = Icon('M12 2a3 3 0 0 0-3 3v1a3 3 0 0 0-3 3v1a3 3 0 0 0 0 6v1a3 3 0 0 0 3 3v1a3 3 0 0 0 6 0v-1a3 3 0 0 0 3-3v-1a3 3 0 0 0 0-6v-1a3 3 0 0 0-3-3V5a3 3 0 0 0-3-3z')
    const IconModels = Icon('M12 2v4|M12 18v4|M4.93 4.93l2.83 2.83|M16.24 16.24l2.83 2.83|M2 12h4|M18 12h4|M4.93 19.07l2.83-2.83|M16.24 7.76l2.83-2.83')
    const IconAudit = Icon('M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z|M14 2v6h6M9 13h6M9 17h6')
    const IconSettings = Icon('M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z|M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z')
    const IconIncidents = Icon('M12 9v4M12 17h.01|M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z')
    const IconHealth = Icon('M22 12h-4l-3 9L9 3l-3 9H2')
    const IconIntegrations = Icon('M9 3H5a2 2 0 0 0-2 2v4|M15 3h4a2 2 0 0 1 2 2v4|M9 21H5a2 2 0 0 1-2-2v-4|M15 21h4a2 2 0 0 0 2-2v-4|M9 12h6')

    const navGroups = [
    {
        label: 'Supervision',
        items: [
        { path: '/admin', label: 'Aperçu SOC', icon: IconOverview },
        { path: '/admin/incidents', label: 'Incidents', icon: IconIncidents, badge: '3', badgeTone: 'danger' },
        ],
    },
    {
        label: 'Opérations',
        items: [
        { path: '/admin/reports', label: 'Signalements', icon: IconReports, badge: '12' },
        { path: '/admin/threat-intel', label: 'Threat Intelligence', icon: IconIntel },
        { path: '/admin/users', label: 'Utilisateurs', icon: IconUsers },
        ],
    },
    {
        label: 'Intelligence Artificielle',
        items: [
        { path: '/admin/models', label: 'AI Engine', icon: IconModels, badge: 'v2.4.1' },
        ],
    },
    {
        label: 'Plateforme',
        items: [
        { path: '/admin/integrations', label: 'Intégrations', icon: IconIntegrations },
        { path: '/admin/health', label: 'Santé Système', icon: IconHealth },
        { path: '/admin/audit', label: 'Audit', icon: IconAudit },
        { path: '/admin/settings', label: 'Paramètres', icon: IconSettings },
        ],
    },
    ]

    const notifications = [
    { id: 1, tone: 'critical', title: 'Campagne phishing détectée', detail: '18 utilisateurs ciblés — MTN Mobile Money', time: 'il y a 3 min' },
    { id: 2, tone: 'high', title: 'Nouveau signalement confirmé', detail: 'mtn-secure-cm.tk bloqué par admin', time: 'il y a 27 min' },
    { id: 3, tone: 'info', title: 'Modèle ML v2.4.1 déployé', detail: 'Précision 94.7% • F1 93.5%', time: 'il y a 2 h' },
    ]

    const pageTitle = computed(() => {
    const map: Record<string, string> = {
        '/admin': 'Security Operations Center',
        '/admin/users': 'Utilisateurs',
        '/admin/reports': 'Signalements',
        '/admin/threat-intel': 'Threat Intelligence',
        '/admin/models': 'AI Engine',
        '/admin/audit': 'Journal d\'audit',
        '/admin/settings': 'Paramètres plateforme',
        '/admin/incidents': 'Gestion des incidents',
        '/admin/integrations': 'Intégrations',
        '/admin/health': 'Santé infrastructure',
    }
    return map[route.path] || 'PhishGuard-AI Admin'
    })
    const pageSubtitle = computed(() => 'PhishGuard-AI • Détecter · Expliquer · Protéger')

    const isActive = (path: string) => route.path === path || route.path.startsWith(path + '/')

    const searchGroups = computed(() => {
    if (!searchQuery.value.trim()) return []
    const q = searchQuery.value.toLowerCase()
    const groups: Array<{ label: string; results: any[] }> = [
        {
        label: 'Menaces',
        results: [
            { id: 't1', icon: '🚨', title: 'Phishing — MTN Mobile Money', subtitle: 'risk 92/100 • 18 utilisateurs ciblés', kind: 'menace' },
            { id: 't2', icon: '🔗', title: 'mtn-secure-cm.tk', subtitle: 'domaine malveillant • confiance 96%', kind: 'domaine' },
        ].filter(r => r.title.toLowerCase().includes(q) || r.subtitle.toLowerCase().includes(q)),
        },
        {
        label: 'Utilisateurs',
        results: [
            { id: 'u1', icon: '👤', title: 'Lareine Tracy', subtitle: 'lareine@phishguard.cm • Admin', kind: 'utilisateur' },
            { id: 'u2', icon: '👤', title: 'Jean Dupont', subtitle: 'jean@example.com • Utilisateur', kind: 'utilisateur' },
        ].filter(r => r.title.toLowerCase().includes(q) || r.subtitle.toLowerCase().includes(q)),
        },
        {
        label: 'Incidents',
        results: [
            { id: 'i1', icon: '⚠️', title: 'INC-2026-0142 — Campagne Mobile Money', subtitle: 'Investigation en cours • Sévérité élevée', kind: 'incident' },
        ].filter(r => r.title.toLowerCase().includes(q) || r.subtitle.toLowerCase().includes(q)),
        },
    ]
    return groups.filter(g => g.results.length > 0)
    })

    function openSearch() { searchOpen.value = true }
    function goToProfile() { showProfile.value = false; router.push({ name: 'admin-settings' }) }
    function goToSecurity() { showProfile.value = false; router.push({ name: 'admin-settings', query: { tab: 'security' } }) }
    function onKey(e: KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openSearch() }
    if (e.key === 'Escape') { searchOpen.value = false; showNotifications.value = false; showProfile.value = false }
    }
    function toggleTheme() {
    isDark.value = !isDark.value
    document.documentElement.classList.toggle('dark', isDark.value)
    }

    onMounted(() => window.addEventListener('keydown', onKey))
    onBeforeUnmount(() => window.removeEventListener('keydown', onKey))

    const handleLogout = async () => {
    await logout()
    router.push({ name: 'home' })
    }
    </script>