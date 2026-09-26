<template>
  <div class="space-y-4">
    <div class="text-center">
      <div
        class="w-14 h-14 mx-auto rounded-full bg-blue-50 ring-8 ring-blue-50/50 flex items-center justify-center text-2xl text-blue-600"
      >
        <i :class="method === 'phone' ? 'fas fa-mobile-screen-button' : 'fas fa-envelope-open-text'"></i>
      </div>
      <h4 class="text-lg font-bold text-slate-800 mt-3">
        {{ t(method === 'phone' ? 'auth.otp.titleSms' : 'auth.otp.titleEmail') }}
      </h4>
      <p class="text-sm text-slate-500">
        {{ t(method === 'phone' ? 'auth.otp.sentPhone' : 'auth.otp.sentEmail') }}
      </p>
    </div>

    <div v-if="!identifier" class="space-y-2">
      <label class="text-xs font-medium text-slate-600 block">{{
        method === "phone" ? t('auth.otp.phoneNumber') : t('auth.email')
      }}</label>
      <input
        v-model="destination"
        :type="method === 'phone' ? 'tel' : 'email'"
        :placeholder="
          method === 'phone' ? '+237 6XX XXX XXX' : t('auth.emailPlaceholder')
        "
        class="auth-input"
      />
      <button
        type="button"
        class="w-full py-2.5 rounded-full bg-blue-50 text-blue-600 text-sm font-semibold hover:bg-blue-100 transition disabled:opacity-50"
        :disabled="isSubmitting || !destination"
        @click="sendCode"
      >
        {{ t('auth.verify.send') }}
      </button>
    </div>

    <form v-if="codeSent" @submit.prevent="verifyCode">
      <div>
        <label
          class="text-xs font-medium text-slate-600 block mb-2 text-center"
        >
          {{ t('auth.verify.code') }} <span class="text-red-500">*</span>
        </label>
        <div class="flex justify-center gap-2">
          <input
            v-for="i in 6"
            :key="i"
            ref="otpInputs"
            v-model="digits[i - 1]"
            type="text"
            maxlength="1"
            class="w-11 h-13 text-center text-xl font-semibold text-slate-700 bg-slate-50 border border-slate-200 rounded-2xl focus:bg-white focus:ring-4 focus:ring-blue-100 focus:border-blue-300 outline-none transition"
            @input="onInput(i - 1, $event)"
            @keydown="onKeydown(i - 1, $event)"
            @paste="onPaste"
          />
        </div>
        <p v-if="error" class="text-xs text-rose-500 mt-2 text-center">
          {{ error }}
        </p>
        <p class="text-xs text-slate-400 mt-2 text-center">
          {{ t('auth.otp.expiresIn') }}
          <span class="font-medium text-slate-600">{{ timer }}</span
          >s
        </p>
      </div>

      <button
        type="submit"
        :disabled="isSubmitting || !isComplete"
        class="auth-btn mt-5"
      >
        <i v-if="isSubmitting" class="fas fa-spinner fa-spin mr-2"></i>
        {{ isSubmitting ? t('auth.otp.verifying') : t('auth.otp.verify') }}
      </button>
    </form>

    <div class="flex items-center justify-between">
      <button
        @click="$emit('back')"
        class="text-sm text-slate-500 hover:text-slate-700 transition"
      >
        <i class="fas fa-arrow-left mr-1"></i> {{ t('common.back') }}
      </button>
      <button
        @click="resendCode"
        :disabled="timer > 0"
        class="text-sm text-blue-600 hover:underline transition disabled:opacity-50"
      >
        {{ t('auth.otp.resend') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import "./auth.css";
import { ref, computed, onMounted, onUnmounted } from "vue";
import { api } from "@/services/api";
import { useI18n } from "@/i18n";

const { t } = useI18n();

const props = defineProps<{
  method: "phone" | "email";
  identifier?: string;
}>();

const emit = defineEmits(["verified", "back"]);

const digits = ref<string[]>(["", "", "", "", "", ""]);
const otpInputs = ref<HTMLInputElement[]>([]);
const timer = ref(60);
const isSubmitting = ref(false);
const error = ref("");
const destination = ref(props.identifier ?? "");
const codeSent = ref(Boolean(props.identifier));

let interval: ReturnType<typeof setInterval> | null = null;

const isComplete = computed(() => digits.value.every((d) => d.length === 1));

function onInput(index: number, event: Event) {
  const input = event.target as HTMLInputElement;
  const value = input.value.replace(/\D/g, "").slice(0, 1);
  digits.value[index] = value;

  if (value && index < 5) {
    otpInputs.value[index + 1]?.focus();
  }
}

function onKeydown(index: number, event: KeyboardEvent) {
  if (event.key === "Backspace" && !digits.value[index] && index > 0) {
    otpInputs.value[index - 1]?.focus();
  }
}

function onPaste(event: ClipboardEvent) {
  const paste = event.clipboardData?.getData("text") || "";
  const parsed = paste.replace(/\D/g, "").slice(0, 6).split("");
  parsed.forEach((d, i) => {
    if (i < 6) digits.value[i] = d;
  });
  const lastIndex = Math.min(parsed.length, 5);
  otpInputs.value[lastIndex]?.focus();
  event.preventDefault();
}

async function verifyCode() {
  const code = digits.value.join("");
  if (code.length < 6) {
    error.value = t('auth.otp.invalidFormat');
    return;
  }

  isSubmitting.value = true;
  error.value = "";

  try {
    const path =
      props.method === "phone"
        ? "/otp/verify"
        : "/verification/verify-email-code";
    const data = await api.post<{ user: unknown }>(path, {
      code,
      ...(props.method === "phone"
        ? { phone: destination.value }
        : { email: destination.value }),
    });
    emit("verified", data.user);
  } catch (err) {
    error.value = t('auth.otp.verifyFailed');
  } finally {
    isSubmitting.value = false;
  }
}

async function sendCode() {
  if (!destination.value) return;
  isSubmitting.value = true;
  error.value = "";
  try {
    const path =
      props.method === "phone" ? "/otp/send" : "/verification/send-email-code";
    await api.post(
      path,
      props.method === "phone"
        ? { phone: destination.value }
        : { email: destination.value },
    );
    codeSent.value = true;
    startTimer();
  } catch {
    error.value = t('auth.otp.sendFailed');
  } finally {
    isSubmitting.value = false;
  }
}

function startTimer() {
  timer.value = 60;
  if (interval) clearInterval(interval);
  interval = setInterval(() => {
    timer.value--;
    if (timer.value <= 0) {
      clearInterval(interval!);
      interval = null;
    }
  }, 1000);
}

function resendCode() {
  if (timer.value > 0) return;
  startTimer();
  const path =
    props.method === "phone"
      ? "/otp/resend"
      : "/verification/resend-email-code";
  void api.post(
    path,
    props.method === "phone"
      ? { phone: destination.value }
      : { email: destination.value },
  );
}

onMounted(() => {
  if (codeSent.value) startTimer();
});
onUnmounted(() => {
  if (interval) clearInterval(interval);
});
</script>

