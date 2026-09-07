<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { authService } from "@/services/auth.service";
import Preloader from "@/components/Preloader.vue";
import AuthModal from "@/components/auth/AuthModal.vue";
import NotificationStack from "@/components/NotificationStack.vue";

const isLoading = ref(true);
const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

onMounted(async () => {
  if (route.query.auth === "login") {
    authStore.openModal("login");
  }

  const code = typeof route.query.code === "string" ? route.query.code : null;
  if (!code) return;
  try {
    authStore.user = await authService.completeGoogleLogin(code);
  } finally {
    await router.replace({ path: route.path, query: {} });
  }
});
</script>

<template>
  <Preloader v-if="isLoading" @complete="isLoading = false" />
  <div :class="isLoading ? 'invisible h-0 overflow-hidden' : ''">
    <RouterView />
  </div>
  <AuthModal />
  <NotificationStack />
</template>
