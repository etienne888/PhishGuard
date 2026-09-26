<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import MfaSettings from '@/components/auth/MfaSettings.vue'
import { userAccountService, type UserProfile } from '@/services/userAccount.service'
import { ApiError } from '@/services/http'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { formatDate } from '@/utils/risk'
import { useI18n } from '@/i18n'

const emit = defineEmits<{ profileChanged: [profile: UserProfile] }>()
const auth = useAuthStore()
const toast = useNotificationsStore()
const { t } = useI18n()

const section = ref<'profile' | 'security'>('profile')
const profile = ref<UserProfile | null>(null)
const name = ref('')
const email = ref('')
const emailPassword = ref('')
const saving = ref(false)
const avatarInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const changingPassword = ref(false)

const emailChanged = computed(() => profile.value && email.value.trim().toLowerCase() !== profile.value.email)
const initials = computed(() => (profile.value?.full_name || profile.value?.email || '?').slice(0, 2).toUpperCase())

function apply(next: UserProfile) {
  profile.value = next
  name.value = next.full_name ?? ''
  email.value = next.email
  emailPassword.value = ''
  if (auth.user) auth.setUser({ ...auth.user, email: next.email, displayName: next.full_name ?? undefined, mfa_active: next.mfa_active })
  emit('profileChanged', next)
}

const message = (e: unknown, fallback: string) => (e instanceof ApiError ? e.message : fallback)

onMounted(async () => {
  try { apply(await userAccountService.getProfile()) } catch { /* toast already shown by apiFetch */ }
})

async function saveProfile() {
  saving.value = true
  try {
    apply(await userAccountService.updateProfile({
      full_name: name.value,
      ...(emailChanged.value ? { email: email.value, current_password: emailPassword.value } : {}),
    }))
    toast.push(emailChanged.value ? t('settings.savedVerifyEmail') : t('settings.saved'), 'success')
  } catch (e) {
    toast.push(message(e, t('settings.saveFailed')), 'error')
  } finally {
    saving.value = false
  }
}

async function onAvatarChosen(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    toast.push(t('settings.imageTooLarge'), 'error')
    return
  }
  uploading.value = true
  try {
    apply(await userAccountService.uploadAvatar(file))
    toast.push(t('settings.avatarUpdated'), 'success')
  } catch (e) {
    toast.push(message(e, t('settings.avatarFailed')), 'error')
  } finally {
    uploading.value = false
  }
}

async function removeAvatar() {
  try { apply(await userAccountService.deleteAvatar()) } catch { /* toast shown */ }
}

async function changePassword() {
  if (newPassword.value.length < 8) return toast.push(t('settings.passwordTooShort', { n: 8 }), 'error')
  if (newPassword.value !== confirmPassword.value) return toast.push(t('auth.errors.passwordMismatch'), 'error')
  changingPassword.value = true
  try {
    await userAccountService.changePassword(currentPassword.value, newPassword.value)
    currentPassword.value = newPassword.value = confirmPassword.value = ''
    toast.push(t('settings.passwordChanged'), 'success')
  } catch (e) {
    toast.push(message(e, t('settings.passwordFailed')), 'error')
  } finally {
    changingPassword.value = false
  }
}
</script>

