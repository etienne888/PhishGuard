<script setup lang="ts">
/** Concrete next steps for the verdict, with the impersonated institution's official contact. */
import { computed } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import { useI18n } from '@/i18n'
import type { AnalysisResult } from '@/types'

const props = defineProps<{ result: AnalysisResult }>()
const { t } = useI18n()

interface Action { icon: IconName; key: string; tone: 'red' | 'amber' | 'blue' | 'green'; params?: Record<string, string> }

const hasLinks = computed(() => (props.result.urls?.length ?? 0) > 0 || /https?:\/\/|www\./i.test(props.result.text ?? ''))
const asksSecret = computed(() => /\b(pin|otp|code|mot de passe|password|cvv)\b/i.test(props.result.text ?? ''))
const official = computed(() => props.result.official ?? null)

const actions = computed<Action[]>(() => {
  const v = props.result.verdict
  const list: Action[] = []
  if (v === 'phishing') {
    if (hasLinks.value) list.push({ icon: 'ban', key: 'noClick', tone: 'red' })
    list.push({ icon: 'key', key: 'noSecret', tone: 'red' })
    list.push({ icon: 'trash', key: 'block', tone: 'amber' })
    list.push({ icon: 'shieldAlert', key: 'report', tone: 'blue' })
  } else if (v === 'suspicious') {
    list.push({ icon: 'hand', key: 'pause', tone: 'amber' })
    if (hasLinks.value) list.push({ icon: 'link', key: 'typeUrl', tone: 'amber' })
    if (asksSecret.value) list.push({ icon: 'key', key: 'noSecret', tone: 'red' })
    list.push({ icon: 'phone', key: 'verify', tone: 'blue' })
  } else {
    list.push({ icon: 'checkCircle', key: 'safe', tone: 'green' })
    list.push({ icon: 'key', key: 'stillSecret', tone: 'blue' })
  }
  return list
})

const clickedSteps = computed(() => props.result.verdict !== 'legitimate')
</script>

<template>
  <div>
    <ul class="grid gap-2.5 sm:grid-cols-2">
      <li v-for="a in actions" :key="a.key" class="action" :class="`tone-${a.tone}`">
        <span class="action-icon"><AppIcon :name="a.icon" :size="18" /></span>
        <span>
          <span class="block text-sm font-semibold">{{ t(`ux.todo.${a.key}.title`) }}</span>
          <span class="block text-xs opacity-80">{{ t(`ux.todo.${a.key}.text`) }}</span>
        </span>
      </li>
    </ul>

    <!-- Official channel of the imitated institution -->
    <div v-if="official && result.verdict !== 'legitimate'" class="official">
      <img v-if="official.logo_url" :src="official.logo_url" alt="" class="h-10 w-10 rounded-xl bg-white object-contain p-1 shadow-sm" loading="lazy" />
      <span v-else class="grid h-10 w-10 place-items-center rounded-xl bg-white text-blue-600 shadow-sm"><AppIcon name="shieldCheck" /></span>
      <div class="min-w-0 flex-1">
        <p class="text-xs font-semibold uppercase tracking-wide text-blue-700 dark:text-cyan-300">{{ t('ux.official.title', { institution: official.institution }) }}</p>
        <p class="text-sm text-slate-700 dark:text-slate-200">{{ t('ux.official.text', { institution: official.institution }) }}</p>
        <div class="mt-2 flex flex-wrap gap-2">
          <a v-if="official.support_contact && /^[+\d\s]+$/.test(official.support_contact)" :href="`tel:${official.support_contact.replace(/\s/g, '')}`" class="chip">
            <AppIcon name="phone" :size="14" /> {{ official.support_contact }}
          </a>
          <span v-else-if="official.support_contact" class="chip"><AppIcon name="phone" :size="14" /> {{ official.support_contact }}</span>
          <a v-if="official.website" :href="official.website" target="_blank" rel="noopener noreferrer" class="chip">
            <AppIcon name="globe" :size="14" /> {{ official.domain || official.website.replace(/^https?:\/\//, '') }}
          </a>
        </div>
      </div>
    </div>

    <details v-if="clickedSteps" class="clicked">
      <summary class="flex cursor-pointer items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
        <AppIcon name="alert" :size="16" class="text-red-500" /> {{ t('ux.clicked.title') }}
        <AppIcon name="chevronDown" :size="16" class="ml-auto opacity-60" />
      </summary>
      <ol class="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
        <li v-for="n in 4" :key="n" class="flex gap-2">
          <span class="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-red-100 text-[11px] font-bold text-red-700">{{ n }}</span>
          <span>{{ t(`ux.clicked.step${n}`) }}</span>
        </li>
      </ol>
    </details>
  </div>
</template>

<style scoped>
.action {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  padding: 0.8rem 0.9rem;
  border-radius: 1rem;
  border: 1px solid transparent;
}
.action-icon {
  display: grid;
  place-items: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 0.8rem;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.7);
}
:global(.dark) .action-icon { background: rgba(15, 23, 42, 0.6); }
.tone-red { background: rgba(239, 68, 68, 0.07); border-color: rgba(239, 68, 68, 0.18); color: #991b1b; }
.tone-amber { background: rgba(245, 158, 11, 0.08); border-color: rgba(245, 158, 11, 0.22); color: #92400e; }
.tone-blue { background: rgba(37, 99, 235, 0.06); border-color: rgba(37, 99, 235, 0.16); color: #1e3a8a; }
.tone-green { background: rgba(16, 185, 129, 0.07); border-color: rgba(16, 185, 129, 0.2); color: #065f46; }
:global(.dark) .tone-red { color: #fca5a5; }
:global(.dark) .tone-amber { color: #fcd34d; }
:global(.dark) .tone-blue { color: #93c5fd; }
:global(.dark) .tone-green { color: #6ee7b7; }
.official {
  margin-top: 0.9rem;
  display: flex;
  gap: 0.8rem;
  align-items: flex-start;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.07), rgba(6, 182, 212, 0.07));
  border: 1px solid rgba(37, 99, 235, 0.15);
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.3rem 0.7rem;
  border-radius: 9999px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #1d4ed8;
  background: white;
  border: 1px solid rgba(37, 99, 235, 0.2);
}
:global(.dark) .chip { background: #0f172a; color: #67e8f9; border-color: rgba(34, 211, 238, 0.3); }
.clicked {
  margin-top: 0.9rem;
  padding: 0.8rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(239, 68, 68, 0.18);
  background: rgba(254, 242, 242, 0.5);
}
:global(.dark) .clicked { background: rgba(127, 29, 29, 0.12); }
.clicked summary::-webkit-details-marker { display: none; }
</style>
