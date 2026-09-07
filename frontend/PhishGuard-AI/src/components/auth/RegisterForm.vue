<template>
  <div
    class="bg-white rounded-2xl max-w-md w-full shadow-2xl relative overflow-hidden p-6 sm:p-8"
  >
    <!-- Header -->
    <div class="flex justify-between items-start mb-6">
      <div>
        <div class="flex items-center gap-3 mb-1">
          <div
            class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-blue-500/25"
          >
            <i class="fas fa-shield-halved text-white text-sm"></i>
          </div>
          <span class="text-xl font-extrabold tracking-tight text-slate-800">
            Phish<span class="text-blue-600">Guard</span
            ><span class="text-cyan-500">-AI</span>
          </span>
        </div>
        <h3 class="text-2xl font-bold text-slate-800 font-display">
          Créer un compte
        </h3>
        <p class="text-sm text-slate-500">
          Rejoignez PhishGuard-AI et restez protégé
        </p>
      </div>
      <button
        class="text-slate-400 hover:text-slate-600 transition p-1 rounded-lg hover:bg-slate-100"
        @click="$emit('close')"
      >
        <i class="fas fa-xmark text-xl"></i>
      </button>
    </div>

    <!-- ============================================================ -->
    <!-- STEP 1: EMAIL & PASSWORD                                     -->
    <!-- ============================================================ -->
    <div class="space-y-4">
      <form @submit.prevent="submitRegister">
        <div>
          <label class="text-xs font-medium text-slate-600 block mb-1">
            Email <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.email"
            type="email"
            placeholder="vous@exemple.com"
            class="w-full px-3 py-2.5 border rounded-lg text-sm transition"
            :class="
              errors.email
                ? 'border-red-400'
                : 'border-slate-200 focus:ring-blue-500/30 focus:border-blue-500'
            "
            @blur="validateField('email')"
            required
          />
          <p v-if="errors.email" class="text-xs text-red-500 mt-1">
            {{ errors.email }}
          </p>
        </div>

        <div>
          <label class="text-xs font-medium text-slate-600 block mb-1">
            Mot de passe <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              class="w-full px-3 py-2.5 border rounded-lg text-sm transition pr-10"
              :class="
                errors.password
                  ? 'border-red-400'
                  : 'border-slate-200 focus:ring-blue-500/30 focus:border-blue-500'
              "
              @blur="validateField('password')"
              required
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
            >
              <i :class="showPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
            </button>
          </div>

          <!-- Password Requirements -->
          <div class="mt-2 space-y-1">
            <p
              v-for="req in passwordRequirements"
              :key="req.id"
              class="text-xs flex items-center gap-1.5 transition-colors"
              :class="req.passed ? 'text-emerald-600' : 'text-slate-400'"
            >
              <i
                :class="req.passed ? 'fas fa-check-circle' : 'fas fa-circle'"
              ></i>
              {{ req.label }}
            </p>
          </div>
        </div>

        <div>
          <label class="text-xs font-medium text-slate-600 block mb-1">
            Confirmer le mot de passe <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.confirmPassword"
            type="password"
            placeholder="••••••••"
            class="w-full px-3 py-2.5 border rounded-lg text-sm transition"
            :class="
              errors.confirmPassword
                ? 'border-red-400'
                : 'border-slate-200 focus:ring-blue-500/30 focus:border-blue-500'
            "
            @blur="validateField('confirmPassword')"
            required
          />
          <p v-if="errors.confirmPassword" class="text-xs text-red-500 mt-1">
            {{ errors.confirmPassword }}
          </p>
        </div>

        <div class="flex items-start gap-2">
          <input
            type="checkbox"
            v-model="form.agreeTerms"
            class="mt-0.5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
          />
          <label class="text-xs text-slate-600">
            J'accepte les
            <button type="button" class="text-blue-600 hover:underline">
              Conditions d'utilisation
            </button>
          </label>
        </div>

        <button
          type="submit"
          :disabled="!form.agreeTerms || isSubmitting"
          class="w-full py-3 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition disabled:opacity-60"
        >
          {{ isSubmitting ? "Création..." : "Créer le compte" }}
        </button>
        <p
          v-if="authStore.error"
          class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2"
        >
          {{ authStore.error }}
        </p>
      </form>

      <GoogleLoginButton @success="handleGoogleSignup" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { isValidEmail, isStrongEnoughPassword } from "@/utils";
import GoogleLoginButton from "./GoogleLoginButton.vue";

const emit = defineEmits(["close", "switch-to-login"]);

const authStore = useAuthStore();
const router = useRouter();

const form = reactive({
  email: "",
  password: "",
  confirmPassword: "",
  agreeTerms: false,
});

const errors = reactive({
  email: "",
  password: "",
  confirmPassword: "",
});

const showPassword = ref(false);
const isSubmitting = ref(false);

const passwordRequirements = computed(() => [
  {
    id: "length",
    label: "Au moins 8 caractères",
    passed: form.password.length >= 8,
  },
  {
    id: "uppercase",
    label: "Au moins une majuscule",
    passed: /[A-Z]/.test(form.password),
  },
  {
    id: "lowercase",
    label: "Au moins une minuscule",
    passed: /[a-z]/.test(form.password),
  },
  {
    id: "number",
    label: "Au moins un chiffre",
    passed: /[0-9]/.test(form.password),
  },
]);

function validateField(field: keyof typeof errors) {
  if (field === "email") {
    errors.email = isValidEmail(form.email) ? "" : "Adresse email invalide.";
  }
  if (field === "password") {
    errors.password = isStrongEnoughPassword(form.password)
      ? ""
      : "Le mot de passe ne respecte pas les critères.";
  }
  if (field === "confirmPassword") {
    errors.confirmPassword =
      form.confirmPassword === form.password
        ? ""
        : "Les mots de passe ne correspondent pas.";
  }
}

function validateForm(): boolean {
  validateField("email");
  validateField("password");
  validateField("confirmPassword");
  return (
    !errors.email &&
    !errors.password &&
    !errors.confirmPassword &&
    form.agreeTerms
  );
}

async function submitRegister() {
  if (!validateForm()) return;
  isSubmitting.value = true;
  const registered = await authStore.register({
    email: form.email,
    password: form.password,
    confirmPassword: form.confirmPassword,
  });
  isSubmitting.value = false;
  if (registered && !authStore.error) {
    emit("close");
    await router.push({
      name: "home",
      query: { auth: "login", registered: "true", email: form.email },
    });
  }
}

function handleGoogleSignup(user: any) {
  emit("close");
  void router.push({ name: "dashboard" });
}
</script>
