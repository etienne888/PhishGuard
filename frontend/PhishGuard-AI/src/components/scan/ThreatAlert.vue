<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted } from 'vue'
import type { AnalysisResult } from '@/types'
import { useI18n } from '@/i18n'

/**
 * Full-screen verdict pop-up, antivirus style: red pulsing alarm for a threat,
 * amber for suspicious, green shield for a safe message.
 */
const props = defineProps<{ result: AnalysisResult }>()
const emit = defineEmits<{ close: []; details: [] }>()
const { t } = useI18n()

const tone = computed(() => ({
  phishing: {
    title: t('alert.phishing.title'),
    subtitle: t('alert.phishing.subtitle'),
    advice: t('alert.phishing.advice'),
    className: 'danger',
  },
  suspicious: {
    title: t('alert.suspicious.title'),
    subtitle: t('alert.suspicious.subtitle'),
    advice: t('alert.suspicious.advice'),
    className: 'warning',
  },
  legitimate: {
    title: t('alert.legitimate.title'),
    subtitle: t('alert.legitimate.subtitle'),
    advice: t('alert.legitimate.advice'),
    className: 'safe',
  },
}[props.result.verdict]))

function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape') emit('close')
}
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="overlay" :class="tone.className" role="alertdialog" aria-modal="true" :aria-label="tone.title" @click.self="emit('close')">
    <div class="card">
      <div class="icon-wrap" aria-hidden="true">
        <span class="pulse"></span>
        <span class="pulse delay"></span>
        <div class="icon">
          <svg v-if="result.verdict === 'legitimate'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" /><path d="M9 12l2 2 4-4" />
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" /><path d="M12 9v4M12 17h.01" />
          </svg>
        </div>
      </div>

      <h2 class="title">{{ tone.title }}</h2>
      <p class="score">{{ t('alert.score') }} <b>{{ Math.round(result.score) }}/100</b></p>
      <p class="text-slate-600 text-sm mt-2">{{ tone.subtitle }}</p>
      <p class="advice">{{ tone.advice }}</p>

      <div class="mt-5 flex flex-wrap justify-center gap-2">
        <button class="btn-primary" @click="emit('details')">{{ t('alert.explain') }}</button>
        <button class="btn-ghost" @click="emit('close')">{{ t('common.close') }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.55);
  backdrop-filter: blur(3px);
}
.overlay.danger { animation: flash 0.9s ease-in-out 3; }
.card {
  width: 100%;
  max-width: 26rem;
  padding: 2rem 1.5rem 1.5rem;
  border-radius: 1.25rem;
  background: white;
  text-align: center;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
  animation: pop 0.35s cubic-bezier(0.2, 0.9, 0.3, 1.3);
}
.danger .card { animation: pop 0.35s cubic-bezier(0.2, 0.9, 0.3, 1.3), shake 0.5s 0.35s; }
.icon-wrap { position: relative; width: 88px; height: 88px; margin: 0 auto; }
.icon {
  position: absolute; inset: 0; display: grid; place-items: center;
  border-radius: 9999px; color: white;
}
.icon svg { width: 44px; height: 44px; }
.pulse {
  position: absolute; inset: 0; border-radius: 9999px;
  animation: ripple 1.8s ease-out infinite;
}
.pulse.delay { animation-delay: 0.6s; }
.danger .icon, .danger .pulse { background: #dc2626; }
.warning .icon, .warning .pulse { background: #f59e0b; }
.safe .icon, .safe .pulse { background: #10b981; }
.title { margin-top: 1.25rem; font-size: 1.5rem; font-weight: 800; letter-spacing: 0.04em; }
.danger .title { color: #b91c1c; }
.warning .title { color: #b45309; }
.safe .title { color: #047857; }
.score { margin-top: 0.25rem; font-size: 0.9rem; color: #475569; }
.advice { margin-top: 0.75rem; font-size: 0.85rem; font-weight: 600; color: #0f172a; }
.btn-primary {
  padding: 0.6rem 1.2rem; border-radius: 0.75rem; font-weight: 600; font-size: 0.875rem;
  background: #0f172a; color: white;
}
.btn-ghost {
  padding: 0.6rem 1.2rem; border-radius: 0.75rem; font-size: 0.875rem; color: #475569;
  border: 1px solid #e2e8f0;
}
@keyframes ripple { from { transform: scale(1); opacity: 0.5; } to { transform: scale(1.9); opacity: 0; } }
@keyframes pop { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }
@keyframes shake {
  20%, 60% { transform: translateX(-8px); }
  40%, 80% { transform: translateX(8px); }
}
@keyframes flash { 50% { background: rgba(185, 28, 28, 0.45); } }
@media (prefers-reduced-motion: reduce) {
  .overlay.danger, .card, .danger .card, .pulse { animation: none; }
}
</style>
