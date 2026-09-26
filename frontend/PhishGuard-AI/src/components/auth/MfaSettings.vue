<script setup lang="ts">
import { nextTick, ref } from "vue";
import QRCode from "qrcode";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/stores/auth";
import { useI18n } from "@/i18n";

const { t } = useI18n();

const authStore = useAuthStore();
const qrCanvas = ref<HTMLCanvasElement | null>(null);
const secret = ref("");
const otpauthUri = ref("");
const code = ref("");
const error = ref("");
const message = ref("");
const isLoading = ref(false);

async function setup() {
  isLoading.value = true;
  error.value = "";
  message.value = "";
  try {
    const result = await authService.setupMfa();
    secret.value = result.secret;
    otpauthUri.value = result.otpauth_uri;
    await nextTick();
    if (qrCanvas.value) {
      await QRCode.toCanvas(qrCanvas.value, result.otpauth_uri, {
        width: 220,
        margin: 2,
        errorCorrectionLevel: "M",
      });
    }
  } catch {
    error.value = t('auth.mfa.setupFailed');
  } finally {
    isLoading.value = false;
  }
}

async function enable() {
  if (!/^\d{6}$/.test(code.value)) {
    error.value = t('auth.mfa.codeFormat');
    return;
  }
  isLoading.value = true;
  error.value = "";
  try {
    await authService.enableMfa(code.value);
    authStore.user = { ...authStore.user!, mfa_active: true };
    message.value = t('auth.mfa.enabledMessage');
    code.value = "";
  } catch {
    error.value = t('auth.mfa.invalidCode');
  } finally {
    isLoading.value = false;
  }
}

const disableCode = ref("");

async function disable() {
  if (!/^\d{6}$/.test(disableCode.value)) {
    error.value = t('auth.mfa.codeFormat');
    return;
  }
  isLoading.value = true;
  error.value = "";
  try {
    await authService.disableMfa(disableCode.value);
    disableCode.value = "";
    authStore.user = { ...authStore.user!, mfa_active: false };
    secret.value = "";
    otpauthUri.value = "";
    message.value = t('auth.mfa.disabledMessage');
  } catch {
    error.value = t('auth.mfa.disableFailed');
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <section
    class="bg-white rounded-2xl border border-slate-100 shadow-card p-6 sm:p-8"
  >
    <div class="flex items-start justify-between gap-4">
      <div>
        <p class="text-xs font-semibold uppercase tracking-wider text-blue-600">
          {{ t('auth.mfa.kicker') }}
        </p>
        <h2 class="text-2xl font-bold text-slate-800 font-display mt-1">
          Google Authenticator
        </h2>
        <p class="text-sm text-slate-500 mt-2 max-w-xl">
          {{ t('auth.mfa.description') }}
        </p>
      </div>
      <span
        class="shrink-0 px-3 py-1 rounded-full text-xs font-semibold"
        :class="
          authStore.user?.mfa_active
            ? 'bg-emerald-50 text-emerald-700'
            : 'bg-slate-100 text-slate-500'
        "
      >
        {{ authStore.user?.mfa_active ? t('auth.mfa.enabled') : t('auth.mfa.disabled') }}
      </span>
    </div>

    <div v-if="!authStore.user?.mfa_active && !otpauthUri" class="mt-6">
      <button
        class="px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold disabled:opacity-60"
        :disabled="isLoading"
        @click="setup"
      >
        {{ isLoading ? t('auth.mfa.preparing') : t('auth.mfa.setup') }}
      </button>
    </div>

    <div
      v-if="otpauthUri && !authStore.user?.mfa_active"
      class="mt-6 grid gap-6 md:grid-cols-[240px_1fr] items-start"
    >
      <div class="rounded-xl border border-slate-200 p-2 w-fit">
        <canvas
          ref="qrCanvas"
          :aria-label="t('auth.mfa.qrLabel')"
        ></canvas>
      </div>
      <div>
        <ol class="list-decimal pl-5 text-sm text-slate-600 space-y-2">
          <li>{{ t('auth.mfa.step1') }}</li>
          <li>{{ t('auth.mfa.step2') }}</li>
          <li>{{ t('auth.mfa.step3') }}</li>
        </ol>
        <label class="block text-xs font-semibold text-slate-600 mt-5 mb-1"
          >{{ t('auth.mfa.confirmCode') }}</label
        >
        <input
          v-model="code"
          inputmode="numeric"
          maxlength="6"
          placeholder="123456"
          class="w-full max-w-xs px-3 py-2.5 border border-slate-200 rounded-lg"
        />
        <button
          class="block mt-3 px-4 py-2.5 rounded-lg bg-emerald-600 text-white text-sm font-semibold disabled:opacity-60"
          :disabled="isLoading"
          @click="enable"
        >
          {{ t('auth.mfa.enable') }}
        </button>
        <p class="text-xs text-slate-400 mt-4 break-all">
          {{ t('auth.mfa.manualKey') }} {{ secret }}
        </p>
      </div>
    </div>

    <div v-if="authStore.user?.mfa_active" class="mt-6">
      <p class="text-sm text-slate-600">
        {{ t('auth.mfa.activeInfo') }}
      </p>
      <input
        v-model="disableCode"
        inputmode="numeric"
        maxlength="6"
        :placeholder="t('auth.mfa.disableCode')"
        class="mt-4 block w-full max-w-xs px-3 py-2.5 border border-slate-200 rounded-lg text-center tracking-[0.3em]"
      />
      <button
        class="mt-4 px-4 py-2.5 rounded-lg border border-red-200 text-red-600 text-sm font-semibold disabled:opacity-60"
        :disabled="isLoading"
        @click="disable"
      >
        {{ t('auth.mfa.disable') }}
      </button>
    </div>

    <p
      v-if="message"
      class="mt-5 text-sm text-emerald-700 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2"
    >
      {{ message }}
    </p>
    <p
      v-if="error"
      class="mt-5 text-sm text-red-700 bg-red-50 border border-red-100 rounded-lg px-3 py-2"
    >
      {{ error }}
    </p>
  </section>
</template>
