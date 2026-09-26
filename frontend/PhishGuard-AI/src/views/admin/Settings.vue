<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MfaSettings from '@/components/auth/MfaSettings.vue'
import PageHeader from '@/components/admin/ui/PageHeader.vue'
import Panel from '@/components/admin/ui/Panel.vue'
import Pill from '@/components/admin/ui/Pill.vue'
import RingGauge from '@/components/admin/ui/RingGauge.vue'
import { adminService, type PlatformSettings } from '@/services/admin.service'
import { socService, type SecurityOverview } from '@/services/soc.service'
import { userAccountService } from '@/services/userAccount.service'
import { ApiError } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { formatDate, timeAgo } from '@/utils/risk'
import { useI18n } from '@/i18n'

/**
 * Admin settings in three tabs:
 *   profile   - identity (photo, name, contact, role details)
 *   security  - personal security centre (posture score, MFA, password, sessions, login history)
 *   policies  - platform-wide rules (registration, authentication, triage, incidents)
 */
type Tab = 'profile' | 'security' | 'policies'
const TABS: Array<{ id: Tab; icon: string }> = [
  { id: 'profile', icon: '👤' }, { id: 'security', icon: '🛡️' }, { id: 'policies', icon: '⚙️' },
]

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const toast = useNotificationsStore()

const tab = ref<Tab>((['profile', 'security', 'policies'] as Tab[]).includes(route.query.tab as Tab) ? route.query.tab as Tab : 'profile')
watch(tab, (next) => router.replace({ query: { ...route.query, tab: next } }))

// ---------------- Profile ----------------
const overview = ref<SecurityOverview | null>(null)
const form = ref({ full_name: '', email: '', phone: '', job_title: '', organization: '', city: '', current_password: '' })
const savingProfile = ref(false)
const uploading = ref(false)
const avatarInput = ref<HTMLInputElement | null>(null)
const profile = computed(() => overview.value?.profile)
const emailChanged = computed(() => profile.value && form.value.email.trim().toLowerCase() !== profile.value.email)
const initials = computed(() => (form.value.full_name || profile.value?.email || 'A').split(' ').map((p) => p[0]).join('').slice(0, 2).toUpperCase())

async function loadOverview() {
  overview.value = await socService.getSecurityOverview()
  const p = overview.value.profile
  form.value = { full_name: p.full_name ?? '', email: p.email, phone: p.phone ?? '', job_title: p.job_title ?? '',
                 organization: p.organization ?? '', city: p.city ?? '', current_password: '' }
}

const message = (e: unknown, fallback: string) => (e instanceof ApiError ? e.message : fallback)

async function saveProfile() {
  savingProfile.value = true
  try {
    await userAccountService.updateProfile({
      full_name: form.value.full_name,
      ...(emailChanged.value ? { email: form.value.email, current_password: form.value.current_password } : {}),
    })
    await adminService.updateProfile({ phone: form.value.phone, job_title: form.value.job_title,
                                       organization: form.value.organization, city: form.value.city })
    if (auth.user) auth.setUser({ ...auth.user, displayName: form.value.full_name || undefined, email: form.value.email })
    toast.push(t('asettings.profileSaved'), 'success')
    await loadOverview()
  } catch (e) {
    toast.push(message(e, t('asettings.profileSaveFailed')), 'error')
  } finally {
    savingProfile.value = false
  }
}

async function onAvatar(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (file.size > 2 * 1024 * 1024) return toast.push(t('settings.imageTooLarge'), 'error')
  uploading.value = true
  try {
    const updated = await userAccountService.uploadAvatar(file)
    if (auth.user) auth.setUser({ ...auth.user, avatar_url: updated.avatar_url })
    await loadOverview()
    toast.push(t('settings.avatarUpdated'), 'success')
  } catch (e) {
    toast.push(message(e, t('settings.avatarFailed')), 'error')
  } finally {
    uploading.value = false
  }
}

