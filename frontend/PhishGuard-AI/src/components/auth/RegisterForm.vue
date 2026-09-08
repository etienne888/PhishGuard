<template>
  <div
    class="bg-white rounded-2xl max-w-md w-full shadow-2xl relative overflow-hidden p-6 sm:p-8"
  >
    <!-- Header -->
    <div class="flex justify-between items-start mb-5">
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
          {{ stepTitle }}
        </h3>
        <p class="text-sm text-slate-500">{{ stepSubtitle }}</p>
      </div>
      <button
        class="text-slate-400 hover:text-slate-600 transition p-1 rounded-lg hover:bg-slate-100"
        @click="$emit('close')"
      >
        <i class="fas fa-xmark text-xl"></i>
      </button>
    </div>

    <!-- Step progress tracker -->
    <div class="flex items-center gap-2 mb-6">
      <template v-for="(item, index) in steps" :key="item.id">
        <div class="flex items-center gap-2 flex-1">
          <div
            class="w-7 h-7 shrink-0 rounded-full flex items-center justify-center text-xs font-semibold transition-colors"
            :class="
              stepIndex > index
                ? 'bg-emerald-500 text-white'
                : stepIndex === index
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-500/30'
                  : 'bg-slate-100 text-slate-400'
            "
          >
            <i v-if="stepIndex > index" class="fas fa-check text-[10px]"></i>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div
            v-if="index < steps.length - 1"
            class="h-0.5 flex-1 rounded transition-colors"
            :class="stepIndex > index ? 'bg-emerald-500' : 'bg-slate-100'"
          ></div>
        </div>
      </template>
    </div>

    <!-- ============================================================ -->
    <!-- STEP 1: ACCOUNT DETAILS (email, phone, password)              -->
    <!-- ============================================================ -->
    <div v-if="step === 'account'" class="space-y-4">
      <form @submit.prevent="submitRegister" class="space-y-4">
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
            Téléphone <span class="text-slate-400">(optionnel)</span>
          </label>
          <PhoneInput
            v-model="form.phone"
            :error="errors.phone"
            @blur="validateField('phone')"
          />
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
          class="w-full py-3 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition disabled:opacity-60 flex items-center justify-center gap-2"
        >
          <i v-if="isSubmitting" class="fas fa-spinner fa-spin"></i>
          {{ isSubmitting ? "Création..." : "Créer le compte" }}
        </button>
        <p
          v-if="authStore.error"
          class="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2"
        >
          {{ authStore.error }}
        </p>
      </form>

      <div class="relative flex items-center py-1">
        <div class="flex-1 border-t border-slate-200"></div>
        <span class="px-4 text-xs text-slate-400 font-medium">OU</span>
        <div class="flex-1 border-t border-slate-200"></div>
      </div>

      <GoogleLoginButton @success="handleGoogleSignup" />

      <p class="text-center text-sm text-slate-500">
        Déjà un compte ?
        <button
          type="button"
          class="text-blue-600 font-medium hover:underline"
          @click="$emit('switch-to-login')"
        >
          Se connecter
        </button>
      </p>
    </div>

    <!-- ============================================================ -->
    <!-- STEP 2: EMAIL VERIFICATION (link or code)                     -->
    <!-- ============================================================ -->
    <div v-else-if="step === 'sent'" class="space-y-5">
      <div v-if="!useCodeMethod" class="text-center space-y-3">
        <div
          class="w-16 h-16 mx-auto rounded-full bg-blue-50 flex items-center justify-center text-2xl text-blue-600"
        >
          <i class="fas fa-envelope-circle-check"></i>
        </div>
        <h4 class="text-lg font-bold text-slate-800">Confirmez votre email</h4>
        <p class="text-sm text-slate-500">
          Un lien de vérification a été envoyé à
          <span class="font-semibold text-slate-700">{{ form.email }}</span
          >. Ouvrez votre boîte mail et cliquez sur le lien pour activer votre
          compte.
        </p>

        <p
          v-if="feedback"
          class="text-xs rounded-lg px-3 py-2"
          :class="
            feedbackIsError
              ? 'text-red-600 bg-red-50 border border-red-200'
              : 'text-emerald-600 bg-emerald-50 border border-emerald-200'
          "
        >
          {{ feedback }}
        </p>

        <button
          type="button"
          :disabled="isResending"
          class="w-full py-2.5 rounded-xl border border-blue-200 text-blue-600 text-sm font-semibold hover:bg-blue-50 transition disabled:opacity-50"
          @click="resendLink"
        >
          <i v-if="isResending" class="fas fa-spinner fa-spin mr-1.5"></i>
          Renvoyer le lien
        </button>

        <button
          type="button"
          class="w-full py-2.5 rounded-xl bg-slate-50 text-slate-600 text-sm font-medium hover:bg-slate-100 transition"
          @click="switchToCode"
        >
          Vérifier avec un code à la place
        </button>
      </div>

      <!-- Fallback: inline OTP code entry for the same email -->
      <OtpVerificationForm
        v-else
        method="email"
        :identifier="form.email"
        @verified="onEmailVerified"
        @back="useCodeMethod = false"
      />
    </div>

    <!-- ============================================================ -->
    <!-- STEP 3: DONE                                                  -->
    <!-- ============================================================ -->
    <div v-else class="text-center space-y-4">
      <div
        class="w-16 h-16 mx-auto rounded-full bg-emerald-50 flex items-center justify-center text-2xl text-emerald-600"
      >
        <i class="fas fa-circle-check"></i>
      </div>
      <h4 class="text-lg font-bold text-slate-800">Email vérifié !</h4>
      <p class="text-sm text-slate-500">
        Votre compte PhishGuard-AI est prêt. Connectez-vous pour commencer à
        analyser vos messages suspects.
      </p>
      <button
        type="button"
        class="w-full py-3 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition"
        @click="finish"
      >
        Se connecter
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { isValidEmail, isStrongEnoughPassword } from "@/utils";
import { api } from "@/services/api";
import GoogleLoginButton from "./GoogleLoginButton.vue";
import PhoneInput from "./PhoneInput.vue";
import OtpVerificationForm from "./OtpVerificationForm.vue";

