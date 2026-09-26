<script setup lang="ts">
/**
 * /learn — "Real or fake?" quiz with levels and badges, plus the golden rules.
 * Signed-in users earn XP (saved on the server); visitors can play without saving.
 */
import { computed, onMounted, ref } from 'vue'
import Navbar from '@/components/Navbar.vue'
import Footer from '@/components/Footer.vue'
import PublicTabBar from '@/components/PublicTabBar.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import HighlightedMessage from '@/components/check/HighlightedMessage.vue'
import { GOLDEN_RULES, LEVELS, QUIZ, type QuizItem } from '@/data/quiz'
import { experienceService, type QuizLevel } from '@/services/experience.service'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'

const auth = useAuthStore()
const { t } = useI18n()

// A fresh order every round
const deck = ref<QuizItem[]>([])
const index = ref(0)
const answer = ref<'fake' | 'real' | null>(null)
const correctCount = ref(0)
const level = ref<QuizLevel | null>(null)
const finished = ref(false)

function shuffle() {
  deck.value = [...QUIZ].sort(() => Math.random() - 0.5)
  index.value = 0
  answer.value = null
  correctCount.value = 0
  finished.value = false
}

const item = computed(() => deck.value[index.value])
const isRight = computed(() => answer.value !== null && answer.value === item.value?.answer)

async function choose(choice: 'fake' | 'real') {
  if (answer.value || !item.value) return
  answer.value = choice
  const correct = choice === item.value.answer
  if (correct) correctCount.value += 1
  if (auth.user) {
    try { level.value = (await experienceService.answerQuiz(correct)).level } catch { /* offline: keep playing */ }
  }
}

function next() {
  if (index.value >= deck.value.length - 1) {
    finished.value = true
    return
  }
  index.value += 1
  answer.value = null
}

const levelInfo = computed(() => {
  const xp = level.value?.xp ?? 0
  const current = [...LEVELS].reverse().find((l) => xp >= l.floor) ?? LEVELS[0]!
  const following = LEVELS.find((l) => l.floor > xp)
  const pct = following ? Math.round(((xp - current.floor) / (following.floor - current.floor)) * 100) : 100
  return { xp, current, following, pct }
})

const CHANNEL_ICON = { sms: 'message', whatsapp: 'smartphone', email: 'mail' } as const

