<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="isOpen"
        class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
        @click.self="closeModal"
      >
        <!-- Login Form -->
        <LoginForm
          v-if="mode === 'login'"
          @close="closeModal"
          @switch-to-register="openRegister"
          @switch-to-demo="openDemo"
        />

        <!-- Register Form -->
        <RegisterForm
          v-else-if="mode === 'register'"
          @close="closeModal"
          @switch-to-login="openLogin"
        />

        <!-- Demo Modal -->
        <div
          v-else-if="mode === 'demo'"
          class="bg-white rounded-2xl max-w-md w-full shadow-2xl p-8 text-center"
        >
          <div
            class="w-20 h-20 mx-auto rounded-full bg-blue-50 flex items-center justify-center text-3xl text-blue-600"
          >
            <i class="fas fa-play"></i>
          </div>
          <h3 class="text-2xl font-bold text-slate-800 mt-4">
            Démo bientôt disponible
          </h3>
          <p class="text-sm text-slate-500 mt-2">
            Découvrez comment PhishGuard-AI détecte le phishing en temps réel.
          </p>
          <button
            class="mt-6 px-6 py-2.5 bg-slate-100 hover:bg-slate-200 rounded-xl text-sm font-medium transition"
            @click="closeModal"
          >
            Fermer
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useAuthStore } from "@/stores/auth";
import LoginForm from "./LoginForm.vue";
import RegisterForm from "./RegisterForm.vue";

const authStore = useAuthStore();

const isOpen = computed(() => authStore.modalMode !== null);
const mode = computed(() => authStore.modalMode);

const closeModal = authStore.closeModal;
const openLogin = () => authStore.openModal("login");
const openRegister = () => authStore.openModal("register");
const openDemo = () => authStore.openModal("demo");
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
