<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { authService } from "@/services/auth.service";
import Preloader from "@/components/Preloader.vue";
import AuthModal from "@/components/auth/AuthModal.vue";
import NotificationStack from "@/components/NotificationStack.vue";
import { useI18n } from "@/i18n";

const isLoading = ref(true);
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();
const { t } = useI18n();

// Offline banner (the checker queues messages and runs them when back online)
const offline = ref(typeof navigator !== "undefined" && navigator.onLine === false);
const setOnline = () => (offline.value = false);
const setOffline = () => (offline.value = true);
window.addEventListener("online", setOnline);
window.addEventListener("offline", setOffline);
onBeforeUnmount(() => {
  window.removeEventListener("online", setOnline);
  window.removeEventListener("offline", setOffline);
});

// Keyboard / screen-reader users: jump over the navigation
function skipToContent() {
  const main = document.querySelector("main");
  if (!main) return;
  main.setAttribute("tabindex", "-1");
  main.focus();
}

onMounted(async () => {
  if (route.query.auth === "login") {
    authStore.openModal("login");
  }

  const code = typeof route.query.code === "string" ? route.query.code : null;
  if (code) {
    try {
      authStore.user = await authService.completeGoogleLogin(code);
    } finally {
      await router.replace({ path: route.path, query: {} });
    }
    return;
  }

  authStore.setUser(await authService.me());
});
</script>

<template>
  <a href="#main" class="skip-link" @click.prevent="skipToContent">{{ t("ux.a11y.skip") }}</a>
  <div v-if="offline" class="offline-bar" role="status">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M1 1l22 22M8.5 16.1a5 5 0 0 1 7 0M12 20h.01" stroke-linecap="round" /></svg>
    {{ t("ux.a11y.offline") }}
  </div>
  <Preloader v-if="isLoading" @complete="isLoading = false" />
  <div :class="isLoading ? 'invisible h-0 overflow-hidden' : ''">
    <RouterView />
  </div>
  <AuthModal />
  <NotificationStack />
</template>

<style>
.skip-link {
  position: fixed;
  left: 1rem;
  top: -4rem;
  z-index: 100;
  padding: 0.6rem 1rem;
  border-radius: 0.75rem;
  background: #2563eb;
  color: white;
  font-weight: 600;
  transition: top 0.2s ease;
}
.skip-link:focus { top: 1rem; }
.offline-bar {
  position: fixed;
  left: 50%;
  top: 4.5rem;
  z-index: 60;
  transform: translateX(-50%);
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.4rem 0.9rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #92400e;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  box-shadow: 0 8px 20px -12px rgba(146, 64, 14, 0.6);
}
</style>
