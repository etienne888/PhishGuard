<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { setSudoPrompt } from '@/services/http'
import { socService } from '@/services/soc.service'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from '@/i18n'

/**
 * Step-up authentication dialog. Registered as the global sudo prompt: when a
 * sensitive request answers SUDO_REQUIRED, apiFetch awaits this dialog and
 * replays the request if the admin confirmed their identity.
 */
const { t } = useI18n()
const auth = useAuthStore()
const open = ref(false)
const password = ref('')
const code = ref('')
const error = ref('')
const busy = ref(false)
const input = ref<HTMLInputElement | null>(null)
let resolver: ((ok: boolean) => void) | null = null

function prompt(): Promise<boolean> {
  password.value = code.value = error.value = ''
  open.value = true
  void nextTick(() => input.value?.focus())
  return new Promise((resolve) => { resolver = resolve })
}

function close(result: boolean) {
  open.value = false
  resolver?.(result)
  resolver = null
}

async function confirm() {
  busy.value = true
  error.value = ''
  try {
    await socService.sudo(password.value, code.value || undefined)
    close(true)
  } catch {
    error.value = t('sudo.failed')
  } finally {
    busy.value = false
  }
}

onMounted(() => setSudoPrompt(prompt))
onBeforeUnmount(() => { setSudoPrompt(null); close(false) })
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-[70] grid place-items-center bg-slate-950/60 p-4 backdrop-blur-sm" @click.self="close(false)">
      <form class="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-700" @submit.prevent="confirm">
        <div class="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-amber-50 text-2xl ring-8 ring-amber-50/50 dark:bg-amber-500/10 dark:ring-amber-500/5">🔐</div>
        <h2 class="mt-4 text-center text-lg font-bold text-slate-900 dark:text-white">{{ t('sudo.title') }}</h2>
        <p class="mt-1 text-center text-sm text-slate-500">{{ t('sudo.text') }}</p>
        <input ref="input" v-model="password" type="password" required autocomplete="current-password" :placeholder="t('auth.password')"
               class="mt-5 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-sm outline-none focus:border-blue-400 focus:bg-white dark:border-slate-700 dark:bg-slate-800" />
        <input v-if="auth.user?.mfa_active" v-model="code" inputmode="numeric" maxlength="6" required :placeholder="t('sudo.code')"
               class="mt-2 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-2.5 text-center text-sm tracking-[0.4em] outline-none focus:border-blue-400 dark:border-slate-700 dark:bg-slate-800" />
        <p v-if="error" class="mt-2 text-center text-xs text-red-600">{{ error }}</p>
        <div class="mt-5 flex gap-2">
          <button type="button" class="flex-1 rounded-xl border border-slate-200 py-2.5 text-sm font-medium dark:border-slate-700" @click="close(false)">{{ t('common.cancel') }}</button>
          <button type="submit" :disabled="busy || !password" class="flex-1 rounded-xl bg-slate-900 py-2.5 text-sm font-semibold text-white disabled:opacity-50 dark:bg-cyan-500 dark:text-slate-900">
            {{ busy ? '…' : t('sudo.confirm') }}
          </button>
        </div>
        <p class="mt-3 text-center text-[11px] text-slate-400">{{ t('sudo.hint') }}</p>
      </form>
    </div>
  </Teleport>
</template>