async function removeAvatar() {
  await userAccountService.deleteAvatar()
  if (auth.user) auth.setUser({ ...auth.user, avatar_url: null })
  await loadOverview()
}

// ---------------- Security ----------------
const pw = ref({ current: '', next: '', confirm: '' })
const changingPassword = ref(false)
const posture = computed(() => overview.value?.posture)

const pwRules = computed(() => {
  const s = settings.value
  const value = pw.value.next
  return [
    { key: 'length', ok: value.length >= (s?.password_min_length ?? 12), text: t('auth.password.length', { n: s?.password_min_length ?? 12 }) },
    { key: 'upper', ok: !s?.password_require_upper || /[A-Z]/.test(value), text: t('auth.password.upper') },
    { key: 'number', ok: !s?.password_require_number || /\d/.test(value), text: t('auth.password.number') },
    { key: 'symbol', ok: !s?.password_require_symbol || /[^A-Za-z0-9]/.test(value), text: t('as.pw.symbol') },
  ]
})

async function changePassword() {
  if (pw.value.next !== pw.value.confirm) return toast.push(t('auth.errors.passwordMismatch'), 'error')
  changingPassword.value = true
  try {
    await userAccountService.changePassword(pw.value.current, pw.value.next)
    pw.value = { current: '', next: '', confirm: '' }
    toast.push(t('as.pw.changed'), 'success')
    await loadOverview()
  } catch (e) {
    toast.push(message(e, t('settings.passwordFailed')), 'error')
  } finally {
    changingPassword.value = false
  }
}

async function signOutOthers() {
  if (!confirm(t('as.sessions.confirm'))) return
  await socService.signOutOthers()
  toast.push(t('as.sessions.done'), 'success')
  await loadOverview()
}

const CHECK_TAB: Record<string, Tab | undefined> = { platform_mfa: 'policies', profile_complete: 'profile' }
function fixCheck(key: string) {
  const target = CHECK_TAB[key]
  if (target) tab.value = target
  else document.getElementById(key === 'mfa' ? 'mfa-panel' : 'password-panel')?.scrollIntoView({ behavior: 'smooth' })
}

const LOGIN_TONE: Record<string, 'green' | 'red' | 'amber'> = {
  login_success: 'green', login_failed: 'red', mfa_failed: 'red', login_blocked: 'amber', account_locked: 'red',
}

// ---------------- Policies ----------------
const settings = ref<PlatformSettings | null>(null)
const savedSettings = ref('')
const savingSettings = ref(false)
const dirty = computed(() => settings.value && JSON.stringify(settings.value) !== savedSettings.value)

async function loadSettings() {
  settings.value = await adminService.getSettings()
  savedSettings.value = JSON.stringify(settings.value)
}

async function saveSettings() {
  if (!settings.value) return
  savingSettings.value = true
  try {
    settings.value = await adminService.updateSettings(settings.value)
    savedSettings.value = JSON.stringify(settings.value)
    toast.push(t('asettings.saved'), 'success')
  } catch (e) {
    toast.push(message(e, t('asettings.saveFailed')), 'error')
  } finally {
    savingSettings.value = false
  }
}

const REGISTRATION_MODES = ['open', 'risk_based', 'approval'] as const
const TRIAGE_MODES = ['manual', 'assisted', 'auto'] as const

onMounted(() => { void loadOverview(); void loadSettings() })
</script>

