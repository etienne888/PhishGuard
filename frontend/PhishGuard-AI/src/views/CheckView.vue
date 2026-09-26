<script setup lang="ts">
/**
 * /check — the checker on its own page. Also the target of:
 *   ?text=&url=&title=  "Share to PhishGuard" from WhatsApp/SMS (installed app, manifest share_target)
 *   ?claim=<token>      "sign in to see the result" links sent by email
 *   ?analysis=<id>      a past result (links in verdict emails)
 */
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import Footer from '@/components/Footer.vue'
import Analyzer from '@/components/Analyzer.vue'
import PublicTabBar from '@/components/PublicTabBar.vue'
import CommunityAlerts from '@/components/CommunityAlerts.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { useAnalysisStore } from '@/stores/analysis'
import { useAuthStore } from '@/stores/auth'
import { authService } from '@/services/auth.service'
import { useI18n } from '@/i18n'

const route = useRoute()
const router = useRouter()
const store = useAnalysisStore()
const auth = useAuthStore()
const { t } = useI18n()
const analyzer = ref<InstanceType<typeof Analyzer> | null>(null)

const query = (key: string) => (typeof route.query[key] === 'string' ? (route.query[key] as string) : '')

// Before the Analyzer mounts, so it claims the scan as soon as the user is signed in
const claimToken = query('claim')
if (claimToken) store.rememberClaim(claimToken)
const analysisId = Number(query('analysis')) || null

onMounted(async () => {
  const user = auth.user ?? await authService.me()
  if (user && !auth.user) auth.setUser(user)

  const shared = [query('title'), query('text'), query('url')].filter(Boolean).join('\n').trim()
  if (shared) {
    await router.replace({ query: {} })
    await analyzer.value?.run(shared, 'share')
    return
  }
  if (claimToken || analysisId) {
    await router.replace({ query: {} })
    if (!user) {
      auth.openModal('login')
    } else if (analysisId) {
      await store.open(analysisId)
    }
  }
})

// Signed in after following an analysis link
watch(() => auth.user, (user) => { if (user && analysisId && !store.result) void store.open(analysisId) })

const STEPS = [
  { icon: 'clipboard' as const, key: 'paste' },
  { icon: 'radar' as const, key: 'scan' },
  { icon: 'hand' as const, key: 'act' },
]
</script>

<template>
  <div class="min-h-screen bg-slate-50 pb-20 dark:bg-slate-950 md:pb-0">
    <Navbar />
    <main class="px-4 pt-24">
      <div class="mx-auto max-w-4xl">
        <ol class="mb-2 grid grid-cols-3 gap-2 sm:gap-4">
          <li v-for="(s, i) in STEPS" :key="s.key" class="flex items-center gap-2 rounded-2xl bg-white/70 px-3 py-2.5 text-xs text-slate-600 ring-1 ring-slate-200 dark:bg-slate-900/60 dark:text-slate-300 dark:ring-slate-800 sm:text-sm">
            <span class="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-blue-600/10 text-blue-600 dark:text-cyan-300"><AppIcon :name="s.icon" :size="17" /></span>
            <span><b class="text-slate-800 dark:text-white">{{ i + 1 }}.</b> {{ t(`ux.check.step.${s.key}`) }}</span>
          </li>
        </ol>
      </div>
      <Analyzer ref="analyzer" />
      <div class="mx-auto mb-16 max-w-4xl">
        <CommunityAlerts compact />
      </div>
    </main>
    <Footer />
    <PublicTabBar />
  </div>
</template>
