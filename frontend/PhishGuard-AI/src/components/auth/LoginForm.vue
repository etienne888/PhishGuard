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
          Content de vous revoir
        </h3>
        <p class="text-sm text-slate-500">
          Connectez-vous à votre compte PhishGuard-AI
        </p>
      </div>
      <button
        class="text-slate-400 hover:text-slate-600 transition p-1 rounded-lg hover:bg-slate-100"
        aria-label="Fermer"
        @click="$emit('close')"
      >
        <i class="fas fa-xmark text-xl"></i>
      </button>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 bg-slate-100 rounded-xl p-1 mb-6">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="flex-1 py-2 text-sm font-medium rounded-lg transition-all duration-200"
        :class="
          activeTab === tab.id
            ? 'bg-white shadow-sm text-slate-800'
            : 'text-slate-500 hover:text-slate-700'
        "
      >
        <i :class="tab.icon" class="mr-1.5"></i>
        {{ tab.label }}
      </button>
    </div>

    <!-- ============================================================ -->
    <!-- TAB 1: EMAIL & PASSWORD                                       -->
    <!-- ============================================================ -->
    <div v-if="activeTab === 'email'" class="space-y-4">
      <form @submit.prevent="handleEmailLogin">
        <div>
          <label class="text-xs font-medium text-slate-600 block mb-1">
            Email <span class="text-red-500">*</span>
          </label>
          <input
            v-model="emailForm.email"
            type="email"
            placeholder="vous@exemple.com"
            class="w-full px-3 py-2.5 border rounded-lg text-sm transition"
            :class="
              emailErrors.email
                ? 'border-red-400 focus:ring-red-500/30'
                : 'border-slate-200 focus:ring-blue-500/30 focus:border-blue-500'
            "
            @blur="validateEmailField('email')"
            required
          />
          <p
            v-if="emailErrors.email"
            class="text-xs text-red-500 mt-1 flex items-center gap-1"
          >
            <i class="fas fa-exclamation-circle text-[10px]"></i>
            {{ emailErrors.email }}
          </p>
        </div>

        <div>
          <div class="flex items-center justify-between mb-1">
            <label class="text-xs font-medium text-slate-600 block">
              Mot de passe <span class="text-red-500">*</span>
            </label>
            <button
              type="button"
              class="text-xs text-blue-600 hover:underline font-medium"
            >
              Mot de passe oublié ?
            </button>
          </div>
          <div class="relative">
            <input
              v-model="emailForm.password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="••••••••"
              class="w-full px-3 py-2.5 border rounded-lg text-sm transition pr-10"
              :class="
                emailErrors.password
                  ? 'border-red-400 focus:ring-red-500/30'
                  : 'border-slate-200 focus:ring-blue-500/30 focus:border-blue-500'
              "
              @blur="validateEmailField('password')"
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
        </div>

        <div class="flex items-center justify-between">
          <label
            class="flex items-center gap-2 text-sm text-slate-600 cursor-pointer"
          >
            <input
              type="checkbox"
              v-model="rememberMe"
              class="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
            />
            Se souvenir de moi
          </label>
        </div>

        <p
          v-if="authError"
          class="text-sm text-red-500 bg-red-50 p-2 rounded-lg border border-red-200 flex items-center gap-2"
        >
          <i class="fas fa-triangle-exclamation"></i>
          {{ authError }}
        </p>

        <button
          type="submit"
          :disabled="isSubmitting"
          class="w-full py-3 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition disabled:opacity-60 flex items-center justify-center gap-2"
        >
          <i v-if="isSubmitting" class="fas fa-spinner fa-spin"></i>
          {{ isSubmitting ? "Connexion en cours..." : "Se connecter" }}
        </button>
      </form>

      <div class="relative flex items-center py-2">
        <div class="flex-1 border-t border-slate-200"></div>
        <span class="px-4 text-xs text-slate-400 font-medium">OU</span>
        <div class="flex-1 border-t border-slate-200"></div>
      </div>

      <!-- Social Login Buttons -->
      <GoogleLoginButton @success="handleGoogleLogin" />

      <div
        v-if="authStore.mfaRequired"
        class="mt-4 rounded-xl border border-blue-100 bg-blue-50 p-4"
      >
        <label class="text-xs font-medium text-slate-700 block mb-2"
          >Code de votre application d'authentification</label
        >
        <input
          v-model="mfaCode"
          inputmode="numeric"
          maxlength="6"
          class="w-full px-3 py-2.5 border border-blue-200 rounded-lg text-sm"
          placeholder="123456"
        />
        <button
          type="button"
          class="w-full mt-3 py-2.5 rounded-lg bg-blue-600 text-white text-sm font-semibold disabled:opacity-60"
          :disabled="isSubmitting || mfaCode.length !== 6"
          @click="verifyMfa"
        >
          Vérifier le code
        </button>
      </div>
    </div>

    <!-- ============================================================ -->
    <!-- TAB 2: PHONE & OTP                                            -->
    <!-- ============================================================ -->
    <div v-if="activeTab === 'phone'">
      <OtpVerificationForm
        method="phone"
        @verified="handleOTPVerified"
        @back="activeTab = 'email'"
      />
    </div>

    <!-- ============================================================ -->
    <!-- TAB 3: EMAIL CODE                                             -->
    <!-- ============================================================ -->
    <div v-if="activeTab === 'emailCode'">
      <EmailCodeForm
        @verified="handleEmailCodeVerified"
        @back="activeTab = 'email'"
      />
    </div>

    <!-- Footer -->
    <div class="mt-6 pt-4 border-t border-slate-200">
      <p class="text-center text-sm text-slate-500">
        Pas encore de compte ?
        <button
          @click="$emit('switch-to-register')"
          class="text-blue-600 font-medium hover:underline"
        >
          S'inscrire
        </button>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { isValidEmail } from "@/utils";
