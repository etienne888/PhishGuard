<template>
    <div class="min-h-screen bg-slate-50">
        <!-- Sidebar -->
        <aside
            class="fixed top-0 left-0 z-40 h-full w-64 bg-white border-r border-slate-200 shadow-lg transition-transform duration-300 ease-in-out"
            :class="isSidebarOpen ? 'translate-x-0' : '-translate-x-full'">
            <div class="flex flex-col h-full">
                <!-- Sidebar Header -->
                <div class="flex items-center gap-3 px-6 h-16 border-b border-slate-200">
                    <div
                        class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-md shadow-blue-500/25">
                        <i class="fas fa-shield-halved text-white text-sm"></i>
                    </div>
                    <span class="text-lg font-extrabold tracking-tight text-slate-800">
                        Phish<span class="text-blue-600">Guard</span><span class="text-cyan-500">-AI</span>
                    </span>
                    <span
                        class="ml-1 text-[10px] font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">Admin</span>
                </div>

                <!-- Navigation -->
                <nav class="flex-1 px-3 py-4 overflow-y-auto">
                    <div class="space-y-1">
                        <router-link v-for="item in navItems" :key="item.path" :to="item.path"
                            class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200"
                            :class="isActive(item.path) ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800'">
                            <span class="text-lg">{{ item.icon }}</span>
                            {{ item.label }}
                            <span v-if="item.badge"
                                class="ml-auto text-[10px] font-semibold bg-red-500 text-white px-2 py-0.5 rounded-full">
                                {{ item.badge }}
                            </span>
                        </router-link>
                    </div>

                    <!-- Bottom: Logout -->
                    <div class="pt-4 mt-4 border-t border-slate-200">
                        <button @click="handleLogout"
                            class="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-all duration-200">
                            <span class="text-lg">🚪</span>
                            Déconnexion
                        </button>
                    </div>
                </nav>
            </div>
        </aside>

        <!-- Mobile Overlay -->
        <div v-if="isSidebarOpen" class="fixed inset-0 z-30 bg-slate-900/50 backdrop-blur-sm lg:hidden"
            @click="isSidebarOpen = false"></div>

        <!-- Main Content -->
        <div class="lg:ml-64">
            <!-- Mobile Toggle -->
            <div class="lg:hidden fixed top-4 left-4 z-20">
                <button @click="isSidebarOpen = !isSidebarOpen"
                    class="p-2.5 bg-white rounded-xl shadow-lg border border-slate-200 hover:bg-slate-50 transition">
                    <svg class="w-5 h-5 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                            d="M4 6h16M4 12h16M4 18h16" />
                    </svg>
                </button>
            </div>

            <!-- Page Content -->
            <main class="pt-28 pb-16 px-4">
                <div class="max-w-7xl mx-auto">
                    <router-view />
                </div>
            </main>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '@/composables'

const route = useRoute()
const router = useRouter()
const { logout } = useAuth()
const isSidebarOpen = ref(false)

const navItems = [
    { path: '/admin', label: 'Aperçu', icon: '📊' },
    { path: '/admin/users', label: 'Utilisateurs', icon: '👥' },
    { path: '/admin/reports', label: 'Signalements', icon: '🚨', badge: '12' },
    { path: '/admin/threat-intel', label: 'Menaces & Catégories', icon: '🧠' },
    { path: '/admin/models', label: 'Modèles ML', icon: '🤖' },
    { path: '/admin/audit', label: 'Audit', icon: '📜' },
    { path: '/admin/settings', label: 'Paramètres', icon: '⚙️' },
]

const isActive = (path: string) => {
    return route.path === path || route.path.startsWith(path + '/')
}

const handleLogout = async () => {
    await logout()
    router.push({ name: 'home' })
}
</script>