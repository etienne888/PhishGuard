<script setup lang="ts">
import Navbar from "@/components/Navbar.vue";
import MfaSettings from "@/components/auth/MfaSettings.vue";
import { useAuthStore } from "@/stores/auth";
import { onMounted } from "vue";
import { authService } from "@/services/auth.service";

const authStore = useAuthStore();

onMounted(async () => {
  authStore.user = await authService.me();
});
</script>

<template>
  <Navbar />
  <main class="pt-28 pb-16 px-4 min-h-screen bg-slate-50">
    <div class="max-w-4xl mx-auto">
      <div class="mb-8">
        <p class="text-xs font-semibold uppercase tracking-wider text-blue-600">
          Compte
        </p>
        <h1 class="text-3xl font-bold text-slate-800 font-display mt-1">
          Sécurité du compte
        </h1>
        <p class="text-slate-500 mt-2">{{ authStore.user?.email }}</p>
      </div>
      <MfaSettings />
    </div>
  </main>
</template>