onMounted(async () => {
  shuffle()
  if (auth.user) {
    try { level.value = (await experienceService.summary()).quiz.level } catch { /* not critical */ }
  }
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 pb-20 dark:bg-slate-950 md:pb-0">
    <Navbar />
    <main class="mx-auto max-w-5xl px-4 pb-16 pt-24">
      <header class="text-center">
        <span class="inline-flex items-center gap-2 rounded-full border border-violet-200 bg-violet-50 px-3 py-1 text-xs font-semibold text-violet-700 dark:border-violet-400/30 dark:bg-violet-400/10 dark:text-violet-300">
          <AppIcon name="graduation" :size="14" /> {{ t('ux.learn.badge') }}
        </span>
        <h1 class="mt-3 text-3xl font-bold text-slate-800 dark:text-white sm:text-4xl font-display">{{ t('ux.learn.title') }}</h1>
        <p class="mx-auto mt-2 max-w-xl text-slate-500">{{ t('ux.learn.subtitle') }}</p>
      </header>

      <div class="mt-8 grid gap-6 lg:grid-cols-3">
        <!-- Quiz -->
        <section class="quiz lg:col-span-2">
          <div class="mb-4 flex items-center justify-between">
            <div class="flex gap-1" :aria-label="t('ux.learn.progress', { n: index + 1, total: deck.length })">
              <span v-for="(_, i) in deck" :key="i" class="h-1.5 w-5 rounded-full transition-colors"
                    :class="i < index || (i === index && answer) ? 'bg-blue-500' : i === index ? 'bg-blue-300' : 'bg-slate-200 dark:bg-slate-700'"></span>
            </div>
            <span class="text-xs font-semibold text-slate-500">{{ t('ux.learn.score', { n: correctCount }) }}</span>
          </div>

          <!-- End of round -->
          <div v-if="finished" class="py-8 text-center">
            <span class="mx-auto grid h-16 w-16 place-items-center rounded-3xl bg-gradient-to-br from-amber-400 to-orange-500 text-white shadow-lg"><AppIcon name="trophy" :size="30" /></span>
            <h2 class="mt-4 text-2xl font-bold text-slate-800 dark:text-white">{{ t('ux.learn.done', { n: correctCount, total: deck.length }) }}</h2>
            <p class="mt-1 text-slate-500">{{ correctCount >= 8 ? t('ux.learn.doneGreat') : correctCount >= 5 ? t('ux.learn.doneGood') : t('ux.learn.doneRetry') }}</p>
            <button class="btn mt-6" @click="shuffle"><AppIcon name="refresh" :size="17" /> {{ t('ux.learn.again') }}</button>
          </div>

          <template v-else-if="item">
            <!-- The message, as it would appear on a phone -->
            <div class="phone">
              <div class="flex items-center gap-2 border-b border-slate-200/70 pb-2 dark:border-slate-700">
                <span class="grid h-8 w-8 place-items-center rounded-full bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-300"><AppIcon :name="CHANNEL_ICON[item.channel]" :size="16" /></span>
                <div>
                  <p class="text-sm font-semibold text-slate-800 dark:text-white">{{ item.sender }}</p>
                  <p class="text-[11px] uppercase tracking-wide text-slate-400">{{ t(`ux.learn.channel.${item.channel}`) }}</p>
                </div>
              </div>
              <div v-if="!answer" class="bubble">{{ t(`ux.quiz.q${item.id}.text`) }}</div>
              <HighlightedMessage v-else class="mt-3" :text="t(`ux.quiz.q${item.id}.text`)" />
            </div>

            <div v-if="!answer" class="mt-5 grid grid-cols-2 gap-3">
              <button class="choice fake" @click="choose('fake')"><AppIcon name="shieldAlert" :size="22" /> {{ t('ux.learn.fake') }}</button>
              <button class="choice real" @click="choose('real')"><AppIcon name="shieldCheck" :size="22" /> {{ t('ux.learn.real') }}</button>
            </div>

            <div v-else class="mt-5" aria-live="polite">
              <div class="verdict" :class="isRight ? 'ok' : 'ko'">
                <AppIcon :name="isRight ? 'checkCircle' : 'xCircle'" :size="22" />
                <div>
                  <p class="font-semibold">{{ isRight ? t('ux.learn.right') : t('ux.learn.wrong') }} — {{ item.answer === 'fake' ? t('ux.learn.itWasFake') : t('ux.learn.itWasReal') }}</p>
                  <p class="mt-1 text-sm opacity-90">{{ t(`ux.quiz.q${item.id}.why`) }}</p>
                  <p v-if="auth.user" class="mt-1 text-xs font-semibold opacity-80">+{{ isRight ? 10 : 2 }} XP</p>
                </div>
              </div>
              <button class="btn mt-4 w-full sm:w-auto" @click="next">
                {{ index >= deck.length - 1 ? t('ux.learn.finish') : t('ux.learn.next') }} <AppIcon name="arrowRight" :size="17" />
              </button>
            </div>
          </template>
        </section>

        <!-- Level + rules -->
        <aside class="space-y-4">
          <section class="card">
            <template v-if="auth.user">
              <div class="flex items-center gap-3">
                <span class="grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-violet-500 to-blue-500 text-white"><AppIcon :name="levelInfo.current.icon" :size="24" /></span>
                <div>
                  <p class="text-xs text-slate-500">{{ t('ux.learn.yourLevel') }}</p>
                  <p class="text-lg font-bold text-slate-800 dark:text-white">{{ t(`ux.level.${levelInfo.current.key}`) }}</p>
                </div>
                <span class="ml-auto text-sm font-bold tabular-nums text-violet-600">{{ levelInfo.xp }} XP</span>
              </div>
              <div class="mt-3 h-2 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"><div class="h-full rounded-full bg-gradient-to-r from-violet-500 to-blue-500 transition-all" :style="{ width: levelInfo.pct + '%' }"></div></div>
              <p v-if="levelInfo.following" class="mt-1.5 text-xs text-slate-500">{{ t('ux.learn.toNext', { xp: levelInfo.following.floor - levelInfo.xp, level: t(`ux.level.${levelInfo.following.key}`) }) }}</p>
              <div class="mt-4 flex justify-between">
                <span v-for="l in LEVELS" :key="l.key" class="badge" :class="levelInfo.xp >= l.floor ? 'on' : ''" :title="t(`ux.level.${l.key}`)">
                  <AppIcon :name="l.icon" :size="16" />
                </span>
              </div>
            </template>
            <template v-else>
              <p class="flex items-center gap-2 font-semibold text-slate-800 dark:text-white"><AppIcon name="trophy" :size="18" class="text-amber-500" /> {{ t('ux.learn.saveTitle') }}</p>
              <p class="mt-1 text-sm text-slate-500">{{ t('ux.learn.saveText') }}</p>
              <button class="btn mt-3 w-full" @click="auth.openModal('register')"><AppIcon name="user" :size="16" /> {{ t('ux.gate.register') }}</button>
            </template>
          </section>

          <section class="card">
            <h2 class="mb-3 flex items-center gap-2 font-semibold text-slate-800 dark:text-white"><AppIcon name="star" :size="18" class="text-amber-500" /> {{ t('ux.rules.title') }}</h2>
            <ul class="space-y-2.5">
              <li v-for="r in GOLDEN_RULES" :key="r.key" class="flex gap-2.5">
                <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-blue-50 text-blue-600 dark:bg-blue-500/10 dark:text-cyan-300"><AppIcon :name="r.icon" :size="16" /></span>
                <span class="text-sm text-slate-600 dark:text-slate-300">{{ t(`ux.rules.${r.key}`) }}</span>
              </li>
            </ul>
          </section>
        </aside>
      </div>
    </main>
    <Footer />
    <PublicTabBar />
  </div>
</template>

<style scoped>
.quiz, .card { padding: 1.3rem; border-radius: 1.6rem; background: white; border: 1px solid rgba(148, 163, 184, 0.22); box-shadow: 0 24px 50px -40px rgba(30, 64, 175, 0.5); }
:global(.dark) .quiz, :global(.dark) .card { background: #0b1224; border-color: #1e293b; }
.phone { max-width: 32rem; margin: 0 auto; padding: 1rem; border-radius: 1.5rem; background: #f1f5f9; border: 1px solid rgba(148, 163, 184, 0.3); }
:global(.dark) .phone { background: #020617; border-color: #1e293b; }
.bubble { margin-top: 0.9rem; padding: 0.85rem 1rem; border-radius: 1.1rem 1.1rem 1.1rem 0.3rem; background: white; font-size: 0.92rem; line-height: 1.6; color: #1e293b; white-space: pre-wrap; box-shadow: 0 4px 12px -8px rgba(15, 23, 42, 0.3); }
:global(.dark) .bubble { background: #1e293b; color: #e2e8f0; }
.choice { display: flex; flex-direction: column; align-items: center; gap: 0.4rem; padding: 1rem; border-radius: 1.2rem; font-weight: 700; transition: transform 0.15s ease, box-shadow 0.2s ease; }
.choice:hover { transform: translateY(-2px); }
.choice.fake { color: #b91c1c; background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.25); }
.choice.real { color: #047857; background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); }
.verdict { display: flex; gap: 0.75rem; padding: 1rem; border-radius: 1.2rem; }
.verdict.ok { color: #065f46; background: rgba(16, 185, 129, 0.1); }
.verdict.ko { color: #9f1239; background: rgba(244, 63, 94, 0.08); }
:global(.dark) .verdict.ok { color: #6ee7b7; }
:global(.dark) .verdict.ko { color: #fda4af; }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 0.45rem; padding: 0.7rem 1.2rem; border-radius: 0.95rem; font-weight: 600; font-size: 0.9rem; color: white; background: linear-gradient(135deg, #2563eb, #06b6d4); box-shadow: 0 12px 24px -12px rgba(37, 99, 235, 0.8); }
.badge { display: grid; place-items: center; width: 2.3rem; height: 2.3rem; border-radius: 0.8rem; color: #94a3b8; background: rgba(148, 163, 184, 0.12); }
.badge.on { color: white; background: linear-gradient(135deg, #8b5cf6, #3b82f6); }
</style>
