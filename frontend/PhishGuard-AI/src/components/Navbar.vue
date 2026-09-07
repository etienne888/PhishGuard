        <script setup lang="ts">
        import { ref } from 'vue'
        import AppLogo from './AppLogo.vue'
        import { useAuth } from '@/composables'

        const { openModal } = useAuth()
        const isMenuOpen = ref(false)

        const links = [
            { href: '#analyze', label: 'Analyser' },
            { href: '#education', label: 'Éducation' },
            { href: '#threat-intel', label: 'Veille' },
            { href: '#about', label: 'À propos' }
        ]
</script>

        <template>
            <nav class="fixed top-0 left-0 w-full z-50 glass border-b border-white/20">
                <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div class="flex items-center justify-between h-16">
                        <a href="#" class="flex items-center gap-2">
                            <AppLogo :size="36" />
                            <span class="text-xl font-extrabold tracking-tight text-slate-800 font-display">
                                <span class="relative inline-block">
                                    <span
                                        class="absolute -inset-1 blur-md bg-gradient-to-r from-blue-600/20 to-cyan-500/20 rounded-lg"></span>
                                    <span class="relative drop-shadow-[0_2px_8px_rgba(37,99,235,0.15)]">
                                        Phish
                                        <span
                                            class="text-blue-600 drop-shadow-[0_2px_8px_rgba(37,99,235,0.25)]">Guard</span>
                                        <span
                                            class="text-cyan-500 drop-shadow-[0_2px_8px_rgba(6,182,212,0.25)]">-AI</span>
                                    </span>
                                </span>
                            </span> <span
                                class="ml-1 hidden sm:inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider bg-emerald-50/80 px-2.5 py-0.5 rounded-full border border-emerald-200/50">
                                <span class="text-emerald-600">Ca</span>
                                <span class="text-red-600">me</span>
                                <span class="text-yellow-600">rou</span>
                                <span class="text-emerald-600">n</span>
                            </span>
                        </a>

                        <div class="hidden md:flex items-center gap-1">
                            <a v-for="link in links" :key="link.href" :href="link.href"
                                class="px-4 py-2 text-sm font-medium text-slate-600 hover:text-blue-600 rounded-lg hover:bg-blue-50/60 transition">
                                {{ link.label }}
                            </a>
                        </div>

                        <div class="hidden sm:flex items-center gap-2">
                            <button
                                class="px-4 py-2 text-sm font-semibold text-slate-700 hover:text-blue-600 rounded-lg hover:bg-blue-50/60 transition"
                                @click="openModal('login')">
                                Se connecter
                            </button>
                            <button
                                class="px-5 py-2 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-cyan-500 rounded-lg shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition hover:scale-[1.02] active:scale-[0.98]"
                                @click="openModal('register')">
                                S'inscrire
                            </button>
                        </div>

                        <button class="md:hidden p-2 text-slate-600" aria-label="Ouvrir le menu"
                            @click="isMenuOpen = !isMenuOpen">
                            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                                stroke-width="2">
                                <path v-if="!isMenuOpen" d="M4 6h16M4 12h16M4 18h16" stroke-linecap="round" />
                                <path v-else d="M6 6l12 12M18 6L6 18" stroke-linecap="round" />
                            </svg>
                        </button>
                    </div>

                    <div v-if="isMenuOpen" class="md:hidden pb-4 flex flex-col gap-1">
                        <a v-for="link in links" :key="link.href" :href="link.href"
                            class="px-3 py-2 text-sm font-medium text-slate-600 rounded-lg hover:bg-blue-50/60"
                            @click="isMenuOpen = false">
                            {{ link.label }}
                        </a>
                        <div class="flex gap-2 mt-2">
                            <button
                                class="flex-1 px-4 py-2 text-sm font-semibold text-slate-700 border border-slate-200 rounded-lg"
                                @click="openModal('login')">
                                Se connecter
                            </button>
                            <button
                                class="flex-1 px-4 py-2 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-cyan-500 rounded-lg"
                                @click="openModal('register')">
                                S'inscrire
                            </button>
                        </div>
                    </div>
                </div>
            </nav>
        </template>