<template>
  <div class="space-y-4">
    <div class="inline-flex rounded-xl bg-slate-100 p-1 text-sm">
      <button v-for="s in [{ id: 'profile', label: `👤 ${t('settings.profile')}` }, { id: 'security', label: `🔒 ${t('settings.security')}` }] as const" :key="s.id"
              class="rounded-lg px-4 py-1.5 font-medium transition"
              :class="section === s.id ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500'" @click="section = s.id">
        {{ s.label }}
      </button>
    </div>

    <!-- PROFILE -->
    <div v-if="section === 'profile'" class="space-y-4">
      <div class="rounded-2xl border border-slate-200 bg-white p-5">
        <h3 class="font-semibold text-slate-800">{{ t('settings.avatar') }}</h3>
        <div class="mt-3 flex items-center gap-4">
          <img v-if="profile?.avatar_url" :src="profile.avatar_url" :alt="t('settings.avatar')" class="h-20 w-20 rounded-full object-cover ring-2 ring-slate-100" />
          <div v-else class="grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-blue-600 to-cyan-500 text-xl font-bold text-white">{{ initials }}</div>
          <div class="flex flex-wrap gap-2">
            <button class="rounded-xl bg-slate-800 px-4 py-2 text-sm font-medium text-white disabled:opacity-60" :disabled="uploading" @click="avatarInput?.click()">
              {{ uploading ? t('settings.uploading') : t('settings.changeAvatar') }}
            </button>
            <button v-if="profile?.avatar_url" class="rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-600" @click="removeAvatar">{{ t('common.delete') }}</button>
            <p class="w-full text-xs text-slate-400">{{ t('settings.avatarHint') }}</p>
          </div>
          <input ref="avatarInput" type="file" accept="image/png,image/jpeg,image/webp" class="hidden" @change="onAvatarChosen" />
        </div>
      </div>

      <form class="space-y-3 rounded-2xl border border-slate-200 bg-white p-5" @submit.prevent="saveProfile">
        <h3 class="font-semibold text-slate-800">{{ t('settings.personal') }}</h3>
        <label class="block text-sm">
          <span class="text-slate-600">{{ t('settings.fullName') }}</span>
          <input v-model="name" maxlength="255" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-blue-400" :placeholder="t('settings.namePlaceholder')" />
        </label>
        <label class="block text-sm">
          <span class="text-slate-600">{{ t('settings.email') }}</span>
          <input v-model="email" type="email" required class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-blue-400" />
          <span v-if="profile && !profile.email_verified" class="mt-1 block text-xs text-amber-600">⚠️ {{ t('settings.unverified') }}</span>
        </label>
        <label v-if="emailChanged" class="block text-sm">
          <span class="text-slate-600">{{ t('settings.currentPassword') }} <span class="text-slate-400">({{ t('settings.requiredForEmail') }})</span></span>
          <input v-model="emailPassword" type="password" required autocomplete="current-password" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-blue-400" />
        </label>
        <div class="flex items-center justify-between pt-1">
          <span class="text-xs text-slate-400">{{ t('settings.memberSince', { date: formatDate(profile?.created_at) }) }}</span>
          <button type="submit" class="rounded-xl bg-blue-600 px-5 py-2 text-sm font-semibold text-white disabled:opacity-60" :disabled="saving">
            {{ saving ? t('settings.saving') : t('common.save') }}
          </button>
        </div>
      </form>
    </div>

    <!-- SECURITY -->
    <div v-else class="space-y-4">
      <div class="rounded-2xl border border-slate-200 bg-white p-5">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-800">{{ t('settings.mfaTitle') }}</h3>
            <p class="mt-1 text-sm text-slate-500">
              {{ t('settings.mfaText') }}
            </p>
          </div>
          <span class="flex-shrink-0 rounded-full px-3 py-1 text-xs font-semibold"
                :class="auth.user?.mfa_active ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'">
            {{ auth.user?.mfa_active ? `✓ ${t('common.enabled')}` : t('common.disabled') }}
          </span>
        </div>
        <div class="mt-4"><MfaSettings /></div>
      </div>

      <form class="space-y-3 rounded-2xl border border-slate-200 bg-white p-5" @submit.prevent="changePassword">
        <h3 class="font-semibold text-slate-800">{{ t('settings.changePassword') }}</h3>
        <input v-model="currentPassword" type="password" required autocomplete="current-password" :placeholder="t('settings.currentPassword')"
               class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400" />
        <input v-model="newPassword" type="password" required minlength="8" autocomplete="new-password" :placeholder="t('settings.newPassword', { n: 8 })"
               class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400" />
        <input v-model="confirmPassword" type="password" required autocomplete="new-password" :placeholder="t('settings.confirmPassword')"
               class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400" />
        <div class="flex justify-end">
          <button type="submit" class="rounded-xl bg-slate-800 px-5 py-2 text-sm font-semibold text-white disabled:opacity-60" :disabled="changingPassword">
            {{ changingPassword ? t('settings.changing') : t('settings.changePassword') }}
          </button>
        </div>
      </form>

      <div class="rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-600">
        {{ t('settings.lastLogin') }} <b>{{ formatDate(profile?.last_login) }}</b>
        <span v-if="profile?.auth_provider === 'google'" class="block mt-1 text-xs text-slate-400">{{ t('settings.google') }}</span>
      </div>
    </div>
  </div>
</template>
