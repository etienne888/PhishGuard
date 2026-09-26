<template>
  <div
    class="auth-card bg-white rounded-3xl max-w-md w-full relative overflow-y-auto max-h-[92vh] px-6 py-7 sm:px-9 sm:py-8"
  >
    <button
      class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition w-9 h-9 rounded-full hover:bg-slate-100 flex items-center justify-center"
      @click="$emit('close')"
    >
      <i class="fas fa-xmark"></i>
    </button>

    <AuthHeader :title="stepTitle" :subtitle="stepSubtitle" />

    <!-- Step progress tracker -->
    <div class="flex items-center gap-2 mb-6">
      <template v-for="(item, index) in steps" :key="item.id">
        <div class="flex items-center gap-2 flex-1">
          <div
            class="w-7 h-7 shrink-0 rounded-full flex items-center justify-center text-xs font-semibold transition-colors"
            :class="
              stepIndex > index
                ? 'bg-emerald-400 text-white'
                : stepIndex === index
                  ? 'bg-blue-500 text-white ring-4 ring-blue-100'
                  : 'bg-slate-100 text-slate-400'
            "
          >
            <i v-if="stepIndex > index" class="fas fa-check text-[10px]"></i>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <div
            v-if="index < steps.length - 1"
            class="h-0.5 flex-1 rounded transition-colors"
            :class="stepIndex > index ? 'bg-emerald-300' : 'bg-slate-100'"
          ></div>
        </div>
      </template>
    </div>

    <!-- ============================================================ -->
    <!-- STEP 1: ACCOUNT DETAILS (email, phone, password)              -->
    <!-- ============================================================ -->
    <div v-if="step === 'account'" class="space-y-4">
      <form @submit.prevent="submitRegister" class="space-y-4">
        <!-- Bot trap: invisible to people, bots fill every field (see backend registration_risk.py) -->
        <input v-model="form.website" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true"
               class="absolute -left-[9999px] h-0 w-0 opacity-0" />
        <div>
          <label class="text-xs font-medium text-slate-500 block mb-1.5 ml-1">
            {{ t('auth.register.fullName') }} <span class="text-red-500">*</span>
          </label>
          <input v-model="form.full_name" type="text" autocomplete="name" maxlength="120" required
                 :placeholder="t('auth.register.fullNamePlaceholder')" class="auth-input"
                 :class="errors.full_name ? 'auth-input--error' : ''" @blur="validateField('full_name')" />
          <p v-if="errors.full_name" class="text-xs text-rose-500 mt-1 ml-1">{{ errors.full_name }}</p>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="text-xs font-medium text-slate-500 block mb-1.5 ml-1">{{ t('auth.register.region') }}</label>
            <select v-model="form.region" class="auth-input">
              <option value="">—</option>
              <option v-for="r in REGIONS" :key="r" :value="r">{{ t(`region.${r}`) }}</option>
            </select>
          </div>
          <div>
            <label class="text-xs font-medium text-slate-500 block mb-1.5 ml-1">{{ t('auth.register.city') }}</label>
            <input v-model="form.city" type="text" autocomplete="address-level2" maxlength="120" placeholder="Yaoundé" class="auth-input" />
          </div>
        </div>
        <div>
          <label class="text-xs font-medium text-slate-500 block mb-1.5 ml-1">
            {{ t('auth.email') }} <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.email"
            type="email"
            :placeholder="t('auth.emailPlaceholder')"
            class="auth-input"
            :class="
              errors.email ? 'auth-input--error' : ''
            "
            @blur="validateField('email')"
            required
          />
          <p v-if="errors.email" class="text-xs text-rose-500 mt-1 ml-1">
            {{ errors.email }}
          </p>
        </div>

        <div>
          <label class="text-xs font-medium text-slate-500 block mb-1.5 ml-1">
            {{ t('auth.phone') }} <span class="text-slate-400">({{ t('common.optional') }})</span>
          </label>
          <PhoneInput
            v-model="form.phone"
            :error="errors.phone"
            @blur="validateField('phone')"
          />
        </div>

        <div>
          <label class="text-xs font-medium text-slate-500 block mb-1.5 ml-1">
            {{ t('auth.password') }} <span class="text-red-500">*</span>
          </label>
          <div class="relative">
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              :placeholder="t('auth.passwordPlaceholder')"
              class="auth-input pr-11"
              :class="
                errors.password ? 'auth-input--error' : ''
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
          <div class="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 ml-1">
            <p
              v-for="req in passwordRequirements"
              :key="req.id"
              class="text-xs flex items-center gap-1.5 transition-colors"
              :class="req.passed ? 'text-emerald-600' : 'text-slate-400'"
            >
              <i
                :class="req.passed ? 'fas fa-check-circle' : 'far fa-circle'"
              ></i>
              {{ req.label }}
            </p>
          </div>
        </div>

        <div>
          <label class="text-xs font-medium text-slate-500 block mb-1.5 ml-1">
            {{ t('auth.confirmPassword') }} <span class="text-red-500">*</span>
          </label>
          <input
            v-model="form.confirmPassword"
            type="password"
            :placeholder="t('auth.passwordPlaceholder')"
            class="auth-input"
            :class="
              errors.confirmPassword ? 'auth-input--error' : ''
            "
            @blur="validateField('confirmPassword')"
            required
          />
          <p v-if="errors.confirmPassword" class="text-xs text-rose-500 mt-1 ml-1">
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
            {{ t('auth.register.accept') }}
            <button type="button" class="text-blue-600 hover:underline">
              {{ t('auth.register.terms') }}
            </button>
          </label>
        </div>

        <button
          type="submit"
          :disabled="!form.agreeTerms || isSubmitting"
          class="auth-btn"
        >
          <i v-if="isSubmitting" class="fas fa-spinner fa-spin"></i>
          {{ isSubmitting ? t('auth.register.creating') : t('auth.register.submit') }}
        </button>
        <p
          v-if="authStore.error"
          class="text-sm text-rose-600 bg-rose-50 rounded-xl px-3 py-2.5"
        >
          {{ authStore.error }}
        </p>
      </form>

      <div class="relative flex items-center py-1">
        <div class="flex-1 border-t border-slate-100"></div>
        <span class="px-4 text-[11px] tracking-widest text-slate-400">{{ t('common.or') }}</span>
        <div class="flex-1 border-t border-slate-100"></div>
      </div>

      <GoogleLoginButton @success="handleGoogleSignup" />

      <p class="text-center text-sm text-slate-500">
        {{ t('auth.register.haveAccount') }}
        <button
          type="button"
          class="text-blue-600 font-medium hover:underline"
          @click="$emit('switch-to-login')"
        >
          {{ t('auth.register.login') }}
        </button>
      </p>
    </div>

    <!-- ============================================================ -->
    <!-- STEP 2: EMAIL VERIFICATION (6-digit OTP code)                  -->
    <!-- ============================================================ -->
    <div v-else-if="step === 'sent'" class="space-y-5">
      <OtpVerificationForm
        method="email"
        :identifier="form.email"
        @verified="onEmailVerified"
        @back="step = 'account'"
      />
    </div>

    <!-- ============================================================ -->
    <!-- STEP 3: DONE                                                  -->
    <!-- ============================================================ -->
    <div v-else class="text-center space-y-4">
      <div
        class="w-16 h-16 mx-auto rounded-full bg-emerald-50 ring-8 ring-emerald-50/50 flex items-center justify-center text-2xl text-emerald-600"
      >
        <i class="fas fa-circle-check"></i>
      </div>
      <h4 class="text-lg font-bold text-slate-800">{{ t('auth.register.verifiedTitle') }}</h4>
      <p class="text-sm text-slate-500">
        {{ t('auth.register.verifiedText') }}
      </p>
      <button
        type="button"
        class="auth-btn"
        @click="finish"
      >
        {{ t('auth.register.login') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import "./auth.css";
import { ref, reactive, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { isValidEmail, isStrongEnoughPassword } from "@/utils";
import GoogleLoginButton from "./GoogleLoginButton.vue";
import PhoneInput from "./PhoneInput.vue";
import OtpVerificationForm from "./OtpVerificationForm.vue";
import AuthHeader from "./AuthHeader.vue";
import { useI18n } from '@/i18n';

const emit = defineEmits(["close", "switch-to-login"]);

const authStore = useAuthStore();
const router = useRouter();
const { t } = useI18n();

type Step = "account" | "sent" | "done";

const steps: { id: Step }[] = [{ id: "account" }, { id: "sent" }, { id: "done" }];

const step = ref<Step>("account");
const stepIndex = computed(() => steps.findIndex((s) => s.id === step.value));

const stepTitle = computed(() => {
  if (step.value === "account") return t('auth.register.title');
  if (step.value === "sent") return t('auth.register.checkEmail');
  return t('auth.register.welcome');
});

const stepSubtitle = computed(() => {
  if (step.value === "account") return t('auth.register.subtitle');
  if (step.value === "sent") return t('auth.register.enterCode', { email: form.email });
  return t('auth.register.activated');
});

const REGIONS = ["adamaoua", "centre", "est", "extreme-nord", "littoral", "nord", "nord-ouest", "ouest", "sud", "sud-ouest", "diaspora"];
// Bots submit instantly: the backend compares this with the submission time
const formStartedAt = Date.now();

const form = reactive({
  full_name: "",
  region: "",
  city: "",
  website: "",
  email: "",
  phone: "",
  password: "",
  confirmPassword: "",
  agreeTerms: false,
});

const errors = reactive({
  full_name: "",
  email: "",
  phone: "",
  password: "",
  confirmPassword: "",
});

const showPassword = ref(false);
const isSubmitting = ref(false);

const passwordRequirements = computed(() => [
  {
    id: "length",
    label: t('auth.password.length', { n: 12 }),
    passed: form.password.length >= 12,
  },
  {
    id: "uppercase",
    label: t('auth.password.upper'),
    passed: /[A-Z]/.test(form.password),
  },
  {
    id: "lowercase",
    label: t('auth.password.lower'),
    passed: /[a-z]/.test(form.password),
  },
  {
    id: "number",
    label: t('auth.password.number'),
    passed: /[0-9]/.test(form.password),
  },
]);

function validateField(field: keyof typeof errors) {
  if (field === "full_name") {
    errors.full_name = form.full_name.trim().length >= 2 ? "" : t('auth.errors.fullName');
  }
  if (field === "email") {
    errors.email = isValidEmail(form.email) ? "" : t('auth.errors.invalidEmail');
  }
  if (field === "phone") {
    errors.phone =
      !form.phone || form.phone.length >= 8
        ? ""
        : t('auth.errors.invalidPhone');
  }
  if (field === "password") {
    errors.password = isStrongEnoughPassword(form.password)
      ? ""
      : t('auth.errors.weakPassword');
  }
  if (field === "confirmPassword") {
    errors.confirmPassword =
      form.confirmPassword === form.password
        ? ""
        : t('auth.errors.passwordMismatch');
  }
}

function validateForm(): boolean {
  validateField("full_name");
  validateField("email");
  validateField("phone");
  validateField("password");
  validateField("confirmPassword");
  return (
    !errors.full_name &&
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
    full_name: form.full_name.trim(),
    region: form.region || undefined,
    city: form.city.trim() || undefined,
    acceptTerms: form.agreeTerms,
    website: form.website,
    form_started_at: formStartedAt,
  });
  isSubmitting.value = false;
  if (registered && !authStore.error) {
    step.value = "sent";
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

