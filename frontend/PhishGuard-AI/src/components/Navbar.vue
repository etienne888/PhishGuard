    <script setup lang="ts">
    import { ref, onMounted, onUnmounted } from 'vue'
    import { useRouter } from 'vue-router'
    import AppLogo from './AppLogo.vue'
    import { useAuth } from '@/composables'
    import { useI18n } from '@/i18n'
    import { useHealthStore } from '@/stores/health'

    const { user, openModal, logout } = useAuth()
    const { locale, locales, t, setLocale } = useI18n()
    const router = useRouter()
    const healthStore = useHealthStore()
    const isMenuOpen = ref(false)
    const isProfileOpen = ref(false)
    const profileRef = ref<HTMLElement | null>(null)

    const links = [
        { href: '#analyze', key: 'nav.analyze' as const },
        { href: '#education', key: 'nav.education' as const },
        { href: '#threat-intel', key: 'nav.threatIntel' as const },
        { href: '#about', key: 'nav.about' as const }
    ]

    // ---- dark mode toggle (opt-in, persisted) ----
    const isDark = ref(false)

    function applyTheme(dark: boolean) {
        document.documentElement.classList.toggle('dark', dark)
    }

    function toggleTheme() {
        isDark.value = !isDark.value
        localStorage.setItem('pg-theme', isDark.value ? 'dark' : 'light')
        applyTheme(isDark.value)
    }

    function changeLocale(event: Event) {
        setLocale((event.target as HTMLSelectElement).value as typeof locale.value)
    }

    onMounted(() => {
        const stored = localStorage.getItem('pg-theme')
        isDark.value = stored ? stored === 'dark' : window.matchMedia('(prefers-color-scheme: dark)').matches
        applyTheme(isDark.value)
        document.addEventListener('click', handleOutsideClick)
        void healthStore.refresh()
    })
    onUnmounted(() => document.removeEventListener('click', handleOutsideClick))

    function handleOutsideClick(event: MouseEvent) {
        if (isProfileOpen.value && !profileRef.value?.contains(event.target as Node)) {
            isProfileOpen.value = false
        }
    }

    async function handleLogout() {
        isProfileOpen.value = false
        isMenuOpen.value = false
        await logout()
        router.push({ name: 'home' })
    }
    </script>

    <template>
        <nav class="fixed top-0 left-0 w-full z-50 bg-white/80 dark:bg-slate-900/85 backdrop-blur-xl border-b border-slate-200/60 dark:border-slate-800 transition-colors">
            <!-- ambient scan line — own overflow-hidden wrapper so it never clips the dropdowns below -->
            <div class="absolute inset-x-0 top-0 h-px overflow-hidden pointer-events-none">
                <div class="h-px w-full -translate-x-full bg-gradient-to-r from-transparent via-cyan-400/60 to-transparent motion-safe:animate-[scan-sweep_6s_linear_infinite]" />
            </div>

            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="flex items-center justify-between h-16">
                    <a href="#" class="flex items-center gap-2.5">
                        <div class="relative">
                            <span class="absolute inset-0 rounded-full bg-cyan-400/0 dark:bg-cyan-400/30 blur-md transition-colors" />
                            <AppLogo :size="36" class="relative" />
                        </div>
                        <span class="text-xl font-extrabold tracking-tight font-display">
                            <span class="text-slate-800 dark:text-white">Phish</span><span class="text-blue-600 dark:text-cyan-400">Guard</span><span class="text-cyan-500 dark:text-slate-500">-AI</span>
                        </span>
                        <span class="ml-1 hidden sm:inline-flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider bg-emerald-50/80 dark:bg-slate-800/80 px-2.5 py-1 rounded-full border border-emerald-200/50 dark:border-slate-700">
                                <span class="flex gap-0.5" :title="healthStore.status?.status ?? 'unknown'">
                                <span
                                    class="h-1.5 w-1.5 rounded-full"
                                    :class="{
                                        'bg-emerald-500': healthStore.tone === 'green',
                                        'bg-amber-500': healthStore.tone === 'amber',
                                        'bg-red-500': healthStore.tone === 'red',
                                    }"
                                />
                                <span class="h-1.5 w-1.5 rounded-full bg-red-500" />
                                <span class="h-1.5 w-1.5 rounded-full bg-yellow-500" />
                            </span>
                            <span class="text-emerald-700 dark:text-slate-400">Cameroun</span>
                        </span>
                    </a>

                    <div class="hidden md:flex items-center gap-1">
                        <a v-for="link in links" :key="link.href" :href="link.href"
                            class="group relative px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-cyan-300 transition-colors">
                            {{ t(link.key) }}
                            <span class="absolute left-4 right-4 -bottom-px h-px bg-blue-600 dark:bg-cyan-400 scale-x-0 group-hover:scale-x-100 transition-transform origin-center" />
                        </a>
                    </div>

                    <div class="hidden sm:flex items-center gap-2">
                        <label class="sr-only" for="language-select">{{ t('nav.language') }}</label>
                        <select id="language-select" :value="locale" class="max-w-[150px] bg-transparent text-xs font-semibold text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 rounded-lg px-2 py-2" @change="changeLocale">
                            <option v-for="option in locales" :key="option.code" :value="option.code">{{ option.nativeLabel }}</option>
                        </select>
                        <!-- theme toggle -->
                        <button
                            @click="toggleTheme"
                            class="p-2 rounded-lg text-slate-500 dark:text-slate-300 hover:bg-blue-50/60 dark:hover:bg-white/5 transition"
                            :aria-label="isDark ? t('nav.lightMode') : t('nav.darkMode')"
                        >
                            <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" /></svg>
                            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
                        </button>

                        <template v-if="!user">
                            <button
                                class="px-4 py-2 text-sm font-semibold text-slate-700 dark:text-slate-300 hover:text-blue-600 dark:hover:text-cyan-300 rounded-lg hover:bg-blue-50/60 dark:hover:bg-white/5 transition"
                                @click="openModal('login')">
                                {{ t('nav.login') }}
                            </button>
                            <button
                                class="px-5 py-2 text-sm font-semibold rounded-lg transition hover:scale-[1.02] active:scale-[0.98]
                                    text-white bg-gradient-to-r from-blue-600 to-cyan-500 shadow-md shadow-blue-500/25 hover:shadow-blue-500/40
                                    dark:text-slate-900 dark:bg-cyan-400 dark:bg-none dark:shadow-[0_0_20px_-4px_rgba(34,211,238,0.6)] dark:hover:bg-cyan-300 dark:hover:shadow-[0_0_28px_-2px_rgba(34,211,238,0.8)]"
                                @click="openModal('register')">
                                {{ t('nav.register') }}
                            </button>
                        </template>

                        <div v-else ref="profileRef" class="flex items-center relative">
                            <button
                                class="flex items-center gap-2 px-3 py-1.5 rounded-lg hover:bg-blue-50/60 dark:hover:bg-white/5 transition"
                                @click="isProfileOpen = !isProfileOpen">
                                <span
                                    class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold
                                        bg-gradient-to-r from-blue-600 to-cyan-500 text-white
                                        dark:bg-slate-800 dark:bg-none dark:text-cyan-300 dark:ring-1 dark:ring-cyan-400/50">
                                    {{ (user.displayName || user.email).charAt(0).toUpperCase() }}
                                </span>
                                <span class="text-sm font-semibold text-slate-700 dark:text-slate-200 max-w-[140px] truncate">
                                    {{ user.displayName || user.email }}
                                </span>
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                    stroke-width="2" class="transition-transform text-slate-400 dark:text-slate-500"
                                    :class="{ 'rotate-180': isProfileOpen }">
                                    <path d="M6 9l6 6 6-6" stroke-linecap="round" stroke-linejoin="round" />
                                </svg>
                            </button>

                            <div v-if="isProfileOpen"
                                class="absolute right-0 top-12 w-56 rounded-xl border py-2 z-50
                                    bg-white border-slate-100 shadow-card
                                    dark:bg-slate-900 dark:border-slate-700 dark:shadow-2xl">
                                <div class="px-4 py-2 border-b border-slate-100 dark:border-slate-800">
                                    <p class="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{{ user.displayName || t('nav.user') }}</p>
                                    <p class="text-xs text-slate-500 truncate">{{ user.email }}</p>
                                </div>
                                <RouterLink to="/dashboard" class="block px-4 py-2 text-sm text-slate-600 dark:text-slate-300 hover:bg-blue-50/60 dark:hover:bg-white/5 dark:hover:text-cyan-300" @click="isProfileOpen = false">
                                    {{ t('nav.dashboard') }}
                                </RouterLink>
                                <RouterLink v-if="user.is_admin" to="/admin" class="block px-4 py-2 text-sm text-slate-600 dark:text-slate-300 hover:bg-blue-50/60 dark:hover:bg-white/5 dark:hover:text-cyan-300" @click="isProfileOpen = false">
                                    {{ t('nav.admin') }}
                                </RouterLink>
                                <button class="w-full text-left px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50/60 dark:hover:bg-red-500/10" @click="handleLogout">
                                    {{ t('nav.logout') }}
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="flex sm:hidden items-center gap-1">
                        <button
                            @click="toggleTheme"
                            class="p-2 rounded-lg text-slate-500 dark:text-slate-300"
                            :aria-label="isDark ? t('nav.lightMode') : t('nav.darkMode')"
                        >
                            <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" /></svg>
                            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
                        </button>
                        <button class="p-2 text-slate-600 dark:text-slate-300" :aria-label="t('nav.openMenu')"
                            @click="isMenuOpen = !isMenuOpen">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                stroke-width="2">
                                <path v-if="!isMenuOpen" d="M4 6h16M4 12h16M4 18h16" stroke-linecap="round" />
                                <path v-else d="M6 6l12 12M18 6L6 18" stroke-linecap="round" />
                            </svg>
                        </button>
                    </div>
                </div>

                <div v-if="isMenuOpen" class="md:hidden pb-4 flex flex-col gap-1 border-t border-slate-100 dark:border-slate-800 pt-3">
                    <a v-for="link in links" :key="link.href" :href="link.href"
                        class="px-3 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 rounded-lg hover:bg-blue-50/60 dark:hover:bg-white/5"
                        @click="isMenuOpen = false">
                        {{ t(link.key) }}
                    </a>
                    <template v-if="!user">
                        <div class="flex gap-2 mt-2">
                            <button
                                class="flex-1 px-4 py-2 text-sm font-semibold text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 rounded-lg"
                                @click="openModal('login')">
                                {{ t('nav.login') }}
                            </button>
                            <button
                                class="flex-1 px-4 py-2 text-sm font-semibold rounded-lg text-white bg-gradient-to-r from-blue-600 to-cyan-500 dark:text-slate-900 dark:bg-cyan-400 dark:bg-none"
                                @click="openModal('register')">
                                {{ t('nav.register') }}
                            </button>
                        </div>
                    </template>
                    <template v-else>
                        <div class="mt-2 pt-2 border-t border-slate-100 dark:border-slate-800">
                            <p class="px-3 text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{{ user.displayName || t('nav.user') }}</p>
                            <RouterLink to="/dashboard" class="block px-3 py-2 text-sm text-slate-600 dark:text-slate-300" @click="isMenuOpen = false">
                                {{ t('nav.dashboard') }}
                            </RouterLink>
                            <RouterLink v-if="user.is_admin" to="/admin" class="block px-3 py-2 text-sm text-slate-600 dark:text-slate-300" @click="isMenuOpen = false">
                                {{ t('nav.admin') }}
                            </RouterLink>
                            <button class="w-full text-left px-3 py-2 text-sm text-red-600 dark:text-red-400" @click="handleLogout">
                                {{ t('nav.logout') }}
                            </button>
                        </div>
                    </template>
                </div>
            </div>
        </nav>
    </template>

    <style scoped>
    @keyframes scan-sweep {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }
    </style>