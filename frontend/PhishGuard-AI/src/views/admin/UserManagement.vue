<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import PageHeader from '@/components/admin/ui/PageHeader.vue'
import Panel from '@/components/admin/ui/Panel.vue'
import Pill from '@/components/admin/ui/Pill.vue'
import StatTile from '@/components/admin/ui/StatTile.vue'
import { adminService, type AdminUser, type ApprovalStatus, type UserActivity } from '@/services/admin.service'
import { useNotificationsStore } from '@/stores/notifications'
import { useAuthStore } from '@/stores/auth'
import { formatDate, timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

/**
 * User management: approval workflow (approve / ask for further verification / reject),
 * sign-up intelligence (IP, location, network, device, risk flags) and account controls.
 */
type Filter = 'all' | 'pending' | 'review' | 'approved' | 'rejected' | 'suspended' | 'risky' | 'admins'
const FILTERS: Filter[] = ['all', 'pending', 'review', 'approved', 'rejected', 'suspended', 'risky', 'admins']

const { t } = useI18n()
const toast = useNotificationsStore()
const auth = useAuthStore()

const users = ref<AdminUser[]>([])
const loading = ref(false)
const filter = ref<Filter>('all')
const q = ref('')
const sort = ref<'recent' | 'risk' | 'activity'>('recent')
const selected = ref<AdminUser | null>(null)
const activity = ref<UserActivity | null>(null)
const note = ref('')
const resendCode = ref(true)
const busy = ref(false)

async function load() {
  loading.value = true
  try {
    users.value = (await adminService.listUsers()).items
    if (selected.value) selected.value = users.value.find((u) => u.id === selected.value?.id) ?? null
  } finally {
    loading.value = false
  }
}
onMounted(load)

const counts = computed(() => ({
  all: users.value.length,
  pending: users.value.filter((u) => u.approval_status === 'pending').length,
  review: users.value.filter((u) => u.approval_status === 'review').length,
  approved: users.value.filter((u) => u.approval_status === 'approved').length,
  rejected: users.value.filter((u) => u.approval_status === 'rejected').length,
  suspended: users.value.filter((u) => u.status === 'suspended').length,
  risky: users.value.filter((u) => u.risk_score >= 50).length,
  admins: users.value.filter((u) => u.role === 'admin').length,
}))
const mfaRate = computed(() => users.value.length ? Math.round(users.value.filter((u) => u.mfa_enabled).length / users.value.length * 100) : 0)

const filtered = computed(() => {
  const needle = q.value.trim().toLowerCase()
  const list = users.value.filter((u) => {
    const match = {
      all: true, pending: u.approval_status === 'pending', review: u.approval_status === 'review',
      approved: u.approval_status === 'approved', rejected: u.approval_status === 'rejected',
      suspended: u.status === 'suspended', risky: u.risk_score >= 50, admins: u.role === 'admin',
    }[filter.value]
    const text = [u.name, u.email, u.registration.ip, u.registration.geo.city, u.registration.geo.country, u.city].join(' ').toLowerCase()
    return match && (!needle || text.includes(needle))
  })
  const by = {
    recent: (a: AdminUser, b: AdminUser) => (b.created_at ?? '').localeCompare(a.created_at ?? ''),
    risk: (a: AdminUser, b: AdminUser) => b.risk_score - a.risk_score,
    activity: (a: AdminUser, b: AdminUser) => (b.last_login ?? '').localeCompare(a.last_login ?? ''),
  }[sort.value]
  return [...list].sort(by)
})

const APPROVAL_TONE: Record<ApprovalStatus, 'green' | 'amber' | 'blue' | 'red'> = {
  approved: 'green', pending: 'amber', review: 'blue', rejected: 'red',
}
const riskTone = (score: number) => (score >= 70 ? 'red' : score >= 40 ? 'amber' : 'green') as 'red' | 'amber' | 'green'
const riskBar = (score: number) => (score >= 70 ? 'bg-red-500' : score >= 40 ? 'bg-amber-500' : 'bg-emerald-500')
const riskText = (score: number) => (score >= 70 ? 'text-red-600' : score >= 40 ? 'text-amber-600' : 'text-emerald-600')

function flagEmoji(code?: string) {
  if (!code || code.length !== 2) return '🌐'
  return String.fromCodePoint(...code.toUpperCase().split('').map((c) => 127397 + c.charCodeAt(0)))
}
function location(u: AdminUser) {
  const geo = u.registration.geo
  if (geo.local) return t('as.logins.local')
  return [geo.city, geo.country].filter(Boolean).join(', ') || '—'
}
const initials = (name: string) => name.split(/\s+/).map((p) => p[0]).join('').slice(0, 2).toUpperCase()

async function open(user: AdminUser) {
  selected.value = user
  note.value = user.approval_note ?? ''
  activity.value = null
  activity.value = await adminService.getActivity(user.id)
}

watch(filter, () => { if (selected.value && !filtered.value.includes(selected.value)) selected.value = null })

async function run(action: () => Promise<AdminUser | unknown>, success: string) {
  busy.value = true
  try {
    const result = await action()
    toast.push(success, 'success')
    if (result && typeof result === 'object' && 'id' in result) {
      const updated = result as AdminUser
      users.value = users.value.map((u) => (u.id === updated.id ? updated : u))
      if (selected.value?.id === updated.id) selected.value = updated
    }
    if (selected.value) activity.value = await adminService.getActivity(selected.value.id)
  } catch {
    /* apiFetch shows the error (or the sudo prompt) */
  } finally {
    busy.value = false
  }
}

const approve = (u: AdminUser) => run(() => adminService.setApproval(u.id, 'approve', note.value), t('um.toast.approved', { name: u.name }))
const requestReview = (u: AdminUser) => run(() => adminService.setApproval(u.id, 'review', note.value, resendCode.value), t('um.toast.review', { name: u.name }))
function reject(u: AdminUser) {
  if (!confirm(t('um.confirmReject', { name: u.name }))) return
  void run(() => adminService.setApproval(u.id, 'reject', note.value), t('um.toast.rejected', { name: u.name }))
}
const toggleSuspend = (u: AdminUser) => run(
  () => (u.status === 'active' ? adminService.suspendUser(u.id) : adminService.reactivateUser(u.id)),
  t(u.status === 'active' ? 'users.nowSuspended' : 'users.nowActive', { name: u.name }))
const unlock = (u: AdminUser) => run(() => adminService.unlockUser(u.id), t('um.toast.unlocked'))
const forceLogout = (u: AdminUser) => run(() => adminService.forceLogout(u.id), t('users.sessionsRevoked', { name: u.name }))
function toggleRole(u: AdminUser) {
  const next = u.role === 'admin' ? 'user' : 'admin'
  if (!confirm(t(next === 'admin' ? 'um.confirmGrant' : 'um.confirmRevoke', { name: u.name }))) return
  void run(() => adminService.updateUser(u.id, { role: next }), t('um.toast.role'))
}
async function remove(u: AdminUser) {
  if (!confirm(t('users.confirmDelete', { name: u.name }))) return
  busy.value = true
  try {
    await adminService.deleteUser(u.id)
    users.value = users.value.filter((x) => x.id !== u.id)
    selected.value = null
    toast.push(t('users.deleted', { name: u.name }), 'success')
  } catch { /* shown */ } finally { busy.value = false }
}

const isSelf = (u: AdminUser) => String(u.id) === String(auth.user?.id)
</script>

<template>
  <div class="space-y-6">
    <PageHeader :title="t('um.title')" :subtitle="t('um.subtitle')" icon="👥">
      <button class="btn-ghost" :disabled="loading" @click="load">↻ {{ t('common.refresh') }}</button>
    </PageHeader>

    <!-- KPIs -->
    <section class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
      <StatTile :label="t('um.kpi.total')" :value="counts.all" icon="👥" clickable @click="filter = 'all'" />
      <StatTile :label="t('um.kpi.pending')" :value="counts.pending" icon="⏳" tone="amber" :hint="t('um.kpi.pendingHint')" clickable @click="filter = 'pending'" />
      <StatTile :label="t('um.kpi.review')" :value="counts.review" icon="🔎" tone="blue" clickable @click="filter = 'review'" />
      <StatTile :label="t('um.kpi.risky')" :value="counts.risky" icon="⚠️" tone="red" :hint="t('um.kpi.riskyHint')" clickable @click="filter = 'risky'" />
      <StatTile :label="t('um.kpi.suspended')" :value="counts.suspended" icon="⛔" clickable @click="filter = 'suspended'" />
      <StatTile :label="t('um.kpi.mfa')" :value="`${mfaRate}%`" icon="🔐" tone="green" />
    </section>

    <!-- Approval banner -->
    <button v-if="counts.pending" class="flex w-full items-center gap-3 rounded-2xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 p-4 text-left transition hover:shadow-md dark:border-amber-500/30 dark:from-amber-500/10 dark:to-orange-500/5"
            @click="filter = 'pending'">
      <span class="text-2xl">⏳</span>
      <span class="flex-1"><b class="block text-amber-900 dark:text-amber-200">{{ t('um.banner', { n: counts.pending }) }}</b>
        <span class="text-sm text-amber-800/80 dark:text-amber-300/80">{{ t('um.bannerHint') }}</span></span>
      <span class="text-sm font-semibold text-amber-800 dark:text-amber-300">{{ t('overview.handle') }} →</span>
    </button>

    <!-- Filters -->
    <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
      <div class="flex flex-wrap gap-1.5">
        <button v-for="f in FILTERS" :key="f" class="chip" :class="{ active: filter === f }" @click="filter = f">
          {{ t(`um.filter.${f}`) }} <span class="opacity-60">{{ counts[f] }}</span>
        </button>
      </div>
      <div class="flex gap-2">
        <input v-model="q" type="search" :placeholder="t('um.search')" class="input w-full lg:w-72" />
        <select v-model="sort" class="input w-auto">
          <option value="recent">{{ t('um.sort.recent') }}</option>
          <option value="risk">{{ t('um.sort.risk') }}</option>
          <option value="activity">{{ t('um.sort.activity') }}</option>
        </select>
      </div>
    </div>

    <!-- Table -->
    <Panel flush>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500 dark:bg-slate-800/50">
            <tr>
              <th class="px-5 py-3">{{ t('users.col.user') }}</th>
              <th class="px-3">{{ t('um.col.status') }}</th>
              <th class="px-3">{{ t('um.col.risk') }}</th>
              <th class="hidden px-3 lg:table-cell">{{ t('um.col.registration') }}</th>
              <th class="hidden px-3 md:table-cell">{{ t('users.col.lastActivity') }}</th>
              <th class="px-5 text-right"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr v-if="loading && !users.length"><td colspan="6" class="px-5 py-10 text-center text-slate-400">{{ t('users.loading') }}</td></tr>
            <tr v-else-if="!filtered.length"><td colspan="6" class="px-5 py-10 text-center text-slate-400">{{ t('users.noMatch') }}</td></tr>
            <tr v-for="u in filtered" :key="u.id" class="cursor-pointer transition hover:bg-slate-50/80 dark:hover:bg-slate-800/40"
                :class="{ 'bg-blue-50/60 dark:bg-cyan-500/5': selected?.id === u.id }" @click="open(u)">
              <td class="px-5 py-3">
                <div class="flex items-center gap-3">
                  <img v-if="u.has_avatar" :src="`/api/user/avatar/${u.id}`" alt="" class="h-9 w-9 flex-shrink-0 rounded-full object-cover" />
                  <span v-else class="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-gradient-to-br from-blue-500 to-cyan-400 text-xs font-bold text-white">{{ initials(u.name) }}</span>
                  <div class="min-w-0">
                    <p class="truncate font-semibold text-slate-800 dark:text-slate-100">{{ u.name }}
                      <Pill v-if="u.role === 'admin'" tone="violet" class="ml-1">ADMIN</Pill></p>
                    <p class="truncate text-xs text-slate-400">{{ u.email }}</p>
                  </div>
                </div>
              </td>
              <td class="px-3">
                <div class="flex flex-col items-start gap-1">
                  <Pill :tone="APPROVAL_TONE[u.approval_status]" dot :pulse="u.approval_status === 'pending'">{{ t(`um.approval.${u.approval_status}`) }}</Pill>
                  <span class="flex gap-1">
                    <Pill v-if="u.status === 'suspended'" tone="red">{{ t('common.suspended') }}</Pill>
                    <Pill v-if="u.locked_until" tone="orange">🔒 {{ t('um.locked') }}</Pill>
                    <Pill v-if="!u.email_verified" tone="slate">{{ t('users.notVerified') }}</Pill>
                  </span>
                </div>
              </td>
              <td class="px-3">
                <div class="w-28">
                  <div class="flex items-center justify-between text-xs"><b class="tabular-nums" :class="riskText(u.risk_score)">{{ u.risk_score }}</b>
                    <span class="text-slate-400">{{ t('um.flags', { n: u.risk_flags.length }) }}</span></div>
                  <div class="mt-1 h-1.5 rounded-full bg-slate-100 dark:bg-slate-800"><div class="h-full rounded-full" :class="riskBar(u.risk_score)" :style="{ width: `${Math.max(4, u.risk_score)}%` }"></div></div>
                </div>
              </td>
              <td class="hidden px-3 lg:table-cell">
                <p class="text-xs"><span class="mr-1">{{ flagEmoji(u.registration.geo.country_code) }}</span>{{ location(u) }}</p>
                <p class="font-mono text-[11px] text-slate-400">{{ u.registration.ip ?? '—' }} · {{ u.registration.device }}</p>
              </td>
              <td class="hidden px-3 text-xs text-slate-500 md:table-cell">{{ u.last_login ? timeAgo(u.last_login) : t('users.never') }}</td>
              <td class="px-5 text-right" @click.stop>
                <div v-if="u.approval_status === 'pending' || u.approval_status === 'review'" class="inline-flex gap-1">
                  <button class="icon-btn text-emerald-600" :title="t('um.action.approve')" :disabled="busy" @click="approve(u)">✓</button>
                  <button class="icon-btn text-red-600" :title="t('um.action.reject')" :disabled="busy" @click="reject(u)">✕</button>
                </div>
                <button v-else class="text-xs font-semibold text-blue-600 hover:underline dark:text-cyan-400" @click="open(u)">{{ t('common.details') }} →</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Panel>

    <!-- ============ Detail drawer ============ -->
    <Teleport to="body">
      <Transition name="drawer">
        <div v-if="selected" class="fixed inset-0 z-50 flex justify-end bg-slate-950/40 backdrop-blur-[2px]" @click.self="selected = null">
          <aside class="h-full w-full max-w-2xl overflow-y-auto bg-slate-50 shadow-2xl dark:bg-slate-950" role="dialog" aria-modal="true">
            <header class="sticky top-0 z-10 border-b border-slate-200 bg-white/95 px-6 py-4 backdrop-blur dark:border-slate-800 dark:bg-slate-900/95">
              <div class="flex items-center gap-4">
                <img v-if="selected.has_avatar" :src="`/api/user/avatar/${selected.id}`" alt="" class="h-14 w-14 rounded-2xl object-cover" />
                <span v-else class="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 text-lg font-bold text-white">{{ initials(selected.name) }}</span>
                <div class="min-w-0 flex-1">
                  <p class="truncate text-lg font-bold text-slate-900 dark:text-white">{{ selected.name }}</p>
                  <p class="truncate text-sm text-slate-500">{{ selected.email }}<span v-if="selected.phone"> · {{ selected.phone }}</span></p>
                  <div class="mt-1 flex flex-wrap gap-1">
                    <Pill :tone="APPROVAL_TONE[selected.approval_status]" dot>{{ t(`um.approval.${selected.approval_status}`) }}</Pill>
                    <Pill :tone="selected.status === 'active' ? 'green' : 'red'">{{ selected.status === 'active' ? t('common.active') : t('common.suspended') }}</Pill>
                    <Pill :tone="selected.mfa_enabled ? 'green' : 'amber'">{{ selected.mfa_enabled ? '🔐 MFA' : t('asettings.mfaOff') }}</Pill>
                    <Pill v-if="selected.role === 'admin'" tone="violet">ADMIN</Pill>
                  </div>
                </div>
                <button class="rounded-lg px-2 py-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800" :aria-label="t('common.close')" @click="selected = null">✕</button>
              </div>
            </header>

            <div class="space-y-5 p-6">
              <!-- Decision -->
              <Panel :title="t('um.decision.title')" :hint="t('um.decision.hint')">
                <textarea v-model="note" rows="2" maxlength="1000" :placeholder="t('um.decision.note')"
                          class="input min-h-[64px] resize-none"></textarea>
                <label class="mt-2 flex items-center gap-2 text-xs text-slate-500"><input v-model="resendCode" type="checkbox" /> {{ t('um.decision.resend') }}</label>
                <div class="mt-3 grid gap-2 sm:grid-cols-3">
                  <button class="decision green" :disabled="busy || isSelf(selected) || selected.approval_status === 'approved'" @click="approve(selected)">✓ {{ t('um.action.approve') }}</button>
                  <button class="decision blue" :disabled="busy || isSelf(selected)" @click="requestReview(selected)">🔎 {{ t('um.action.review') }}</button>
                  <button class="decision red" :disabled="busy || isSelf(selected) || selected.approval_status === 'rejected'" @click="reject(selected)">✕ {{ t('um.action.reject') }}</button>
                </div>
                <p v-if="selected.approved_at" class="mt-2 text-xs text-slate-400">{{ t('um.decision.last', { date: formatDate(selected.approved_at) }) }}</p>
              </Panel>

              <!-- Risk -->
              <Panel :title="t('um.risk.title')" :hint="t('um.risk.hint')">
                <div class="flex items-center gap-4">
                  <div class="grid h-16 w-16 place-items-center rounded-2xl text-2xl font-black text-white" :class="riskBar(selected.risk_score)">{{ selected.risk_score }}</div>
                  <div class="flex-1">
                    <p class="font-semibold text-slate-800 dark:text-slate-100">{{ t(`um.risk.level.${riskTone(selected.risk_score)}`) }}</p>
                    <p class="text-xs text-slate-500">{{ t('um.risk.explain') }}</p>
                  </div>
                </div>
                <ul v-if="selected.risk_flags.length" class="mt-4 space-y-2">
                  <li v-for="f in selected.risk_flags" :key="f.code" class="flex items-start gap-3 rounded-xl bg-red-50/70 p-3 dark:bg-red-500/5">
                    <span class="rounded-md bg-red-500 px-1.5 py-0.5 text-[10px] font-bold text-white">+{{ f.weight }}</span>
                    <div class="text-sm"><b class="text-slate-800 dark:text-slate-100">{{ t(`um.flag.${f.code}`) }}</b>
                      <p class="text-xs text-slate-500">{{ t(`um.flag.${f.code}.hint`, { detail: f.detail }) }}</p></div>
                  </li>
                </ul>
                <p v-else class="mt-4 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300">✓ {{ t('um.risk.clean') }}</p>
              </Panel>

              <!-- Registration intelligence -->
              <Panel :title="t('um.reg.title')" :hint="t('um.reg.hint')">
                <dl class="grid gap-3 text-sm sm:grid-cols-2">
                  <div class="kv"><dt>IP</dt><dd class="font-mono">{{ selected.registration.ip ?? '—' }}</dd></div>
                  <div class="kv"><dt>{{ t('map.col.location') }}</dt><dd>{{ flagEmoji(selected.registration.geo.country_code) }} {{ location(selected) }}<span v-if="selected.registration.geo.region"> ({{ selected.registration.geo.region }})</span></dd></div>
                  <div class="kv"><dt>{{ t('um.reg.network') }}</dt><dd>{{ selected.registration.geo.isp ?? '—' }}
                    <span class="ml-1 inline-flex gap-1">
                      <Pill v-if="selected.registration.geo.proxy" tone="red">VPN/Proxy</Pill>
                      <Pill v-if="selected.registration.geo.hosting" tone="orange">{{ t('um.reg.datacenter') }}</Pill>
                      <Pill v-if="selected.registration.geo.mobile" tone="blue">{{ t('um.reg.mobile') }}</Pill>
                    </span></dd></div>
                  <div class="kv"><dt>{{ t('as.logins.device') }}</dt><dd>{{ selected.registration.device }}</dd></div>
                  <div class="kv"><dt>{{ t('um.reg.declared') }}</dt><dd>{{ [selected.city, selected.region].filter(Boolean).join(', ') || '—' }}</dd></div>
                  <div class="kv"><dt>{{ t('um.reg.terms') }}</dt><dd>{{ selected.registration.terms_accepted_at ? formatDate(selected.registration.terms_accepted_at) : '—' }}</dd></div>
                  <div class="kv"><dt>{{ t('um.reg.created') }}</dt><dd>{{ formatDate(selected.created_at) }}</dd></div>
                  <div class="kv"><dt>{{ t('um.reg.provider') }}</dt><dd>{{ selected.auth_provider }}</dd></div>
                  <div class="kv sm:col-span-2"><dt>User-Agent</dt><dd class="break-all font-mono text-[11px] text-slate-500">{{ selected.registration.user_agent ?? '—' }}</dd></div>
                </dl>
                <div v-if="activity?.same_ip_accounts.length" class="mt-4 rounded-xl border border-amber-200 bg-amber-50/60 p-3 dark:border-amber-500/30 dark:bg-amber-500/5">
                  <p class="text-sm font-semibold text-amber-800 dark:text-amber-300">⚠️ {{ t('um.reg.sameIp', { n: activity.same_ip_accounts.length }) }}</p>
                  <ul class="mt-1 space-y-0.5 text-xs text-amber-900/80 dark:text-amber-200/80">
                    <li v-for="s in activity.same_ip_accounts" :key="s.id">{{ s.email }} · {{ t(`um.approval.${s.approval_status}`) }}</li>
                  </ul>
                </div>
              </Panel>

              <!-- Activity -->
              <Panel :title="t('um.activity.title')" :hint="activity ? t('um.activity.hint', { ips: activity.distinct_login_ips, failed: activity.failed_logins_24h }) : ''">
                <p v-if="!activity" class="text-sm text-slate-400">{{ t('common.loading') }}</p>
                <p v-else-if="!activity.events.length" class="text-sm text-slate-400">{{ t('um.activity.empty') }}</p>
                <ol v-else class="relative space-y-3 border-l border-slate-200 pl-4 dark:border-slate-700">
                  <li v-for="e in activity.events" :key="e.id" class="relative">
                    <span class="absolute -left-[21px] top-1.5 h-2.5 w-2.5 rounded-full ring-4 ring-slate-50 dark:ring-slate-950"
                          :class="e.severity === 'critical' ? 'bg-red-500' : e.severity === 'warning' ? 'bg-amber-500' : 'bg-emerald-500'"></span>
                    <p class="text-sm font-medium text-slate-800 dark:text-slate-100">{{ t(`event.${e.type}`) }}
                      <span v-if="e.actor && e.actor_id !== selected.id" class="text-xs font-normal text-slate-400">· {{ t('um.activity.by', { name: e.actor }) }}</span></p>
                    <p class="text-xs text-slate-500">{{ formatDate(e.created_at) }} · <span class="font-mono">{{ e.ip ?? '—' }}</span> · {{ e.location === 'local' ? t('as.logins.local') : e.location ?? '—' }} · {{ e.device }}</p>
                  </li>
                </ol>
              </Panel>

              <!-- Account controls -->
              <Panel :title="t('um.controls.title')">
                <div class="grid gap-2 sm:grid-cols-2">
                  <button class="control" :disabled="busy || isSelf(selected)" @click="toggleSuspend(selected)">{{ selected.status === 'active' ? `⛔ ${t('overview.suspend')}` : `✅ ${t('overview.reactivate')}` }}</button>
                  <button class="control" :disabled="busy" @click="forceLogout(selected)">⎋ {{ t('users.forceLogout') }}</button>
                  <button class="control" :disabled="busy || !selected.locked_until" @click="unlock(selected)">🔓 {{ t('um.action.unlock') }}</button>
                  <button class="control" :disabled="busy || isSelf(selected)" @click="toggleRole(selected)">👑 {{ selected.role === 'admin' ? t('um.action.revokeAdmin') : t('um.action.grantAdmin') }} <small>🔐</small></button>
                  <button class="control danger sm:col-span-2" :disabled="busy || isSelf(selected)" @click="remove(selected)">🗑 {{ t('um.action.delete') }} <small>🔐</small></button>
                </div>
                <p class="mt-3 text-xs text-slate-400">🔐 {{ t('um.controls.sudo') }}</p>
              </Panel>
            </div>
          </aside>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.input { border-radius: 0.75rem; border: 1px solid #e2e8f0; background: white; padding: 0.55rem 0.85rem; font-size: 0.875rem; outline: none; width: 100%; }
.input:focus { border-color: #60a5fa; box-shadow: 0 0 0 4px rgba(191, 219, 254, 0.45); }
:global(.dark) .input { background: #0f172a; border-color: #334155; color: #f1f5f9; }
.btn-ghost { border-radius: 0.75rem; border: 1px solid #e2e8f0; padding: 0.5rem 1rem; font-size: 0.875rem; font-weight: 500; }
:global(.dark) .btn-ghost { border-color: #334155; color: #e2e8f0; }
.chip { border-radius: 9999px; border: 1px solid #e2e8f0; padding: 0.35rem 0.8rem; font-size: 0.78rem; font-weight: 600; color: #475569; transition: all 0.15s; }
.chip:hover { border-color: #94a3b8; }
.chip.active { background: #0f172a; border-color: #0f172a; color: white; }
:global(.dark) .chip { border-color: #334155; color: #cbd5e1; }
:global(.dark) .chip.active { background: #22d3ee; border-color: #22d3ee; color: #0f172a; }
.icon-btn { display: inline-grid; place-items: center; width: 2rem; height: 2rem; border-radius: 0.6rem; font-weight: 700; transition: background 0.15s; }
.icon-btn:hover { background: #f1f5f9; }
:global(.dark) .icon-btn:hover { background: #1e293b; }
.decision { border-radius: 0.8rem; padding: 0.6rem; font-size: 0.85rem; font-weight: 700; color: white; transition: transform 0.15s, opacity 0.15s; }
.decision:hover:not(:disabled) { transform: translateY(-1px); }
.decision:disabled { opacity: 0.4; }
.decision.green { background: #059669; } .decision.blue { background: #2563eb; } .decision.red { background: #dc2626; }
.control { border-radius: 0.8rem; border: 1px solid #e2e8f0; background: white; padding: 0.6rem 0.8rem; font-size: 0.85rem; font-weight: 600; color: #334155; text-align: left; transition: all 0.15s; }
.control:hover:not(:disabled) { border-color: #93c5fd; background: #f8fafc; }
.control:disabled { opacity: 0.45; }
.control.danger { color: #dc2626; border-color: #fecaca; }
.control small { float: right; opacity: 0.6; }
:global(.dark) .control { background: #0f172a; border-color: #334155; color: #e2e8f0; }
.kv dt { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; color: #94a3b8; }
.kv dd { margin-top: 0.15rem; color: #1e293b; }
:global(.dark) .kv dd { color: #e2e8f0; }
.drawer-enter-active, .drawer-leave-active { transition: opacity 0.2s ease; }
.drawer-enter-active aside, .drawer-leave-active aside { transition: transform 0.25s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; }
.drawer-enter-from aside, .drawer-leave-to aside { transform: translateX(100%); }
</style>
