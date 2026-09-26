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
                :title="isCollapsed ? t('admin.layout.expand') : t('admin.layout.collapse')"
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
                    <span v-if="item.demo && !isCollapsed" class="ml-auto rounded px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide bg-slate-100 text-slate-400 dark:bg-slate-800">{{ t('admin.layout.demo') }}</span>
                    <span
                    v-else-if="item.badge && !isCollapsed"
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
                <span class="text-xs font-medium text-emerald-700 dark:text-emerald-400">{{ t('admin.layout.infraOk') }}</span>
            </div>
            <button
                @click="handleLogout"
                class="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition"
            >
                <svg class="w-[18px] h-[18px] flex-shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
                </svg>
                <span v-if="!isCollapsed">{{ t('nav.logout') }}</span>
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
                <span class="truncate">{{ t('admin.layout.searchShort') }}</span>
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
                <span class="text-xs font-medium text-emerald-700 dark:text-emerald-400">{{ t('admin.layout.allOk') }}</span>
                </div>

                <!-- Language -->
                <select :value="locale" :aria-label="t('nav.language')" :title="t('nav.language')"
                        class="hidden sm:block max-w-[130px] bg-transparent text-xs font-semibold text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-1.5"
                        @change="setLocale(($event.target as HTMLSelectElement).value as Locale)">
                <option v-for="option in locales" :key="option.code" :value="option.code">{{ option.nativeLabel }}</option>
                </select>

                <!-- Theme -->
                <button
                @click="toggleTheme"
                class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                :title="isDark ? t('nav.lightMode') : t('nav.darkMode')"
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
                    <span v-if="unreadAlerts" class="absolute top-1 right-1 min-w-[16px] h-4 px-1 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center">{{ unreadAlerts }}</span>
                </button>
                <div v-if="showNotifications" class="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
                    <div class="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-slate-800">
                    <span class="text-sm font-semibold">{{ t('admin.layout.liveAlerts') }}</span>
                    <button class="text-xs text-blue-600 hover:underline" @click="ops.load()">{{ t('common.refresh') }}</button>
                    </div>
                    <div class="max-h-80 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
                    <p v-if="!notifications.length" class="p-4 text-center text-sm text-slate-400">{{ t('admin.layout.noAlerts') }}</p>
                    <div v-for="n in notifications" :key="n.id" class="p-3 hover:bg-slate-50 dark:hover:bg-slate-800/50" :class="{ 'cursor-pointer': n.to }" @click="openNotification(n)">
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
                    <img v-if="user?.avatar_url" :src="user.avatar_url" alt="" class="w-8 h-8 rounded-full object-cover ring-2 ring-white dark:ring-slate-800" />
                    <div v-else class="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 flex items-center justify-center text-white text-xs font-bold">{{ profileInitials }}</div>
                    <div class="hidden md:block text-left">
                    <div class="text-xs font-semibold leading-tight">{{ displayName }}</div>
                    <div class="text-[10px] text-slate-500 leading-tight">{{ t('admin.layout.administrator') }}</div>
                    </div>
                </button>
                <div v-if="showProfile" class="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">
                    <div class="px-4 py-3 border-b border-slate-200 dark:border-slate-800">
                    <p class="text-sm font-semibold">{{ displayName }}</p>
                    <p class="text-xs text-slate-500">{{ user?.email }}</p>
                    </div>
                    <div class="p-1.5">
                    <button @click="goToProfile" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-slate-100 dark:hover:bg-slate-800">{{ t('admin.layout.myProfile') }}</button>
                    <button @click="goToSecurity" class="w-full text-left px-3 py-2 rounded-md text-sm hover:bg-slate-100 dark:hover:bg-slate-800">{{ t('admin.layout.preferences') }}</button>
                    <button @click="handleLogout" class="w-full text-left px-3 py-2 rounded-md text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-500/10">{{ t('nav.logout') }}</button>
                    </div>
                </div>
                </div>
            </div>
            </div>
        </header>

        <!-- PAGE CONTENT -->
        <main class="pt-6 pb-16 px-4">
            <div class="max-w-[1400px] mx-auto">
            <div v-if="route.meta.demo" class="mb-4 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-200">
                <span>🧪</span>
                <span><b>{{ t('admin.layout.demoTitle') }}</b> {{ t('admin.layout.demoText') }}</span>
            </div>
            <router-view />
            </div>
        </main>
        </div>

        <SudoModal />

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
                :placeholder="t('admin.layout.searchLong')"
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
            <p v-if="searchQuery && searchGroups.length === 0" class="text-center text-sm text-slate-400 py-8">{{ t('admin.layout.noResults', { q: searchQuery }) }}</p>
            <p v-if="!searchQuery" class="text-center text-sm text-slate-400 py-8">{{ t('admin.layout.typeToSearch') }}</p>
            </div>
        </div>
        </div>
    </div>
    </template>

    <script setup lang="ts">
    import { ref, computed, onMounted, onBeforeUnmount, h, watch } from 'vue'
    import { useRoute, useRouter } from 'vue-router'
    import { useAuth } from '@/composables'
    import { useAdminOpsStore } from '@/stores/adminOps'
    import { useTheme } from '@/composables/useTheme'
    import { timeAgo } from '@/utils/risk'
    import SudoModal from '@/components/admin/SudoModal.vue'
    import { socService, type SocSummary } from '@/services/soc.service'
    import type { SecurityEvent } from '@/services/admin.service'
    import { apiLanguage, useI18n, type Locale } from '@/i18n'

    const route = useRoute()
    const router = useRouter()
    const { logout, user } = useAuth()
    const { t, locale, locales, setLocale } = useI18n()

    const displayName = computed(() => user.value?.displayName || user.value?.email?.split('@')[0] || t('admin.layout.administrator'))
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
    const { isDark, toggleTheme } = useTheme()

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
    const IconRadar = Icon('M19.1 4.9A10 10 0 1 0 22 12M16.2 7.8A6 6 0 1 0 18 12M12 12l7-7')
    const IconIntegrations = Icon('M9 3H5a2 2 0 0 0-2 2v4|M15 3h4a2 2 0 0 1 2 2v4|M9 21H5a2 2 0 0 1-2-2v-4|M15 21h4a2 2 0 0 0 2-2v-4|M9 12h6')

    const IconWhitelist = Icon('M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z|M9 12l2 2 4-4')

    // Live numbers for badges and the bell (same store as the command centre)
    const ops = useAdminOpsStore()
    let opsTimer: number | undefined

    // SOC counters (incidents, pending accounts) + security alerts for the bell
    const soc = ref<SocSummary | null>(null)
    const securityAlerts = ref<SecurityEvent[]>([])
    async function loadSoc() {
    try {
        const [summary, alerts] = await Promise.all([socService.getSummary(), socService.getAlerts()])
        soc.value = summary
        securityAlerts.value = alerts.items
    } catch { /* counters are optional */ }
    }

    type NavItem = { path: string; label: string; icon: unknown; badge?: string | number; badgeTone?: string; demo?: boolean }
    const navGroups = computed<Array<{ label: string; items: NavItem[] }>>(() => {
    const pending = ops.overview?.review.pending ?? 0
    return [
    {
        label: t('admin.nav.command'),
        items: [
        { path: '/admin', label: t('admin.nav.overview'), icon: IconOverview },
        { path: '/admin/reports', label: t('admin.nav.reports'), icon: IconReports, badge: pending || undefined, badgeTone: ops.overview?.review.reported ? 'danger' : undefined },
        { path: '/admin/users', label: t('admin.nav.users'), icon: IconUsers, badge: soc.value?.pending_accounts || ops.overview?.users.total, badgeTone: soc.value?.pending_accounts ? 'danger' : undefined },
        { path: '/admin/whitelist', label: t('admin.nav.whitelist'), icon: IconWhitelist, badge: ops.overview?.engine.whitelist_domains },
        ],
    },
    {
        label: t('admin.nav.soc'),
        items: [
        { path: '/admin/incidents', label: t('admin.nav.incidents'), icon: IconIncidents, badge: soc.value?.incidents.open || undefined, badgeTone: soc.value?.incidents.critical ? 'danger' : undefined },
        { path: '/admin/radar', label: t('geo.radar.nav'), icon: IconRadar },
        { path: '/admin/threat-intel', label: t('admin.nav.threatIntel'), icon: IconIntel },
        { path: '/admin/audit', label: t('admin.nav.audit'), icon: IconAudit },
        { path: '/admin/health', label: t('admin.nav.health'), icon: IconHealth },
        ],
    },
    {
        label: t('admin.nav.platform'),
        items: [
        { path: '/admin/settings', label: t('admin.nav.settings'), icon: IconSettings },
        { path: '/admin/models', label: t('admin.nav.models'), icon: IconModels, demo: true },
        { path: '/admin/integrations', label: t('admin.nav.integrations'), icon: IconIntegrations, demo: true },
        ],
    },
    ]
    })

    const notifications = computed(() => {
    const d = ops.overview
    if (!d) return []
    const list: Array<{ id: string; tone: string; title: string; detail: string; time: string; to?: string; analysisId?: number }> = []
    if (d.review.reported) list.push({ id: 'reported', tone: 'critical', title: t('admin.alerts.reported', { n: d.review.reported }), detail: t('admin.alerts.reportedDetail'), time: t('admin.alerts.now'), to: '/admin/reports' })
    if (d.review.pending - d.review.reported > 0) list.push({ id: 'borderline', tone: 'high', title: t('admin.alerts.borderline', { n: d.review.pending - d.review.reported }), detail: t('admin.alerts.borderlineDetail'), time: t('admin.alerts.now'), to: '/admin/reports' })
    for (const a of d.latest.filter((x) => x.status === 'phishing').slice(0, 4)) {
        list.push({ id: `a${a.id}`, tone: 'critical', title: t('admin.alerts.threat'), detail: `${a.preview.slice(0, 60)} — ${a.source}`, time: timeAgo(a.received_at), to: '/admin/reports' })
    }
    for (const i of soc.value?.incidents.latest.filter((x) => x.severity === 'critical' || x.status === 'open').slice(0, 3) ?? []) {
        list.push({ id: `inc${i.id}`, tone: i.severity === 'critical' ? 'critical' : 'high', title: `${i.ref} · ${t('admin.alerts.incident')}`, detail: i.indicator ?? i.title, time: timeAgo(i.last_seen), to: '/admin/incidents' })
    }
    if (soc.value?.pending_accounts) list.push({ id: 'pending-accounts', tone: 'high', title: t('admin.alerts.pendingAccounts', { n: soc.value.pending_accounts }), detail: t('um.bannerHint'), time: '', to: '/admin/users' })
    for (const e of securityAlerts.value.slice(0, 5)) {
        list.push({ id: `sec${e.id}`, tone: e.severity === 'critical' ? 'critical' : 'high', title: t(`event.${e.type}`), detail: [e.user, e.ip, e.location === 'local' ? t('as.logins.local') : e.location].filter(Boolean).join(' · '), time: timeAgo(e.created_at), to: '/admin/audit' })
    }
    if (!d.engine.ai_enabled) list.push({ id: 'ai', tone: 'info', title: t('admin.alerts.aiOff'), detail: t('admin.alerts.aiOffDetail'), time: '' })
    return list
    })
    const unreadAlerts = computed(() => notifications.value.filter((n) => n.tone === 'critical').length)

    function openNotification(n: { to?: string }) {
    showNotifications.value = false
    if (n.to) router.push(n.to)
    }

    const pageTitle = computed(() => {
    const map: Record<string, string> = {
        '/admin': t('admin.page.overview'),
        '/admin/users': t('admin.page.users'),
        '/admin/reports': t('admin.page.reports'),
        '/admin/whitelist': t('admin.page.whitelist'),
        '/admin/radar': t('geo.radar.title'),
        '/admin/threat-intel': t('admin.page.threatIntel'),
        '/admin/models': t('admin.page.models'),
        '/admin/audit': t('admin.page.audit'),
        '/admin/settings': t('admin.page.settings'),
        '/admin/incidents': t('admin.page.incidents'),
        '/admin/integrations': t('admin.page.integrations'),
        '/admin/health': t('admin.page.health'),
    }
    return map[route.path] || 'PhishGuard-AI Admin'
    })
    const pageSubtitle = computed(() => t('admin.layout.tagline'))

    const isActive = (path: string) => route.path === path || route.path.startsWith(path + '/')

    const searchGroups = computed(() => {
    if (!searchQuery.value.trim()) return []
    const q = searchQuery.value.toLowerCase()
    const groups: Array<{ label: string; results: any[] }> = [
        {
        label: t('admin.search.threats'),
        results: [
            { id: 't1', icon: '🚨', title: 'Phishing — MTN Mobile Money', subtitle: t('admin.search.sampleThreat'), kind: t('admin.search.kindThreat') },
            { id: 't2', icon: '🔗', title: 'mtn-secure-cm.tk', subtitle: t('admin.search.sampleDomain'), kind: t('admin.search.kindDomain') },
        ].filter(r => r.title.toLowerCase().includes(q) || r.subtitle.toLowerCase().includes(q)),
        },
        {
        label: t('admin.nav.users'),
        results: [
            { id: 'u1', icon: '👤', title: 'Lareine Tracy', subtitle: 'lareine@phishguard.cm • Admin', kind: t('admin.search.kindUser') },
            { id: 'u2', icon: '👤', title: 'Jean Dupont', subtitle: `jean@example.com • ${t('nav.user')}`, kind: t('admin.search.kindUser') },
        ].filter(r => r.title.toLowerCase().includes(q) || r.subtitle.toLowerCase().includes(q)),
        },
        {
        label: t('admin.nav.incidents'),
        results: [
            { id: 'i1', icon: '⚠️', title: `INC-2026-0142 — ${t('admin.search.sampleCampaign')}`, subtitle: t('admin.search.sampleIncident'), kind: t('admin.search.kindIncident') },
        ].filter(r => r.title.toLowerCase().includes(q) || r.subtitle.toLowerCase().includes(q)),
        },
    ]
    return groups.filter(g => g.results.length > 0)
    })

    function openSearch() { searchOpen.value = true }
    function goToProfile() { showProfile.value = false; router.push({ name: 'admin-settings', query: { tab: 'profile' } }) }
    function goToSecurity() { showProfile.value = false; router.push({ name: 'admin-settings', query: { tab: 'security' } }) }
    function onKey(e: KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); openSearch() }
    if (e.key === 'Escape') { searchOpen.value = false; showNotifications.value = false; showProfile.value = false }
    }

    // Engine labels and sources come from the server in the interface language
    watch(apiLanguage, () => { void ops.load(); void loadSoc() })

    onMounted(() => {
    window.addEventListener('keydown', onKey)
    void ops.load()
    void loadSoc()
    opsTimer = window.setInterval(() => { void ops.load(); void loadSoc() }, 30_000)
    })
    onBeforeUnmount(() => {
    window.removeEventListener('keydown', onKey)
    window.clearInterval(opsTimer)
    })

    const handleLogout = async () => {
    await logout()
    router.push({ name: 'home' })
    }
    </script>