const emit = defineEmits(["close", "switch-to-login"]);

const authStore = useAuthStore();
const router = useRouter();

type Step = "account" | "sent" | "done";

const steps: { id: Step; label: string }[] = [
  { id: "account", label: "Compte" },
  { id: "sent", label: "Vérification" },
  { id: "done", label: "Terminé" },
];

const step = ref<Step>("account");
const stepIndex = computed(() => steps.findIndex((s) => s.id === step.value));

const stepTitle = computed(() => {
  if (step.value === "account") return "Créer un compte";
  if (step.value === "sent") return "Vérifiez votre email";
  return "Bienvenue à bord";
});

const stepSubtitle = computed(() => {
  if (step.value === "account") return "Rejoignez PhishGuard-AI et restez protégé";
  if (step.value === "sent") return "Une dernière étape avant de commencer";
  return "Votre compte est activé";
});

const form = reactive({
  email: "",
  phone: "",
  password: "",
  confirmPassword: "",
  agreeTerms: false,
});

const errors = reactive({
  email: "",
  phone: "",
  password: "",
  confirmPassword: "",
});

const showPassword = ref(false);
const isSubmitting = ref(false);
const useCodeMethod = ref(false);
const isResending = ref(false);
const feedback = ref("");
const feedbackIsError = ref(false);

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
  if (field === "phone") {
    errors.phone =
      !form.phone || form.phone.length >= 8
        ? ""
        : "Numéro de téléphone invalide.";
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
  validateField("phone");
  validateField("password");
  validateField("confirmPassword");
  return (
    !errors.email &&
    !errors.phone &&
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
    phone: form.phone || undefined,
  });
  isSubmitting.value = false;
  if (registered && !authStore.error) {
    step.value = "sent";
  }
}

async function resendLink() {
  isResending.value = true;
  feedback.value = "";
  try {
    await api.post("/verification/send-email-link", { email: form.email });
    feedback.value = "Un nouveau lien vient d'être envoyé.";
    feedbackIsError.value = false;
  } catch {
    feedback.value = "Impossible de renvoyer le lien pour le moment.";
    feedbackIsError.value = true;
  } finally {
    isResending.value = false;
  }
}

async function switchToCode() {
  feedback.value = "";
  try {
    await api.post("/verification/send-email-code", { email: form.email });
    useCodeMethod.value = true;
  } catch {
    feedback.value = "Impossible d'envoyer un code pour le moment.";
    feedbackIsError.value = true;
  }
}

function onEmailVerified(user: unknown) {
  authStore.setUser(user as any);
  step.value = "done";
}

function finish() {
  emit("close");
  void router.push({ name: "home", query: { auth: "login", email: form.email } });
}

function handleGoogleSignup() {
  emit("close");
  void router.push({ name: "dashboard" });
}
</script>