import GoogleLoginButton from "./GoogleLoginButton.vue";
import OtpVerificationForm from "./OtpVerificationForm.vue";
import EmailCodeForm from "./EmailCodeForm.vue";

const emit = defineEmits(["close", "switch-to-register", "switch-to-demo"]);

const authStore = useAuthStore();
const router = useRouter();

// Tabs
const tabs = [
  { id: "email", label: "Email", icon: "fas fa-envelope" },
  { id: "phone", label: "Téléphone", icon: "fas fa-phone" },
  { id: "emailCode", label: "Code Email", icon: "fas fa-key" },
];
const activeTab = ref("email");

// Email form
const emailForm = reactive({ email: "", password: "" });
const emailErrors = reactive({ email: "", password: "" });
const showPassword = ref(false);
const rememberMe = ref(false);
const mfaCode = ref("");

const isSubmitting = ref(false);
const authError = ref("");

function validateEmailField(field: keyof typeof emailErrors) {
  if (field === "email") {
    emailErrors.email = isValidEmail(emailForm.email)
      ? ""
      : "Adresse email invalide.";
  }
  if (field === "password") {
    emailErrors.password =
      emailForm.password.length >= 8 ? "" : "Minimum 8 caractères.";
  }
}

async function handleEmailLogin() {
  validateEmailField("email");
  validateEmailField("password");
  if (emailErrors.email || emailErrors.password) return;

  isSubmitting.value = true;
  authError.value = "";
  try {
    await authStore.login({
      email: emailForm.email,
      password: emailForm.password,
    });
    if (!authStore.error && authStore.user) {
      emit("close");
      await router.push({ name: "dashboard" });
    }
  } catch (err: any) {
    authError.value = err.message || "Erreur de connexion";
  } finally {
    isSubmitting.value = false;
  }
}

async function verifyMfa() {
  isSubmitting.value = true;
  await authStore.verifyMfa(mfaCode.value);
  if (!authStore.error && authStore.user) {
    emit("close");
    await router.push({ name: "dashboard" });
  }
  isSubmitting.value = false;
}

function handleGoogleLogin(user: any) {
  authStore.user = user.user ?? user;
  emit("close");
  void router.push({ name: "dashboard" });
}

function handleOTPVerified(user: any) {
  authStore.user = user;
  emit("close");
  void router.push({ name: "dashboard" });
}

function handleEmailCodeVerified(user: any) {
  authStore.user = user;
  emit("close");
  void router.push({ name: "dashboard" });
}
</script>
