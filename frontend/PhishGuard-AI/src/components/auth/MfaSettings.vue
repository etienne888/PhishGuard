<script setup lang="ts">
import { nextTick, ref } from "vue";
import QRCode from "qrcode";
import { authService } from "@/services/auth.service";
import { useAuthStore } from "@/stores/auth";

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
    error.value = "Impossible de préparer Google Authenticator.";
  } finally {
    isLoading.value = false;
  }
}

async function enable() {
  if (!/^\d{6}$/.test(code.value)) {
    error.value = "Entrez un code à 6 chiffres.";
    return;
  }
  isLoading.value = true;
  error.value = "";
  try {
    await authService.enableMfa(code.value);
    authStore.user = { ...authStore.user!, mfa_active: true };
    message.value = "Google Authenticator est maintenant activé.";
    code.value = "";
  } catch {
    error.value = "Code invalide ou expiré.";
  } finally {
    isLoading.value = false;
  }
}

async function disable() {
  isLoading.value = true;
  error.value = "";
  try {
    await authService.disableMfa();
    authStore.user = { ...authStore.user!, mfa_active: false };
    secret.value = "";
    otpauthUri.value = "";
    message.value = "Google Authenticator a été désactivé.";
  } catch {
    error.value = "Impossible de désactiver la double authentification.";
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
          Sécurité
        </p>
        <h2 class="text-2xl font-bold text-slate-800 font-display mt-1">
          Google Authenticator
        </h2>
        <p class="text-sm text-slate-500 mt-2 max-w-xl">
          Ajoutez une deuxième étape de connexion avec un code généré sur votre
          téléphone.
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
        {{ authStore.user?.mfa_active ? "Activé" : "Désactivé" }}
      </span>
    </div>

    <div v-if="!authStore.user?.mfa_active && !otpauthUri" class="mt-6">
      <button
        class="px-4 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold disabled:opacity-60"
        :disabled="isLoading"
        @click="setup"
      >
        {{ isLoading ? "Préparation..." : "Configurer Google Authenticator" }}
      </button>
    </div>

    <div
      v-if="otpauthUri && !authStore.user?.mfa_active"
      class="mt-6 grid gap-6 md:grid-cols-[240px_1fr] items-start"
    >
      <div class="rounded-xl border border-slate-200 p-2 w-fit">
        <canvas
          ref="qrCanvas"
          aria-label="QR code Google Authenticator"
        ></canvas>
      </div>
      <div>
        <ol class="list-decimal pl-5 text-sm text-slate-600 space-y-2">
          <li>Ouvrez Google Authenticator sur votre téléphone.</li>
          <li>Scannez le QR code affiché.</li>
          <li>Entrez le code à 6 chiffres généré.</li>
        </ol>
        <label class="block text-xs font-semibold text-slate-600 mt-5 mb-1"
          >Code de confirmation</label
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
          Activer la protection
        </button>
        <p class="text-xs text-slate-400 mt-4 break-all">
          Clé manuelle : {{ secret }}
        </p>
      </div>
    </div>

    <div v-if="authStore.user?.mfa_active" class="mt-6">
      <p class="text-sm text-slate-600">
        Votre compte demandera un code Authenticator à chaque nouvelle
        connexion.
      </p>
      <button
        class="mt-4 px-4 py-2.5 rounded-lg border border-red-200 text-red-600 text-sm font-semibold disabled:opacity-60"
        :disabled="isLoading"
        @click="disable"
      >
        Désactiver Google Authenticator
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
