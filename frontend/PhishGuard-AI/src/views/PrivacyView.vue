<script setup lang="ts">
/** /privacy — what PhishGuard stores, why, for how long, and one-click history deletion. */
import { ref } from 'vue'
import Navbar from '@/components/Navbar.vue'
import Footer from '@/components/Footer.vue'
import PublicTabBar from '@/components/PublicTabBar.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import { experienceService } from '@/services/experience.service'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores'
import { useI18n } from '@/i18n'

const auth = useAuthStore()
const toast = useNotificationsStore()
const { t } = useI18n()

const SECTIONS: Array<{ key: string; icon: IconName }> = [
  { key: 'collect', icon: 'file' },
  { key: 'why', icon: 'target' },
  { key: 'mailbox', icon: 'inbox' },
  { key: 'share', icon: 'users' },
  { key: 'keep', icon: 'clock' },
  { key: 'security', icon: 'lock' },
]

const confirming = ref(false)
const deleting = ref(false)

async function deleteHistory() {
  deleting.value = true
  try {
    const { deleted } = await experienceService.deleteHistory()
    toast.push(t('ux.privacy.deleted', { n: deleted }), 'success')
    confirming.value = false
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 pb-20 dark:bg-slate-950 md:pb-0">
    <Navbar />
    <main class="mx-auto max-w-4xl px-4 pb-16 pt-24">
      <header class="flex flex-col items-center text-center">
        <span class="grid h-16 w-16 place-items-center rounded-3xl bg-gradient-to-br from-emerald-500 to-cyan-500 text-white shadow-lg"><AppIcon name="lock" :size="30" /></span>
        <h1 class="mt-4 text-3xl font-bold text-slate-800 dark:text-white font-display">{{ t('ux.privacy.title') }}</h1>
        <p class="mt-2 max-w-xl text-slate-500">{{ t('ux.privacy.subtitle') }}</p>
      </header>

      <div class="mt-8 grid gap-4 sm:grid-cols-2">
        <section v-for="s in SECTIONS" :key="s.key" class="card">
          <span class="icon"><AppIcon :name="s.icon" :size="18" /></span>
          <h2 class="mt-3 font-semibold text-slate-800 dark:text-white">{{ t(`ux.privacy.${s.key}.title`) }}</h2>
          <p class="mt-1 text-sm leading-relaxed text-slate-600 dark:text-slate-300">{{ t(`ux.privacy.${s.key}.text`) }}</p>
        </section>
      </div>

      <section class="danger mt-6">
        <span class="icon red"><AppIcon name="trash" :size="18" /></span>
        <div class="flex-1">
          <h2 class="font-semibold text-slate-800 dark:text-white">{{ t('ux.privacy.deleteTitle') }}</h2>
          <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">{{ t('ux.privacy.deleteText') }}</p>
          <div class="mt-3">
            <button v-if="!auth.user" class="btn-soft" @click="auth.openModal('login')"><AppIcon name="user" :size="15" /> {{ t('ux.gate.login') }}</button>
            <button v-else-if="!confirming" class="btn-red" @click="confirming = true"><AppIcon name="trash" :size="15" /> {{ t('ux.privacy.deleteButton') }}</button>
            <div v-else class="flex flex-wrap items-center gap-2">
              <span class="text-sm font-semibold text-red-700">{{ t('ux.privacy.deleteConfirm') }}</span>
              <button class="btn-red" :disabled="deleting" @click="deleteHistory"><AppIcon name="check" :size="15" /> {{ t('ux.privacy.deleteYes') }}</button>
              <button class="btn-soft" @click="confirming = false">{{ t('common.cancel') }}</button>
            </div>
          </div>
        </div>
      </section>

      <p class="mt-6 flex items-start gap-2 text-sm text-slate-500"><AppIcon name="mail" :size="16" class="mt-0.5" /> {{ t('ux.privacy.contact') }}</p>
    </main>
    <Footer />
    <PublicTabBar />
  </div>
</template>

<style scoped>
.card { padding: 1.2rem; border-radius: 1.4rem; background: white; border: 1px solid rgba(148, 163, 184, 0.22); }
:global(.dark) .card, :global(.dark) .danger { background: #0b1224; border-color: #1e293b; }
.icon { display: grid; place-items: center; width: 2.4rem; height: 2.4rem; border-radius: 0.85rem; color: #059669; background: rgba(16, 185, 129, 0.1); flex-shrink: 0; }
.icon.red { color: #dc2626; background: rgba(239, 68, 68, 0.1); }
.danger { display: flex; gap: 0.9rem; padding: 1.2rem; border-radius: 1.4rem; background: white; border: 1px solid rgba(239, 68, 68, 0.2); }
.btn-red, .btn-soft { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.55rem 0.95rem; border-radius: 0.85rem; font-size: 0.85rem; font-weight: 600; }
.btn-red { color: white; background: #dc2626; }
.btn-red:disabled { opacity: 0.6; }
.btn-soft { color: #334155; background: rgba(148, 163, 184, 0.15); }
:global(.dark) .btn-soft { color: #cbd5e1; }
</style>
