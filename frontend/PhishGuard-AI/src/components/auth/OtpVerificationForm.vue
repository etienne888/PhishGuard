<template>
  <div class="space-y-4">
    <div class="text-center">
      <div
        class="w-16 h-16 mx-auto rounded-full bg-blue-50 flex items-center justify-center text-2xl text-blue-600"
      >
        <i class="fas fa-mobile-screen-button"></i>
      </div>
      <h4 class="text-lg font-bold text-slate-800 mt-3">
        Vérification par {{ method === "phone" ? "SMS" : "Email" }}
      </h4>
      <p class="text-sm text-slate-500">
        Un code a été envoyé à votre
        {{ method === "phone" ? "téléphone" : "email" }}
      </p>
    </div>

    <div v-if="!identifier" class="space-y-2">
      <label class="text-xs font-medium text-slate-600 block">{{
        method === "phone" ? "Numéro de téléphone" : "Email"
      }}</label>
      <input
        v-model="destination"
        :type="method === 'phone' ? 'tel' : 'email'"
        :placeholder="
          method === 'phone' ? '+237 6XX XXX XXX' : 'vous@exemple.com'
        "
        class="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm"
      />
      <button
        type="button"
        class="w-full py-2.5 rounded-lg border border-blue-200 text-blue-600 text-sm font-semibold disabled:opacity-50"
        :disabled="isSubmitting || !destination"
        @click="sendCode"
      >
        Envoyer le code
      </button>
    </div>

    <form v-if="codeSent" @submit.prevent="verifyCode">
      <div>
        <label
          class="text-xs font-medium text-slate-600 block mb-2 text-center"
        >
          Code de vérification <span class="text-red-500">*</span>
        </label>
        <div class="flex justify-center gap-2">
          <input
            v-for="i in 6"
            :key="i"
            ref="otpInputs"
            v-model="digits[i - 1]"
            type="text"
            maxlength="1"
            class="w-11 h-14 text-center text-xl font-bold border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition"
            @input="onInput(i - 1, $event)"
            @keydown="onKeydown(i - 1, $event)"
            @paste="onPaste"
          />
        </div>
        <p v-if="error" class="text-xs text-red-500 mt-2 text-center">
          {{ error }}
        </p>
        <p class="text-xs text-slate-400 mt-2 text-center">
          Le code expire dans
          <span class="font-medium text-slate-600">{{ timer }}</span
          >s
        </p>
      </div>

      <button
        type="submit"
        :disabled="isSubmitting || !isComplete"
        class="w-full py-3 mt-4 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition disabled:opacity-60"
      >
        <i v-if="isSubmitting" class="fas fa-spinner fa-spin mr-2"></i>
        {{ isSubmitting ? "Vérification..." : "Vérifier" }}
      </button>
    </form>

    <div class="flex items-center justify-between">
      <button
        @click="$emit('back')"
        class="text-sm text-slate-500 hover:text-slate-700 transition"
      >
        <i class="fas fa-arrow-left mr-1"></i> Retour
      </button>
      <button
        @click="resendCode"
        :disabled="timer > 0"
        class="text-sm text-blue-600 hover:underline transition disabled:opacity-50"
      >
        Renvoyer le code
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { api } from "@/services/api";

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
    error.value = "Code invalide (6 chiffres requis).";
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
    error.value = "Erreur de vérification";
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
    error.value = "Impossible d'envoyer le code.";
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
