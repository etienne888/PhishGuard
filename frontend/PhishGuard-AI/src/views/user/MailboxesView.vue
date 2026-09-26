<script setup lang="ts">
/**
 * /dashboard/mailboxes — connect Gmail / Outlook (OAuth, read-only by default),
 * see what was scanned, pause or disconnect; or use the forwarding address.
 */
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Navbar from '@/components/Navbar.vue'
import LiveScan from '@/components/mailbox/LiveScan.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { IconName } from '@/components/ui/icons'
import { mailboxService, type MailboxConnection, type MailboxOverview, type MailProvider } from '@/services/mailbox.service'
import { useNotificationsStore } from '@/stores'
import { timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

const route = useRoute()
const router = useRouter()
const toast = useNotificationsStore()
const { t } = useI18n()

const data = ref<MailboxOverview | null>(null)
const loading = ref(true)
const busy = ref<number | string | null>(null)
const labelThreats = ref(false)
const confirmDelete = ref<MailboxConnection | null>(null)
const copied = ref(false)

const PROVIDERS: Array<{ id: MailProvider; name: string; colour: string; letter: string }> = [
  { id: 'gmail', name: 'Gmail', colour: 'linear-gradient(135deg,#ea4335,#fbbc05)', letter: 'G' },
  { id: 'outlook', name: 'Outlook / Hotmail', colour: 'linear-gradient(135deg,#0078d4,#28a8ea)', letter: 'O' },
]

const STATUS: Record<MailboxConnection['status'], { tone: string; icon: IconName }> = {
  active: { tone: 'text-emerald-700 bg-emerald-50 border-emerald-200', icon: 'checkCircle' },
  paused: { tone: 'text-slate-600 bg-slate-100 border-slate-200', icon: 'pause' },
  error: { tone: 'text-amber-700 bg-amber-50 border-amber-200', icon: 'alert' },
  revoked: { tone: 'text-red-700 bg-red-50 border-red-200', icon: 'xCircle' },
}

const ERRORS = ['denied', 'state', 'revoked', 'token', 'unreachable', 'provider', 'unauthorized', 'forbidden']

const totals = computed(() => (data.value?.items ?? []).reduce(
  (acc, m) => ({ scanned: acc.scanned + m.scanned_count, threats: acc.threats + m.threat_count }), { scanned: 0, threats: 0 }))

// Mailboxes whose scan is shown live (running now, or just finished: summary stays visible)
const watching = ref(new Set<number>())
function watchScan(id: number) { watching.value = new Set([...watching.value, id]) }

async function load() {
  try {
    data.value = await mailboxService.list()
    for (const m of data.value.items) if (m.progress?.state === 'running') watchScan(m.id)
  } finally {
    loading.value = false
  }
}

async function connect(provider: MailProvider) {
  busy.value = provider
  try {
    const { url } = await mailboxService.connect(provider, labelThreats.value)
    window.location.assign(url)
  } catch {
    busy.value = null
  }
}

async function syncNow(m: MailboxConnection) {
  busy.value = m.id
  try {
    await mailboxService.sync(m.id)
    // Remount the live view so it follows the new run from the start
    watching.value = new Set([...watching.value].filter((id) => id !== m.id))
    setTimeout(() => watchScan(m.id), 0)
  } catch { /* toast from apiFetch */ } finally { busy.value = null }
}

async function onScanFinished() {
  await load()
}

async function togglePause(m: MailboxConnection) {
  busy.value = m.id
  try { await mailboxService.setPaused(m.id, m.status !== 'paused'); await load() } finally { busy.value = null }
}

async function disconnect() {
  const m = confirmDelete.value
  if (!m) return
  busy.value = m.id
  try {
    await mailboxService.disconnect(m.id)
    toast.push(t('ux.mailbox.disconnected', { email: m.email }), 'success')
    confirmDelete.value = null
    await load()
  } finally { busy.value = null }
}

async function copyAddress() {
  if (!data.value?.forward_address) return
  try { await navigator.clipboard.writeText(data.value.forward_address); copied.value = true; setTimeout(() => (copied.value = false), 2000) } catch { /* ignore */ }
}

onMounted(async () => {
  const connected = route.query.connected
  const error = route.query.error
  if (connected) toast.push(t('ux.mailbox.connected'), 'success')
  if (typeof error === 'string') toast.push(t(`ux.mailbox.error.${ERRORS.includes(error) ? error : 'provider'}`), 'error')
  if (connected || error) router.replace({ query: {} })
  await load()
  if (connected) for (const m of data.value?.items ?? []) if (m.status === 'active' && !m.last_sync_at) watchScan(m.id)
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 pb-16 dark:bg-slate-950">
    <Navbar />
    <main class="mx-auto max-w-5xl px-4 pt-24">
      <RouterLink to="/dashboard" class="mb-4 inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-blue-600">
        <AppIcon name="chevronRight" :size="16" class="rotate-180" /> {{ t('ux.back') }}
      </RouterLink>

      <!-- Header -->
      <header class="hero">
        <span class="hero-icon"><AppIcon name="inbox" :size="28" /></span>
        <div class="flex-1">
          <h1 class="text-2xl font-bold text-slate-800 dark:text-white font-display">{{ t('ux.mailbox.title') }}</h1>
          <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">{{ t('ux.mailbox.subtitle') }}</p>
        </div>
        <div v-if="data?.items.length" class="flex gap-3">
          <div class="stat"><span class="text-xl font-bold tabular-nums">{{ totals.scanned }}</span><span>{{ t('ux.mailbox.scanned') }}</span></div>
          <div class="stat text-red-600"><span class="text-xl font-bold tabular-nums">{{ totals.threats }}</span><span>{{ t('ux.mailbox.threats') }}</span></div>
        </div>
      </header>

      <!-- How it works -->
      <ol class="mt-5 grid gap-3 sm:grid-cols-3">
        <li v-for="(s, i) in (['connect', 'scan', 'alert'] as const)" :key="s" class="how">
          <span class="how-icon"><AppIcon :name="(['plug', 'radar', 'bell'] as const)[i]!" :size="18" /></span>
          <div>
            <p class="text-sm font-semibold text-slate-800 dark:text-white">{{ t(`ux.mailbox.how.${s}.title`) }}</p>
            <p class="text-xs text-slate-500">{{ t(`ux.mailbox.how.${s}.text`) }}</p>
          </div>
        </li>
      </ol>

      <div v-if="loading" class="mt-6 h-40 animate-pulse rounded-3xl bg-white dark:bg-slate-900"></div>

      <template v-else-if="data">
        <!-- Connected mailboxes -->
        <section v-if="data.items.length" class="mt-6 space-y-3">
          <h2 class="section-title"><AppIcon name="shieldCheck" :size="18" /> {{ t('ux.mailbox.connectedTitle') }}</h2>
          <template v-for="m in data.items" :key="m.id">
          <article class="box">
            <span class="logo" :style="{ background: PROVIDERS.find((p) => p.id === m.provider)?.colour }">{{ m.provider === 'gmail' ? 'G' : 'O' }}</span>
            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <p class="truncate font-semibold text-slate-800 dark:text-white">{{ m.email }}</p>
                <span class="pill" :class="STATUS[m.status].tone"><AppIcon :name="STATUS[m.status].icon" :size="12" /> {{ t(`ux.mailbox.status.${m.status}`) }}</span>
                <span class="pill border-slate-200 bg-white text-slate-500"><AppIcon :name="m.read_only ? 'eye' : 'settings'" :size="12" /> {{ m.read_only ? t('ux.mailbox.readOnly') : t('ux.mailbox.labels') }}</span>
              </div>
              <div class="mt-1.5 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
                <span class="flex items-center gap-1"><AppIcon name="mail" :size="13" /> {{ t('ux.mailbox.scannedN', { n: m.scanned_count }) }}</span>
                <span class="flex items-center gap-1 text-red-600"><AppIcon name="shieldAlert" :size="13" /> {{ t('ux.mailbox.threatsN', { n: m.threat_count }) }}</span>
                <span class="flex items-center gap-1"><AppIcon name="clock" :size="13" /> {{ m.last_sync_at ? t('ux.mailbox.lastSync', { when: timeAgo(m.last_sync_at) }) : t('ux.mailbox.firstSync') }}</span>
              </div>
              <p v-if="m.last_error" class="mt-1.5 flex items-center gap-1 text-xs text-amber-700"><AppIcon name="info" :size="13" /> {{ t(`ux.mailbox.error.${ERRORS.includes(m.last_error) ? m.last_error : 'provider'}`) }}</p>
            </div>
            <div class="flex flex-wrap gap-2">
              <button v-if="m.status === 'revoked' || m.status === 'error'" class="act primary" :disabled="busy !== null" @click="connect(m.provider)">
                <AppIcon name="plug" :size="15" /> {{ t('ux.mailbox.reconnect') }}
              </button>
              <button v-else class="act" :disabled="busy !== null || m.status === 'paused'" @click="syncNow(m)">
                <AppIcon name="refresh" :size="15" :class="{ 'animate-spin': busy === m.id }" /> {{ t('ux.mailbox.syncNow') }}
              </button>
              <button class="act" :disabled="busy !== null" @click="togglePause(m)">
                <AppIcon :name="m.status === 'paused' ? 'play' : 'pause'" :size="15" /> {{ m.status === 'paused' ? t('ux.mailbox.resume') : t('ux.mailbox.pause') }}
              </button>
              <button class="act danger" :disabled="busy !== null" @click="confirmDelete = m">
                <AppIcon name="trash" :size="15" /> {{ t('ux.mailbox.disconnect') }}
              </button>
            </div>
          </article>
            <LiveScan v-if="watching.has(m.id)" :key="`live-${m.id}`" :mailbox-id="m.id" :email="m.email" class="-mt-1" @finished="onScanFinished" />
          </template>
          <RouterLink to="/dashboard?tab=history" class="inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 hover:underline">
            {{ t('ux.mailbox.seeResults') }} <AppIcon name="arrowRight" :size="15" />
          </RouterLink>
        </section>

        <!-- Connect -->
        <section class="mt-6">
          <h2 class="section-title"><AppIcon name="plug" :size="18" /> {{ t('ux.mailbox.connectTitle') }}</h2>
          <div class="grid gap-3 sm:grid-cols-2">
            <div v-for="p in PROVIDERS" :key="p.id" class="provider">
              <span class="logo" :style="{ background: p.colour }">{{ p.letter }}</span>
              <div class="flex-1">
                <p class="font-semibold text-slate-800 dark:text-white">{{ p.name }}</p>
                <p class="text-xs text-slate-500">{{ data.providers[p.id] ? t('ux.mailbox.readOnlyHint') : t('ux.mailbox.notConfigured') }}</p>
              </div>
              <button class="act primary" :disabled="!data.providers[p.id] || busy !== null" @click="connect(p.id)">
                <span v-if="busy === p.id" class="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/50 border-t-white"></span>
                <AppIcon v-else name="plug" :size="15" /> {{ t('ux.mailbox.connect') }}
              </button>
            </div>
          </div>
          <label class="mt-3 flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
            <input v-model="labelThreats" type="checkbox" class="mt-1 rounded" />
            <span>{{ t('ux.mailbox.labelOption') }}</span>
          </label>
        </section>

        <!-- Forwarding -->
        <section class="mt-6 forward">
          <span class="how-icon"><AppIcon name="mail" :size="18" /></span>
          <div class="flex-1">
            <h2 class="font-semibold text-slate-800 dark:text-white">{{ t('ux.mailbox.forwardTitle') }}</h2>
            <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">{{ t('ux.mailbox.forwardText') }}</p>
            <div v-if="data.forward_address" class="mt-3 flex flex-wrap items-center gap-2">
              <code class="rounded-xl bg-white px-3 py-2 text-sm font-semibold text-blue-700 ring-1 ring-blue-200 dark:bg-slate-900 dark:text-cyan-300">{{ data.forward_address }}</code>
              <button class="act" @click="copyAddress"><AppIcon :name="copied ? 'check' : 'clipboard'" :size="15" /> {{ copied ? t('ux.copied') : t('ux.copy') }}</button>
            </div>
            <p v-else class="mt-2 text-xs text-slate-500">{{ t('ux.mailbox.forwardOff') }}</p>
            <p class="mt-2 flex items-start gap-1.5 text-xs text-slate-500"><AppIcon name="info" :size="14" class="mt-0.5" /> {{ t('ux.mailbox.forwardTip') }}</p>
          </div>
        </section>

        <!-- Privacy -->
        <section class="mt-6 grid gap-3 sm:grid-cols-3">
          <div v-for="(k, i) in (['read', 'store', 'never'] as const)" :key="k" class="privacy">
            <AppIcon :name="(['eye', 'lock', 'ban'] as const)[i]!" :size="18" class="text-blue-600" />
            <p class="text-sm font-semibold text-slate-800 dark:text-white">{{ t(`ux.mailbox.privacy.${k}.title`) }}</p>
            <p class="text-xs text-slate-500">{{ t(`ux.mailbox.privacy.${k}.text`) }}</p>
          </div>
        </section>
        <RouterLink to="/privacy" class="mt-3 inline-flex items-center gap-1.5 text-sm text-blue-600 hover:underline"><AppIcon name="lock" :size="14" /> {{ t('ux.privacy.link') }}</RouterLink>
      </template>
    </main>

    <!-- Confirm disconnect -->
    <div v-if="confirmDelete" class="fixed inset-0 z-[60] grid place-items-center bg-slate-900/50 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" @click.self="confirmDelete = null">
      <div class="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl dark:bg-slate-900">
        <span class="grid h-12 w-12 place-items-center rounded-2xl bg-red-50 text-red-600"><AppIcon name="trash" :size="22" /></span>
        <h3 class="mt-3 text-lg font-bold text-slate-800 dark:text-white">{{ t('ux.mailbox.confirmTitle') }}</h3>
        <p class="mt-1 text-sm text-slate-600 dark:text-slate-300">{{ t('ux.mailbox.confirmText', { email: confirmDelete.email }) }}</p>
        <div class="mt-5 flex justify-end gap-2">
          <button class="act" @click="confirmDelete = null">{{ t('common.cancel') }}</button>
          <button class="act danger-solid" :disabled="busy !== null" @click="disconnect"><AppIcon name="trash" :size="15" /> {{ t('ux.mailbox.disconnect') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hero { display: flex; flex-wrap: wrap; align-items: center; gap: 1rem; padding: 1.4rem; border-radius: 1.6rem; background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(6, 182, 212, 0.08)); border: 1px solid rgba(37, 99, 235, 0.14); }
.hero-icon { display: grid; place-items: center; width: 3.5rem; height: 3.5rem; border-radius: 1.2rem; color: white; background: linear-gradient(135deg, #2563eb, #06b6d4); box-shadow: 0 12px 26px -12px rgba(37, 99, 235, 0.8); }
.stat { display: flex; flex-direction: column; align-items: center; padding: 0.5rem 0.9rem; border-radius: 1rem; background: rgba(255, 255, 255, 0.8); font-size: 0.7rem; color: #64748b; }
:global(.dark) .stat { background: rgba(15, 23, 42, 0.7); }
.how, .privacy { display: flex; gap: 0.7rem; padding: 0.9rem; border-radius: 1.1rem; background: white; border: 1px solid rgba(148, 163, 184, 0.22); }
.privacy { flex-direction: column; gap: 0.35rem; }
:global(.dark) .how, :global(.dark) .privacy, :global(.dark) .box, :global(.dark) .provider, :global(.dark) .forward { background: #0b1224; border-color: #1e293b; }
.how-icon { display: grid; place-items: center; width: 2.2rem; height: 2.2rem; border-radius: 0.8rem; color: #2563eb; background: rgba(37, 99, 235, 0.1); flex-shrink: 0; }
.section-title { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; font-weight: 700; color: #1e293b; }
:global(.dark) .section-title { color: #e2e8f0; }
.box, .provider { display: flex; flex-wrap: wrap; align-items: center; gap: 0.9rem; padding: 1rem 1.1rem; border-radius: 1.3rem; background: white; border: 1px solid rgba(148, 163, 184, 0.22); }
.logo { display: grid; place-items: center; width: 2.8rem; height: 2.8rem; border-radius: 0.95rem; color: white; font-weight: 800; font-size: 1.1rem; flex-shrink: 0; }
.pill { display: inline-flex; align-items: center; gap: 0.25rem; padding: 0.1rem 0.5rem; border-radius: 9999px; border-width: 1px; font-size: 0.68rem; font-weight: 600; }
.act { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.5rem 0.8rem; border-radius: 0.8rem; font-size: 0.78rem; font-weight: 600; color: #334155; background: white; border: 1px solid rgba(148, 163, 184, 0.35); transition: all 0.15s ease; }
.act:hover:not(:disabled) { border-color: #2563eb; color: #2563eb; }
.act:disabled { opacity: 0.5; cursor: not-allowed; }
:global(.dark) .act { background: #0f172a; color: #cbd5e1; border-color: #1e293b; }
.act.primary { color: white; background: linear-gradient(135deg, #2563eb, #06b6d4); border: 0; }
.act.primary:hover:not(:disabled) { color: white; }
.act.danger:hover:not(:disabled) { color: #dc2626; border-color: #fca5a5; }
.act.danger-solid { color: white; background: #dc2626; border: 0; }
.forward { display: flex; gap: 0.8rem; padding: 1.1rem; border-radius: 1.3rem; background: white; border: 1px solid rgba(148, 163, 184, 0.22); }
</style>
