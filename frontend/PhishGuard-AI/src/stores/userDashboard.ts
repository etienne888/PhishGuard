import { defineStore } from 'pinia'
import { ref } from 'vue'
import {
  userDashboardService,
  type DashboardActivity,
  type DashboardMessage,
  type DashboardOverview,
  type DashboardTimelineItem,
  type ScoreReason,
} from '@/services/userDashboard.service'

const CACHE_DURATION_MS = 30_000

export const useUserDashboardStore = defineStore('userDashboard', () => {
  const overview = ref<DashboardOverview | null>(null)
  const messages = ref<DashboardMessage[]>([])
  const messagesTotal = ref(0)
  const activities = ref<DashboardActivity[]>([])
  const timeline = ref<DashboardTimelineItem[]>([])
  const score = ref<number | null>(null)
  const scoreReasons = ref<ScoreReason[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastFetched = ref<number | null>(null)
  let activeRequest: Promise<void> | null = null

  async function load(range = 'today', force = false) {
    const isFresh = lastFetched.value !== null && Date.now() - lastFetched.value < CACHE_DURATION_MS
    if (!force && isFresh) return
    if (activeRequest) return activeRequest

    isLoading.value = true
    error.value = null
    activeRequest = Promise.all([
      userDashboardService.getOverview(),
      userDashboardService.getRecentMessages(),
      userDashboardService.getActivity(),
      userDashboardService.getTimeline(range),
      userDashboardService.getScoreBreakdown(),
    ]).then(([nextOverview, recentMessages, recentActivity, nextTimeline, breakdown]) => {
      overview.value = nextOverview
      messages.value = recentMessages.items
      messagesTotal.value = recentMessages.total
      activities.value = recentActivity.items
      timeline.value = nextTimeline.items
      score.value = breakdown.score
      scoreReasons.value = breakdown.reasons
      lastFetched.value = Date.now()
    }).catch((caught: unknown) => {
      error.value = caught instanceof Error ? caught.message : 'Impossible de charger le tableau de bord.'
    }).finally(() => {
      isLoading.value = false
      activeRequest = null
    })

    return activeRequest
  }

  async function changeRange(range: string) {
    const result = await userDashboardService.getTimeline(range)
    timeline.value = result.items
  }

  async function reportMessage(id: number) {
    const result = await userDashboardService.reportMessage(id)
    const message = messages.value.find((item) => item.id === id)
    if (message) message.reported_at = result.reported_at
    await load('today', true)
  }

  async function checkSecurity() {
    return userDashboardService.checkSecurity()
  }

  return {
    overview,
    messages,
    messagesTotal,
    activities,
    timeline,
    score,
    scoreReasons,
    isLoading,
    error,
    lastFetched,
    load,
    changeRange,
    reportMessage,
    checkSecurity,
  }
})
