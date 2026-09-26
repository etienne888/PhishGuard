<script setup lang="ts">
/** Visitor scan: the analysis is done on the server; the result opens after sign-in. */
import AppIcon from '@/components/ui/AppIcon.vue'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'
import type { GatedScan } from '@/types'

defineProps<{ gate: GatedScan }>()
const auth = useAuthStore()
const { t } = useI18n()
</script>

<template>
  <section class="gate" aria-live="polite">
    <!-- Blurred preview of a result card: shows that something is waiting -->
    <div class="ghost" aria-hidden="true">
      <div class="h-14 w-14 rounded-2xl bg-slate-300/60"></div>
      <div class="flex-1 space-y-2">
        <div class="h-4 w-2/3 rounded-full bg-slate-300/70"></div>
        <div class="h-3 w-1/2 rounded-full bg-slate-300/50"></div>
        <div class="h-2.5 w-full rounded-full bg-slate-300/40"></div>
      </div>
    </div>

    <div class="relative z-10 flex flex-col items-center px-5 py-8 text-center sm:px-10">
      <span class="lock"><AppIcon name="lock" :size="26" /></span>
      <p class="mt-4 text-xs font-semibold uppercase tracking-[0.18em] text-blue-600 dark:text-cyan-300">{{ t('ux.gate.eyebrow') }}</p>
      <h3 class="mt-1 text-xl font-bold text-slate-800 dark:text-white sm:text-2xl font-display">{{ t('ux.gate.title') }}</h3>
      <p class="mt-2 max-w-md text-sm text-slate-600 dark:text-slate-300">{{ t('ux.gate.text', { checks: gate.checks }) }}</p>

      <ul class="mt-5 grid w-full max-w-lg gap-2 text-left sm:grid-cols-3">
        <li class="perk"><AppIcon name="shieldCheck" :size="18" class="text-emerald-600" /><span>{{ t('ux.gate.perk1') }}</span></li>
        <li class="perk"><AppIcon name="history" :size="18" class="text-blue-600" /><span>{{ t('ux.gate.perk2') }}</span></li>
        <li class="perk"><AppIcon name="bell" :size="18" class="text-violet-600" /><span>{{ t('ux.gate.perk3') }}</span></li>
      </ul>

      <div class="mt-6 flex w-full max-w-sm flex-col gap-2 sm:flex-row">
        <button class="btn-primary flex-1" @click="auth.openModal('login')">
          <AppIcon name="unlock" :size="18" /> {{ t('ux.gate.login') }}
        </button>
        <button class="btn-soft flex-1" @click="auth.openModal('register')">
          <AppIcon name="user" :size="18" /> {{ t('ux.gate.register') }}
        </button>
      </div>
      <p class="mt-3 flex items-center gap-1.5 text-xs text-slate-500"><AppIcon name="clock" :size="14" /> {{ t('ux.gate.kept') }}</p>

      <div class="tip">
        <AppIcon name="alert" :size="18" class="mt-0.5 text-amber-600" />
        <p>{{ gate.safetyTip }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.gate {
  position: relative;
  overflow: hidden;
  border-radius: 1.5rem;
  border: 1px solid rgba(37, 99, 235, 0.16);
  background:
    radial-gradient(120% 80% at 50% 0%, rgba(37, 99, 235, 0.10), transparent 60%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.9), rgba(241, 246, 255, 0.9));
}
:global(.dark) .gate { background: radial-gradient(120% 80% at 50% 0%, rgba(34, 211, 238, 0.12), transparent 60%), #0b1224; border-color: rgba(34, 211, 238, 0.2); }
.ghost {
  position: absolute;
  inset: 1.25rem 1.25rem auto;
  display: flex;
  gap: 1rem;
  filter: blur(6px);
  opacity: 0.55;
}
.lock {
  display: grid;
  place-items: center;
  width: 4rem;
  height: 4rem;
  border-radius: 1.4rem;
  color: white;
  background: linear-gradient(135deg, #2563eb, #06b6d4);
  box-shadow: 0 14px 30px -12px rgba(37, 99, 235, 0.7);
}
.perk {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  border-radius: 0.9rem;
  font-size: 0.78rem;
  color: #334155;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(148, 163, 184, 0.25);
}
:global(.dark) .perk { background: rgba(15, 23, 42, 0.7); color: #cbd5e1; }
.tip {
  margin-top: 1.5rem;
  display: flex;
  gap: 0.6rem;
  max-width: 32rem;
  padding: 0.8rem 1rem;
  border-radius: 1rem;
  text-align: left;
  font-size: 0.82rem;
  color: #92400e;
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(251, 191, 36, 0.35);
}
:global(.dark) .tip { color: #fcd34d; }
.btn-primary, .btn-soft {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border-radius: 0.95rem;
  font-size: 0.9rem;
  font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.2s ease;
}
.btn-primary { color: white; background: linear-gradient(135deg, #2563eb, #06b6d4); box-shadow: 0 10px 24px -10px rgba(37, 99, 235, 0.7); }
.btn-primary:hover { transform: translateY(-1px); }
.btn-soft { color: #1d4ed8; background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.2); }
:global(.dark) .btn-soft { color: #67e8f9; background: rgba(34, 211, 238, 0.08); border-color: rgba(34, 211, 238, 0.25); }
</style>
