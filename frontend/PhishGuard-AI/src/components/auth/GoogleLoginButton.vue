<template>
  <button
    @click="handleGoogleLogin"
    :disabled="isLoading"
    class="w-full py-2.5 border border-slate-200 rounded-xl hover:bg-slate-50 transition text-sm font-medium text-slate-700 flex items-center justify-center gap-3 disabled:opacity-60"
  >
    <svg v-if="!isLoading" class="w-5 h-5" viewBox="0 0 24 24">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
    <i v-else class="fas fa-spinner fa-spin"></i>
    {{ isLoading ? "Connexion..." : "Continuer avec Google" }}
  </button>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { api } from "@/services/api";

const emit = defineEmits(["success", "error"]);

const isLoading = ref(false);

async function handleGoogleLogin() {
  isLoading.value = true;
  try {
    // Initialize Google OAuth
    const data = await api.get<{ authUrl: string }>("/oauth/google/init");
    // Redirect to Google OAuth
    window.location.href = data.authUrl;
  } catch (error) {
    emit("error", error);
  } finally {
    isLoading.value = false;
  }
}

// If Google OAuth redirects back to the app with code
if (window.location.search.includes("code=")) {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get("code");
  if (code) {
    // Exchange code for user info
    api
      .post("/oauth/google/callback", { code })
      .then((user) => emit("success", user))
      .catch((err) => {
        emit("error", err);
      });
  }
}
</script>