<template>
  <div class="space-y-6">
    <PageHeader :title="t('admin.page.settings')" :subtitle="t('as.subtitle')" icon="⚙️" />

    <!-- Tabs -->
    <div class="inline-flex rounded-2xl bg-slate-100 p-1 dark:bg-slate-800/80">
      <button v-for="item in TABS" :key="item.id" class="rounded-xl px-4 py-2 text-sm font-semibold transition"
              :class="tab === item.id ? 'bg-white text-slate-900 shadow-sm dark:bg-slate-900 dark:text-white' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400'"
              @click="tab = item.id">
        {{ item.icon }} {{ t(`as.tab.${item.id}`) }}
      </button>
    </div>

    <!-- ================= PROFILE ================= -->
    <div v-if="tab === 'profile'" class="grid gap-6 lg:grid-cols-3">
      <!-- Identity card -->
      <div class="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900 to-blue-950 p-6 text-white shadow-lg">
        <div class="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-cyan-400/20 blur-3xl"></div>
        <p class="text-[11px] font-semibold uppercase tracking-widest text-cyan-300">{{ t('as.card.title') }}</p>
        <div class="mt-5 flex flex-col items-center text-center">
          <div class="relative">
            <img v-if="profile?.avatar_url" :src="profile.avatar_url" alt="" class="h-28 w-28 rounded-3xl object-cover ring-4 ring-white/10" />
            <div v-else class="grid h-28 w-28 place-items-center rounded-3xl bg-gradient-to-br from-cyan-400 to-blue-600 text-3xl font-bold ring-4 ring-white/10">{{ initials }}</div>
            <span class="absolute -bottom-2 -right-2 grid h-9 w-9 place-items-center rounded-xl text-sm shadow-lg"
                  :class="profile?.mfa_active ? 'bg-emerald-500' : 'bg-amber-500'" :title="profile?.mfa_active ? t('asettings.mfaOn') : t('asettings.mfaOff')">
              {{ profile?.mfa_active ? '🔒' : '⚠️' }}
            </span>
          </div>
          <p class="mt-4 text-lg font-bold">{{ form.full_name || profile?.email }}</p>
          <p class="text-sm text-slate-300">{{ form.job_title || t('admin.layout.administrator') }}<span v-if="form.organization"> · {{ form.organization }}</span></p>
          <p class="mt-1 text-xs text-slate-400">{{ profile?.email }}</p>
          <div class="mt-4 flex gap-2">
            <button class="rounded-xl bg-white/10 px-3 py-2 text-xs font-semibold hover:bg-white/20 disabled:opacity-50" :disabled="uploading" @click="avatarInput?.click()">
              📷 {{ uploading ? t('settings.uploading') : t('settings.changeAvatar') }}
            </button>
            <button v-if="profile?.avatar_url" class="rounded-xl px-3 py-2 text-xs text-slate-300 hover:bg-white/10" @click="removeAvatar">{{ t('common.delete') }}</button>
          </div>
          <input ref="avatarInput" type="file" accept="image/png,image/jpeg,image/webp" class="hidden" @change="onAvatar" />
          <p class="mt-2 text-[11px] text-slate-500">{{ t('settings.avatarHint') }}</p>
        </div>
        <dl class="mt-6 grid grid-cols-2 gap-3 border-t border-white/10 pt-4 text-xs">
          <div><dt class="text-slate-400">{{ t('as.card.since') }}</dt><dd class="font-semibold">{{ formatDate(profile?.created_at) }}</dd></div>
          <div><dt class="text-slate-400">{{ t('settings.lastLogin') }}</dt><dd class="font-semibold">{{ timeAgo(profile?.last_login) || '—' }}</dd></div>
          <div><dt class="text-slate-400">{{ t('as.card.score') }}</dt><dd class="font-semibold">{{ posture?.score ?? '—' }}/100 · {{ posture?.grade }}</dd></div>
          <div><dt class="text-slate-400">{{ t('users.col.role') }}</dt><dd class="font-semibold">{{ t('users.role.admin') }}</dd></div>
        </dl>
      </div>

      <!-- Form -->
      <Panel class="lg:col-span-2" :title="t('settings.personal')" :hint="t('as.profile.hint')">
        <form class="grid gap-4 sm:grid-cols-2" @submit.prevent="saveProfile">
          <label class="field sm:col-span-2"><span>{{ t('settings.fullName') }}</span><input v-model="form.full_name" maxlength="255" /></label>
          <label class="field"><span>{{ t('as.profile.jobTitle') }}</span><input v-model="form.job_title" maxlength="120" :placeholder="t('as.profile.jobPlaceholder')" /></label>
          <label class="field"><span>{{ t('as.profile.organization') }}</span><input v-model="form.organization" maxlength="160" placeholder="PhishGuard-AI" /></label>
          <label class="field"><span>{{ t('settings.email') }}</span><input v-model="form.email" type="email" required /></label>
          <label class="field"><span>{{ t('auth.phone') }}</span><input v-model="form.phone" placeholder="+237 6 00 00 00 00" /></label>
          <label class="field"><span>{{ t('as.profile.city') }}</span><input v-model="form.city" maxlength="120" placeholder="Yaoundé" /></label>
          <label v-if="emailChanged" class="field"><span>{{ t('settings.currentPassword') }} <em>({{ t('settings.requiredForEmail') }})</em></span>
            <input v-model="form.current_password" type="password" required autocomplete="current-password" /></label>
          <div class="flex items-center justify-between gap-3 sm:col-span-2">
            <p class="text-xs text-slate-400">🔏 {{ t('as.profile.privacy') }}</p>
            <button class="btn-primary" :disabled="savingProfile">{{ savingProfile ? t('settings.saving') : t('asettings.saveProfile') }}</button>
          </div>
        </form>
      </Panel>
    </div>

    <!-- ================= SECURITY CENTRE ================= -->
    <div v-else-if="tab === 'security'" class="space-y-6">
      <!-- Posture -->
      <section class="grid gap-6 lg:grid-cols-3">
        <div class="relative overflow-hidden rounded-2xl bg-slate-900 p-6 text-white shadow-lg lg:col-span-1">
          <div class="scan" aria-hidden="true"></div>
          <p class="text-[11px] font-semibold uppercase tracking-widest text-cyan-300">{{ t('as.posture.title') }}</p>
          <div class="mt-4 flex items-center gap-5">
            <RingGauge :value="posture?.score" :size="120" :label="t('as.posture.score')" />
            <div>
              <p class="text-5xl font-black" :class="{ 'text-emerald-400': posture?.grade === 'A', 'text-cyan-300': posture?.grade === 'B', 'text-amber-400': posture?.grade === 'C', 'text-red-400': posture?.grade === 'D' }">{{ posture?.grade ?? '—' }}</p>
              <p class="mt-1 text-sm text-slate-300">{{ t(`as.posture.grade${posture?.grade ?? 'D'}`) }}</p>
            </div>
          </div>
          <div class="mt-5 grid grid-cols-3 gap-2 text-center text-xs">
            <div class="rounded-xl bg-white/5 p-2"><p class="text-lg font-bold">{{ overview?.platform.failed_logins_24h ?? 0 }}</p><p class="text-slate-400">{{ t('as.posture.failed24') }}</p></div>
            <div class="rounded-xl bg-white/5 p-2"><p class="text-lg font-bold">{{ overview?.platform.locked_accounts ?? 0 }}</p><p class="text-slate-400">{{ t('as.posture.locked') }}</p></div>
            <div class="rounded-xl bg-white/5 p-2"><p class="text-lg font-bold" :class="overview?.platform.admins_without_mfa ? 'text-amber-400' : ''">{{ overview?.platform.admins_without_mfa ?? 0 }}/{{ overview?.platform.admins ?? 0 }}</p><p class="text-slate-400">{{ t('as.posture.adminsNoMfa') }}</p></div>
          </div>
        </div>

        <Panel class="lg:col-span-2" :title="t('as.checks.title')" :hint="t('as.checks.hint')">
          <ul class="grid gap-2 sm:grid-cols-2">
            <li v-for="check in posture?.checks ?? []" :key="check.key"
                class="flex items-start gap-3 rounded-xl border p-3"
                :class="check.ok ? 'border-emerald-100 bg-emerald-50/50 dark:border-emerald-500/20 dark:bg-emerald-500/5' : 'border-amber-200 bg-amber-50/60 dark:border-amber-500/30 dark:bg-amber-500/5'">
              <span class="mt-0.5 grid h-6 w-6 flex-shrink-0 place-items-center rounded-full text-xs font-bold text-white" :class="check.ok ? 'bg-emerald-500' : 'bg-amber-500'">{{ check.ok ? '✓' : '!' }}</span>
              <div class="min-w-0 flex-1">
                <p class="text-sm font-semibold text-slate-800 dark:text-slate-100">{{ t(`as.check.${check.key}`) }}</p>
                <p class="text-xs text-slate-500">{{ t(`as.check.${check.key}.hint`, { n: check.value ?? 0 }) }}</p>
              </div>
              <div class="text-right">
                <p class="text-[10px] font-semibold text-slate-400">+{{ check.weight }}</p>
                <button v-if="!check.ok" class="mt-1 text-xs font-semibold text-blue-600 hover:underline dark:text-cyan-400" @click="fixCheck(check.key)">{{ t('as.checks.fix') }}</button>
              </div>
            </li>
          </ul>
        </Panel>
      </section>

      <div class="grid gap-6 lg:grid-cols-2">
        <!-- MFA -->
        <div id="mfa-panel"><MfaSettings /></div>

        <!-- Password -->
        <Panel id="password-panel" :title="t('settings.changePassword')" :hint="profile?.password_changed_at ? t('as.pw.last', { when: timeAgo(profile.password_changed_at) }) : t('as.pw.never')">
          <form class="space-y-3" @submit.prevent="changePassword">
            <input v-model="pw.current" class="input" type="password" required autocomplete="current-password" :placeholder="t('settings.currentPassword')" />
            <input v-model="pw.next" class="input" type="password" required autocomplete="new-password" :placeholder="t('as.pw.new')" />
            <input v-model="pw.confirm" class="input" type="password" required autocomplete="new-password" :placeholder="t('settings.confirmPassword')" />
            <ul class="grid grid-cols-2 gap-1 text-xs">
              <li v-for="rule in pwRules" :key="rule.key" :class="rule.ok ? 'text-emerald-600' : 'text-slate-400'">{{ rule.ok ? '✓' : '○' }} {{ rule.text }}</li>
            </ul>
            <p class="rounded-lg bg-blue-50 px-3 py-2 text-xs text-blue-800 dark:bg-blue-500/10 dark:text-blue-200">ℹ️ {{ t('as.pw.sessionsNote') }}</p>
            <button class="btn-primary w-full" :disabled="changingPassword || pwRules.some((r) => !r.ok)">{{ changingPassword ? t('settings.changing') : t('settings.changePassword') }}</button>
          </form>
        </Panel>
      </div>

      <!-- Sessions + login history -->
      <Panel :title="t('as.logins.title')" :hint="t('as.logins.hint')" flush>
        <template #actions>
          <Pill :tone="overview?.sudo.active ? 'green' : 'slate'" dot :pulse="overview?.sudo.active">
            {{ overview?.sudo.active ? t('as.sudo.active') : t('as.sudo.inactive', { n: overview?.sudo.minutes ?? 10 }) }}
          </Pill>
          <button class="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-600 hover:bg-red-50 dark:border-red-500/30 dark:hover:bg-red-500/10" @click="signOutOthers">
            ⎋ {{ t('as.sessions.signOutOthers') }}
          </button>
        </template>
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-slate-50 text-left text-[11px] uppercase tracking-wide text-slate-500 dark:bg-slate-800/50">
              <tr><th class="px-5 py-2.5">{{ t('as.logins.result') }}</th><th class="px-3">IP</th><th class="px-3">{{ t('map.col.location') }}</th><th class="px-3">{{ t('as.logins.device') }}</th><th class="px-5 text-right">{{ t('audit.col.timestamp') }}</th></tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
              <tr v-if="!overview?.logins.length"><td colspan="5" class="px-5 py-8 text-center text-slate-400">{{ t('as.logins.empty') }}</td></tr>
              <tr v-for="e in overview?.logins ?? []" :key="e.id">
                <td class="px-5 py-2.5">
                  <Pill :tone="LOGIN_TONE[e.type] ?? 'slate'" dot>{{ t(`event.${e.type}`) }}</Pill>
                  <Pill v-if="e.details.new_location" tone="amber" class="ml-1">{{ t('as.logins.newLocation') }}</Pill>
                </td>
                <td class="px-3 font-mono text-xs">{{ e.ip ?? '—' }}</td>
                <td class="px-3 text-xs">{{ e.location === 'local' ? t('as.logins.local') : e.location ?? '—' }}
                  <Pill v-if="e.network.proxy" tone="red" class="ml-1">VPN/Proxy</Pill></td>
                <td class="px-3 text-xs text-slate-500">{{ e.device }}</td>
                <td class="px-5 text-right text-xs text-slate-500">{{ formatDate(e.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </Panel>
    </div>

    <!-- ================= POLICIES ================= -->
    <div v-else-if="settings" class="space-y-6">
      <div class="grid gap-6 xl:grid-cols-2">
        <Panel :title="`🚪 ${t('as.pol.registration')}`" :hint="t('as.pol.registrationHint')">
          <div class="space-y-4">
            <label class="toggle"><div><p>{{ t('asettings.allowSignup') }}</p><small>{{ t('asettings.allowSignupHint') }}</small></div>
              <input v-model="settings.allow_signup" type="checkbox" /></label>
            <div>
              <p class="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">{{ t('as.pol.mode') }}</p>
              <div class="grid gap-2 sm:grid-cols-3">
                <button v-for="mode in REGISTRATION_MODES" :key="mode" type="button" class="choice" :class="{ active: settings.registration_mode === mode }"
                        @click="settings.registration_mode = mode">
                  <b>{{ t(`as.pol.mode.${mode}`) }}</b><small>{{ t(`as.pol.mode.${mode}.hint`) }}</small>
                </button>
              </div>
            </div>
            <label v-if="settings.registration_mode === 'risk_based'" class="block text-sm">
              <span class="flex justify-between text-slate-600 dark:text-slate-300">{{ t('as.pol.riskThreshold') }} <b>{{ settings.registration_risk_threshold }}/100</b></span>
              <input v-model.number="settings.registration_risk_threshold" type="range" min="10" max="90" step="5" class="range" />
            </label>
            <label class="toggle"><div><p>{{ t('as.pol.disposable') }}</p><small>{{ t('as.pol.disposableHint') }}</small></div>
              <input v-model="settings.block_disposable_emails" type="checkbox" /></label>
            <label class="toggle"><div><p>{{ t('asettings.requireVerification') }}</p><small>{{ t('asettings.requireVerificationHint') }}</small></div>
              <input v-model="settings.require_email_verification" type="checkbox" /></label>
          </div>
        </Panel>

        <Panel :title="`🔑 ${t('as.pol.auth')}`" :hint="t('as.pol.authHint')">
          <div class="space-y-4">
            <label class="toggle"><div><p>{{ t('asettings.mfaRequired') }}</p><small>{{ t('asettings.mfaRequiredHint') }}</small></div>
              <input v-model="settings.mfa_required" type="checkbox" /></label>
            <div class="grid gap-3 sm:grid-cols-2">
              <label class="field"><span>{{ t('asettings.maxAttempts') }}</span><input v-model.number="settings.max_login_attempts" type="number" min="1" max="20" /></label>
              <label class="field"><span>{{ t('asettings.lockout') }} ({{ t('asettings.minutes') }})</span><input v-model.number="settings.lockout_duration_min" type="number" min="1" /></label>
              <label class="field"><span>{{ t('asettings.sessionTimeout') }} ({{ t('asettings.minutes') }})</span><input v-model.number="settings.session_timeout_min" type="number" min="0" /></label>
              <label class="field"><span>{{ t('as.pol.sudo') }} ({{ t('asettings.minutes') }})</span><input v-model.number="settings.sudo_minutes" type="number" min="1" max="60" /></label>
            </div>
            <div class="rounded-xl border border-slate-200 p-3 dark:border-slate-700">
              <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ t('asettings.passwordPolicy') }}</p>
              <div class="mt-2 flex flex-wrap items-center gap-4 text-sm text-slate-600 dark:text-slate-300">
                <label class="flex items-center gap-2">{{ t('asettings.minLength') }} <input v-model.number="settings.password_min_length" type="number" min="8" max="64" class="w-16 rounded-lg border border-slate-200 bg-transparent px-2 py-1 dark:border-slate-700" /></label>
                <label class="flex items-center gap-1.5"><input v-model="settings.password_require_upper" type="checkbox" /> {{ t('asettings.requireUpper') }}</label>
                <label class="flex items-center gap-1.5"><input v-model="settings.password_require_number" type="checkbox" /> {{ t('asettings.requireNumber') }}</label>
                <label class="flex items-center gap-1.5"><input v-model="settings.password_require_symbol" type="checkbox" /> {{ t('asettings.requireSymbol') }}</label>
              </div>
            </div>
          </div>
        </Panel>

        <Panel :title="`🤖 ${t('as.pol.triage')}`" :hint="t('as.pol.triageHint')">
          <div class="space-y-4">
            <div class="grid gap-2 sm:grid-cols-3">
              <button v-for="mode in TRIAGE_MODES" :key="mode" type="button" class="choice" :class="{ active: settings.triage_mode === mode }"
                      @click="settings.triage_mode = mode">
                <b>{{ t(`triage.mode.${mode}`) }}</b><small>{{ t(`triage.mode.${mode}.hint`) }}</small>
              </button>
            </div>
            <label v-if="settings.triage_mode === 'assisted'" class="block text-sm">
              <span class="flex justify-between text-slate-600 dark:text-slate-300">{{ t('triage.threshold') }} <b>{{ settings.triage_threshold }} %</b></span>
              <input v-model.number="settings.triage_threshold" type="range" min="50" max="99" step="1" class="range" />
              <small class="text-xs text-slate-400">{{ t('triage.thresholdHint', { n: settings.triage_threshold }) }}</small>
            </label>
          </div>
        </Panel>

        <Panel :title="`🚨 ${t('as.pol.incidents')}`" :hint="t('as.pol.incidentsHint')">
          <div class="space-y-4">
            <div class="grid gap-3 sm:grid-cols-2">
              <label class="field"><span>{{ t('as.pol.incidentThreshold') }}</span><input v-model.number="settings.incident_threshold" type="number" min="2" max="50" /></label>
              <label class="field"><span>{{ t('as.pol.incidentWindow') }}</span><input v-model.number="settings.incident_window_hours" type="number" min="1" max="720" /></label>
            </div>
            <label class="toggle"><div><p>{{ t('as.pol.autoBlock') }}</p><small>{{ t('as.pol.autoBlockHint') }}</small></div>
              <input v-model="settings.auto_block_incidents" type="checkbox" /></label>
          </div>
        </Panel>
      </div>

      <!-- Sticky save bar -->
      <div class="sticky bottom-4 z-10 flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-white/90 px-5 py-3 shadow-lg backdrop-blur dark:border-slate-700 dark:bg-slate-900/90">
        <p class="text-sm" :class="dirty ? 'text-amber-600' : 'text-slate-400'">{{ dirty ? `● ${t('as.pol.unsaved')}` : `✓ ${t('as.pol.saved')}` }}
          <span class="ml-2 text-xs text-slate-400">🔐 {{ t('as.pol.sudoNote') }}</span></p>
        <div class="flex gap-2">
          <button class="rounded-xl px-4 py-2 text-sm text-slate-500 disabled:opacity-40" :disabled="!dirty" @click="settings = JSON.parse(savedSettings)">{{ t('common.cancel') }}</button>
          <button class="btn-primary" :disabled="!dirty || savingSettings" @click="saveSettings">{{ savingSettings ? t('settings.saving') : t('admin.settings.save') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.field { display: flex; flex-direction: column; gap: 0.35rem; font-size: 0.8rem; font-weight: 500; color: #475569; }
.field em { font-style: normal; color: #94a3b8; font-weight: 400; }
.field input, .input {
  width: 100%; border-radius: 0.75rem; border: 1px solid #e2e8f0; background: #f8fafc; padding: 0.6rem 0.85rem;
  font-size: 0.875rem; color: #0f172a; outline: none; transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
}
.field input:focus, .input:focus { border-color: #60a5fa; background: #fff; box-shadow: 0 0 0 4px rgba(191, 219, 254, 0.5); }
:global(.dark) .field { color: #cbd5e1; }
:global(.dark) .field input, :global(.dark) .input { background: #0f172a; border-color: #334155; color: #f1f5f9; }
.btn-primary {
  border-radius: 0.75rem; background: #0f172a; padding: 0.6rem 1.2rem; font-size: 0.875rem; font-weight: 600; color: white;
  transition: opacity 0.15s, transform 0.15s;
}
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.5; }
:global(.dark) .btn-primary { background: #22d3ee; color: #0f172a; }
.toggle { display: flex; cursor: pointer; align-items: center; justify-content: space-between; gap: 1rem; }
.toggle p { font-size: 0.875rem; font-weight: 500; color: #334155; }
.toggle small { font-size: 0.75rem; color: #94a3b8; }
:global(.dark) .toggle p { color: #e2e8f0; }
.toggle input { appearance: none; width: 2.75rem; height: 1.5rem; flex-shrink: 0; border-radius: 9999px; background: #cbd5e1; position: relative; transition: background 0.2s; cursor: pointer; }
.toggle input::after { content: ''; position: absolute; top: 2px; left: 2px; width: 1.25rem; height: 1.25rem; border-radius: 9999px; background: white; transition: transform 0.2s; box-shadow: 0 1px 3px rgba(0,0,0,.2); }
.toggle input:checked { background: #2563eb; }
.toggle input:checked::after { transform: translateX(1.25rem); }
.choice { display: flex; flex-direction: column; gap: 0.2rem; border-radius: 0.9rem; border: 1px solid #e2e8f0; padding: 0.7rem 0.8rem; text-align: left; transition: all 0.15s; }
.choice b { font-size: 0.85rem; color: #0f172a; }
.choice small { font-size: 0.7rem; line-height: 1.3; color: #64748b; }
.choice:hover { border-color: #93c5fd; }
.choice.active { border-color: #2563eb; background: #eff6ff; box-shadow: 0 0 0 3px rgba(191, 219, 254, 0.6); }
:global(.dark) .choice { border-color: #334155; }
:global(.dark) .choice b { color: #f1f5f9; }
:global(.dark) .choice.active { background: rgba(34, 211, 238, 0.08); border-color: #22d3ee; box-shadow: none; }
.range { margin-top: 0.4rem; width: 100%; accent-color: #2563eb; }
.scan { position: absolute; inset: 0; transform: translateX(-100%); background: linear-gradient(90deg, transparent, rgba(34, 211, 238, 0.12), transparent); animation: scan 5s linear infinite; }
@keyframes scan { to { transform: translateX(100%); } }
@media (prefers-reduced-motion: reduce) { .scan { animation: none; } }
</style>
