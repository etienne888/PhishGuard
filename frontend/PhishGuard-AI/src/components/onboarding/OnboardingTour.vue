<script setup lang="ts">
/** 3-screen welcome after the first sign-in: what PhishGuard does, how, and a first try with an example. */
import { computed, onMounted, ref } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import { experienceService } from '@/services/experience.service'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'

const emit = defineEmits<{ try: [text: string]; done: [] }>()
const auth = useAuthStore()
const { t } = useI18n()
const step = ref(0)
const dialog = ref<HTMLElement | null>(null)

const name = computed(() => (auth.user?.displayName || auth.user?.email || '').split(/[ @]/)[0] ?? '')

const SCREENS: Array<{ key: string; icon: IconName; points: Array<{ icon: IconName; key: string }> }> = [
  { key: 'welcome', icon: 'shieldCheck', points: [{ icon: 'message', key: 'sms' }, { icon: 'mail', key: 'email' }, { icon: 'smartphone', key: 'whatsapp' }] },
  { key: 'how', icon: 'radar', points: [{ icon: 'clipboard', key: 'paste' }, { icon: 'cpu', key: 'engines' }, { icon: 'hand', key: 'act' }] },
  { key: 'try', icon: 'sparkles', points: [{ icon: 'inbox', key: 'mailbox' }, { icon: 'graduation', key: 'learn' }, { icon: 'lock', key: 'private' }] },
]

async function finish(tryExample: boolean) {
  if (auth.user) auth.user = { ...auth.user, onboarded: true }
  void experienceService.markOnboarded().catch(() => undefined)
  if (tryExample) emit('try', t('analysis.example1.text'))
  emit('done')
}

onMounted(() => dialog.value?.focus())
</script>

<template>
  <div class="fixed inset-0 z-[70] grid place-items-center bg-slate-900/55 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" :aria-label="t('ux.onboarding.aria')"
       @keydown.esc="finish(false)">
    <div ref="dialog" tabindex="-1" class="tour">
      <div class="glow" aria-hidden="true"></div>
      <button class="absolute right-4 top-4 z-10 rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600" :aria-label="t('ux.onboarding.skip')" @click="finish(false)">
        <AppIcon name="x" :size="18" />
      </button>

      <Transition name="slide" mode="out-in">
        <div :key="step" class="relative px-6 pb-2 pt-8 text-center sm:px-10">
          <span class="hero-icon"><AppIcon :name="SCREENS[step]!.icon" :size="30" /></span>
          <h2 class="mt-5 text-2xl font-bold text-slate-800 dark:text-white font-display">{{ t(`ux.onboarding.${SCREENS[step]!.key}.title`, { name }) }}</h2>
          <p class="mx-auto mt-2 max-w-sm text-sm text-slate-600 dark:text-slate-300">{{ t(`ux.onboarding.${SCREENS[step]!.key}.text`) }}</p>
          <ul class="mt-6 grid gap-2 text-left">
            <li v-for="p in SCREENS[step]!.points" :key="p.key" class="point">
              <span class="point-icon"><AppIcon :name="p.icon" :size="17" /></span>
              <span class="text-sm text-slate-700 dark:text-slate-200">{{ t(`ux.onboarding.${SCREENS[step]!.key}.${p.key}`) }}</span>
            </li>
          </ul>
        </div>
      </Transition>

      <div class="flex items-center justify-between gap-3 px-6 pb-6 pt-4 sm:px-10">
        <div class="flex gap-1.5" aria-hidden="true">
          <span v-for="(_, i) in SCREENS" :key="i" class="h-1.5 rounded-full transition-all" :class="i === step ? 'w-6 bg-blue-600' : 'w-1.5 bg-slate-300'"></span>
        </div>
        <div class="flex gap-2">
          <button v-if="step > 0" class="ghost" @click="step--">{{ t('common.previous') }}</button>
          <button v-if="step < SCREENS.length - 1" class="primary" @click="step++">{{ t('common.next') }} <AppIcon name="arrowRight" :size="16" /></button>
          <button v-else class="primary" @click="finish(true)"><AppIcon name="play" :size="15" /> {{ t('ux.onboarding.tryExample') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tour { position: relative; width: 100%; max-width: 30rem; overflow: hidden; border-radius: 2rem; background: white; box-shadow: 0 40px 80px -30px rgba(15, 23, 42, 0.6); outline: none; }
:global(.dark) .tour { background: #0b1224; }
.glow { position: absolute; inset: -40% -20% auto; height: 16rem; background: radial-gradient(closest-side, rgba(37, 99, 235, 0.2), transparent); pointer-events: none; }
.hero-icon { display: inline-grid; place-items: center; width: 4.2rem; height: 4.2rem; border-radius: 1.5rem; color: white; background: linear-gradient(135deg, #2563eb, #06b6d4); box-shadow: 0 16px 32px -14px rgba(37, 99, 235, 0.8); }
.point { display: flex; align-items: center; gap: 0.75rem; padding: 0.65rem 0.8rem; border-radius: 1rem; background: rgba(148, 163, 184, 0.08); }
.point-icon { display: grid; place-items: center; width: 2.1rem; height: 2.1rem; border-radius: 0.75rem; color: #2563eb; background: rgba(37, 99, 235, 0.1); flex-shrink: 0; }
.primary, .ghost { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.6rem 1rem; border-radius: 0.9rem; font-size: 0.85rem; font-weight: 600; }
.primary { color: white; background: linear-gradient(135deg, #2563eb, #06b6d4); }
.ghost { color: #475569; background: rgba(148, 163, 184, 0.12); }
.slide-enter-active, .slide-leave-active { transition: all 0.25s ease; }
.slide-enter-from { opacity: 0; transform: translateX(16px); }
.slide-leave-to { opacity: 0; transform: translateX(-16px); }
@media (prefers-reduced-motion: reduce) { .slide-enter-active, .slide-leave-active { transition: none; } }
</style>
