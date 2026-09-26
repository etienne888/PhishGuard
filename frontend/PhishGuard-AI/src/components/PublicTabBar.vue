<script setup lang="ts">
/** Bottom navigation on phones for the public pages (the dashboard has its own). */
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'

const route = useRoute()
const auth = useAuthStore()
const { t } = useI18n()

const items = computed<Array<{ key: string; icon: IconName; to: string }>>(() => [
  { key: 'home', icon: 'home', to: '/' },
  { key: 'check', icon: 'shieldCheck', to: '/check' },
  { key: 'learn', icon: 'graduation', to: '/learn' },
  { key: 'alerts', icon: 'radar', to: '/#alerts' },
  { key: 'account', icon: 'user', to: auth.user ? '/dashboard' : '' },
])

function active(to: string) {
  return !!to && (to === '/' ? route.path === '/' && !route.hash : route.fullPath === to || route.path === to)
}
</script>

<template>
  <nav class="tabbar md:hidden" :aria-label="t('ux.tabs.aria')">
    <template v-for="item in items" :key="item.key">
      <RouterLink v-if="item.to" :to="item.to" class="tab" :class="{ on: active(item.to) }" :aria-current="active(item.to) ? 'page' : undefined">
        <span class="tab-icon" :class="{ main: item.key === 'check' }"><AppIcon :name="item.icon" :size="item.key === 'check' ? 22 : 20" /></span>
        <span>{{ t(`ux.tabs.${item.key}`) }}</span>
      </RouterLink>
      <button v-else class="tab" @click="auth.openModal('login')">
        <span class="tab-icon"><AppIcon :name="item.icon" :size="20" /></span>
        <span>{{ t('ux.tabs.login') }}</span>
      </button>
    </template>
  </nav>
</template>

<style scoped>
.tabbar {
  position: fixed; left: 0; right: 0; bottom: 0; z-index: 40;
  display: grid; grid-template-columns: repeat(5, 1fr);
  padding: 0.35rem 0.25rem calc(0.35rem + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.92); backdrop-filter: blur(14px);
  border-top: 1px solid rgba(148, 163, 184, 0.25);
}
:global(.dark) .tabbar { background: rgba(2, 6, 23, 0.92); border-color: #1e293b; }
.tab { display: flex; flex-direction: column; align-items: center; gap: 0.1rem; padding: 0.2rem 0; font-size: 0.66rem; font-weight: 600; color: #64748b; min-height: 44px; }
.tab.on { color: #2563eb; }
:global(.dark) .tab.on { color: #67e8f9; }
.tab-icon { display: grid; place-items: center; width: 2.2rem; height: 1.7rem; border-radius: 9999px; transition: background 0.2s ease; }
.tab.on .tab-icon { background: rgba(37, 99, 235, 0.1); }
.tab-icon.main { width: 2.6rem; height: 2.6rem; margin-top: -1.1rem; color: white; background: linear-gradient(135deg, #2563eb, #06b6d4); box-shadow: 0 10px 20px -8px rgba(37, 99, 235, 0.7); }
</style>
