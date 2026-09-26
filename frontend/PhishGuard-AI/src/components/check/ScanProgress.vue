<script setup lang="ts">
/**
 * The analysis steps, shown while the server works. The pipeline runs them in
 * parallel; steps light up in order so the user sees what is being checked,
 * and all turn green when the answer arrives.
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import { useI18n } from '@/i18n'

const { t } = useI18n()

const STEPS: Array<{ key: string; icon: IconName }> = [
  { key: 'read', icon: 'file' },
  { key: 'sender', icon: 'user' },
  { key: 'links', icon: 'link' },
  { key: 'ai', icon: 'brain' },
  { key: 'verdict', icon: 'gauge' },
]

const active = ref(0)
let timer: number | undefined

onMounted(() => {
  timer = window.setInterval(() => {
    // The last step stays "in progress" until the result is in
    if (active.value < STEPS.length - 1) active.value += 1
  }, 750)
})
onBeforeUnmount(() => window.clearInterval(timer))
</script>

<template>
  <div class="progress-card" role="status" aria-live="polite">
    <div class="mb-4 flex items-center gap-3">
      <span class="radar"><AppIcon name="radar" :size="22" /></span>
      <div>
        <p class="text-sm font-semibold text-slate-800 dark:text-white">{{ t('ux.progress.title') }}</p>
        <p class="text-xs text-slate-500">{{ t('ux.progress.subtitle') }}</p>
      </div>
    </div>
    <ol class="grid gap-2 sm:grid-cols-5">
      <li v-for="(step, i) in STEPS" :key="step.key" class="step" :class="i < active ? 'done' : i === active ? 'current' : 'todo'">
        <span class="step-icon">
          <AppIcon :name="i < active ? 'check' : step.icon" :size="16" />
        </span>
        <span class="text-xs font-medium leading-tight">{{ t(`ux.progress.${step.key}`) }}</span>
      </li>
    </ol>
  </div>
</template>

<style scoped>
.progress-card {
  border-radius: 1.25rem;
  padding: 1.1rem 1.1rem 1.2rem;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.06), rgba(6, 182, 212, 0.07));
  border: 1px solid rgba(37, 99, 235, 0.14);
}
.radar {
  display: grid;
  place-items: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px;
  color: #2563eb;
  background: rgba(37, 99, 235, 0.1);
  animation: pulse 1.6s ease-in-out infinite;
}
.step {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0.55rem 0.65rem;
  border-radius: 0.9rem;
  transition: all 0.3s ease;
}
.step-icon {
  display: grid;
  place-items: center;
  width: 1.9rem;
  height: 1.9rem;
  border-radius: 0.7rem;
  flex-shrink: 0;
  transition: all 0.3s ease;
}
.todo { color: #94a3b8; }
.todo .step-icon { background: rgba(148, 163, 184, 0.12); }
.current { color: #1d4ed8; background: rgba(255, 255, 255, 0.7); box-shadow: 0 4px 14px -6px rgba(37, 99, 235, 0.35); }
.current .step-icon { background: #2563eb; color: white; animation: pulse 1.2s ease-in-out infinite; }
.done { color: #047857; }
.done .step-icon { background: rgba(16, 185, 129, 0.14); }
:global(.dark) .current { background: rgba(30, 41, 59, 0.8); color: #93c5fd; }
@keyframes pulse { 50% { box-shadow: 0 0 0 6px rgba(37, 99, 235, 0.12); } }
@media (prefers-reduced-motion: reduce) { .radar, .current .step-icon { animation: none; } }
</style>
