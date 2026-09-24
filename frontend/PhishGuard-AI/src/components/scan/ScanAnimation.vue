<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

/**
 * Antivirus-style scanner shown while an analysis runs. The steps mirror the
 * real pipeline (backend/app/pipeline); they advance on a timer because the
 * backend answers in one response.
 */
const STEPS = [
  { label: 'Lecture du message', icon: '📨' },
  { label: 'Vérification des liens', icon: '🔗' },
  { label: "Contrôle de l'expéditeur", icon: '🏛️' },
  { label: 'Modèle anti-phishing', icon: '🧠' },
  { label: "Analyse par l'IA", icon: '🤖' },
  { label: 'Calcul du score final', icon: '⚖️' },
]

const active = ref(0)
let timer: number | undefined

onMounted(() => {
  // The AI step is the slow one: stop there until the result arrives
  timer = window.setInterval(() => {
    if (active.value < STEPS.length - 2) active.value++
  }, 700)
})
onBeforeUnmount(() => window.clearInterval(timer))
</script>

<template>
  <div class="scan-card" role="status" aria-live="polite">
    <div class="radar" aria-hidden="true">
      <span class="ring ring-1"></span>
      <span class="ring ring-2"></span>
      <span class="ring ring-3"></span>
      <span class="sweep"></span>
      <svg viewBox="0 0 24 24" class="shield" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    </div>

    <div class="flex-1 min-w-0">
      <p class="text-sm font-semibold text-cyan-200">Analyse en cours…</p>
      <ul class="mt-2 space-y-1.5">
        <li v-for="(step, index) in STEPS" :key="step.label" class="flex items-center gap-2 text-xs transition-colors"
            :class="index < active ? 'text-emerald-300' : index === active ? 'text-white' : 'text-slate-500'">
          <span class="w-4 text-center">
            <template v-if="index < active">✓</template>
            <span v-else-if="index === active" class="dot"></span>
            <template v-else>•</template>
          </span>
          <span>{{ step.icon }} {{ step.label }}</span>
        </li>
      </ul>
      <div class="mt-3 h-1 rounded-full bg-slate-700 overflow-hidden">
        <div class="h-full bg-cyan-400 transition-all duration-700" :style="{ width: ((active + 1) / STEPS.length) * 100 + '%' }"></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.scan-card {
  display: flex;
  gap: 1.25rem;
  align-items: center;
  padding: 1.25rem;
  border-radius: 1rem;
  background: radial-gradient(circle at 20% 30%, #0e3a4f 0%, #0f172a 70%);
  color: white;
}
.radar {
  position: relative;
  flex-shrink: 0;
  width: 96px;
  height: 96px;
  border-radius: 9999px;
  background: #06202b;
  overflow: hidden;
  box-shadow: 0 0 24px rgba(34, 211, 238, 0.25) inset;
}
.ring {
  position: absolute;
  inset: 0;
  margin: auto;
  border-radius: 9999px;
  border: 1px solid rgba(34, 211, 238, 0.25);
}
.ring-1 { width: 32%; height: 32%; }
.ring-2 { width: 64%; height: 64%; }
.ring-3 { width: 96%; height: 96%; }
.sweep {
  position: absolute;
  inset: 0;
  border-radius: 9999px;
  background: conic-gradient(from 0deg, rgba(34, 211, 238, 0.55), rgba(34, 211, 238, 0) 70deg);
  animation: sweep 1.6s linear infinite;
}
.shield {
  position: absolute;
  inset: 0;
  margin: auto;
  width: 34px;
  height: 34px;
  color: #67e8f9;
  animation: breathe 1.6s ease-in-out infinite;
}
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  background: #22d3ee;
  animation: blink 0.9s ease-in-out infinite;
}
@keyframes sweep { to { transform: rotate(360deg); } }
@keyframes breathe { 50% { transform: scale(1.12); opacity: 0.8; } }
@keyframes blink { 50% { opacity: 0.2; } }
@media (prefers-reduced-motion: reduce) {
  .sweep, .shield, .dot { animation: none; }
}
</style>
