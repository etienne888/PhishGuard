<template>
  <div
    class="auth-card bg-white rounded-3xl max-w-md w-full relative overflow-hidden px-6 py-7 sm:px-9 sm:py-8"
  >
    <!-- Close -->
    <button
      class="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition w-9 h-9 rounded-full hover:bg-slate-100 flex items-center justify-center"
      :aria-label="t('auth.close')"
      @click="$emit('close')"
    >
      <i class="fas fa-xmark"></i>
    </button>

    <!-- Header -->
    <AuthHeader :title="t('auth.login.title')" :subtitle="t('auth.login.subtitle')" />

    <!-- Tabs -->
    <div class="flex gap-1 bg-slate-100/70 rounded-full p-1 mb-6">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="flex-1 py-2 text-xs sm:text-sm font-medium rounded-full transition-all duration-200"
        :class="
          activeTab === tab.id
            ? 'bg-white shadow-sm text-blue-600'
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
      <form class="space-y-4" @submit.prevent="handleEmailLogin">
        <div>
          <label class="text-xs font-medium text-slate-500 block mb-1.5 ml-1">
            {{ t('auth.email') }} <span class="text-red-500">*</span>
          </label>
          <input
            v-model="emailForm.email"
            type="email"
            :placeholder="t('auth.emailPlaceholder')"
            class="auth-input"
            :class="
              emailErrors.email ? 'auth-input--error' : ''
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
          <div class="flex items-center justify-between mb-1.5">
            <label class="text-xs font-medium text-slate-500 block ml-1">
              {{ t('auth.password') }} <span class="text-red-500">*</span>
            </label>
            <button
              type="button"
              class="text-xs text-blue-600 hover:underline font-medium"
            >
              {{ t('auth.login.forgot') }}
            </button>
          </div>
          <div class="relative">
            <input
              v-model="emailForm.password"
              :type="showPassword ? 'text' : 'password'"
              :placeholder="t('auth.passwordPlaceholder')"
              class="auth-input pr-11"
              :class="
                emailErrors.password ? 'auth-input--error' : ''
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
            {{ t('auth.login.remember') }}
          </label>
        </div>

        <p
          v-if="authError"
          class="text-sm text-rose-600 bg-rose-50 px-3 py-2.5 rounded-xl flex items-center gap-2"
        >
          <i class="fas fa-triangle-exclamation"></i>
          {{ authError }}
        </p>

        <button
          type="submit"
          :disabled="isSubmitting"
          class="auth-btn"
        >
          <i v-if="isSubmitting" class="fas fa-spinner fa-spin"></i>
          {{ isSubmitting ? t('auth.login.submitting') : t('auth.login.submit') }}
        </button>
      </form>

      <div class="relative flex items-center py-2">
        <div class="flex-1 border-t border-slate-100"></div>
        <span class="px-4 text-[11px] tracking-widest text-slate-400">{{ t('common.or') }}</span>
        <div class="flex-1 border-t border-slate-100"></div>
      </div>

      <!-- Social Login Buttons -->
      <GoogleLoginButton @success="handleGoogleLogin" />

      <div
        v-if="authStore.mfaRequired"
        class="mt-4 rounded-2xl bg-blue-50/70 p-4"
      >
        <label class="text-xs font-medium text-slate-700 block mb-2"
          >{{ t('auth.login.mfaLabel') }}</label
        >
        <input
          v-model="mfaCode"
          inputmode="numeric"
          maxlength="6"
          class="auth-input bg-white text-center tracking-[0.4em]"
          placeholder="123456"
        />
        <button
          type="button"
          class="auth-btn mt-3"
          :disabled="isSubmitting || mfaCode.length !== 6"
          @click="verifyMfa"
        >
          {{ t('auth.verify.submit') }}
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
    <div class="mt-6 pt-5 border-t border-slate-100">
      <p class="text-center text-sm text-slate-500">
        {{ t('auth.login.noAccount') }}
        <button
          @click="$emit('switch-to-register')"
          class="text-blue-600 font-medium hover:underline"
        >
          {{ t('auth.login.register') }}
        </button>
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import "./auth.css";
import { ref, reactive, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { isValidEmail } from "@/utils";
import GoogleLoginButton from "./GoogleLoginButton.vue";
import OtpVerificationForm from "./OtpVerificationForm.vue";
import EmailCodeForm from "./EmailCodeForm.vue";
import AuthHeader from "./AuthHeader.vue";
import { useI18n } from '@/i18n';
import type { AuthUser } from '@/types';

const emit = defineEmits(["close", "switch-to-register", "switch-to-demo"]);

const authStore = useAuthStore();
const router = useRouter();
const { t } = useI18n();

// Tabs
const tabs = computed(() => [
  { id: "email", label: t('auth.email'), icon: "fas fa-envelope" },
  { id: "phone", label: t('auth.phone'), icon: "fas fa-phone" },
  { id: "emailCode", label: t('auth.login.emailCodeTab'), icon: "fas fa-key" },
]);
const activeTab = ref("email");

// Email form
const emailForm = reactive({ email: "", password: "" });
const emailErrors = reactive({ email: "", password: "" });
const showPassword = ref(false);
const rememberMe = ref(false);
const mfaCode = ref("");

const isSubmitting = ref(false);
const authError = ref("");

function dashboardTarget(user: AuthUser) {
  return user.is_admin === true ? { name: 'admin-overview' } : { name: 'dashboard' };
}

async function redirectAfterLogin(user: AuthUser) {
  emit('close');
  await router.replace(dashboardTarget(user));
}

function isWrappedLoginResponse(value: AuthUser | { user?: AuthUser }): value is { user?: AuthUser } {
  return 'user' in value;
}

function validateEmailField(field: keyof typeof emailErrors) {
  if (field === "email") {
    emailErrors.email = isValidEmail(emailForm.email)
      ? ""
      : t('auth.errors.invalidEmail');
  }
  if (field === "password") {
    emailErrors.password =
      emailForm.password.length >= 8 ? "" : t('auth.errors.passwordMin', { n: 8 });
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
      await redirectAfterLogin(authStore.user);
    }
  } catch (err: any) {
    authError.value = err.message || t('auth.errors.loginFailed');
  } finally {
    isSubmitting.value = false;
  }
}

async function verifyMfa() {
  isSubmitting.value = true;
  await authStore.verifyMfa(mfaCode.value);
  if (!authStore.error && authStore.user) {
    await redirectAfterLogin(authStore.user);
  }
  isSubmitting.value = false;
}

function handleGoogleLogin(response: { user?: AuthUser } | AuthUser) {
  let user: AuthUser;
  if (isWrappedLoginResponse(response)) {
    if (!response.user) return;
    user = response.user;
  } else {
    user = response;
  }
  authStore.user = user;
  void redirectAfterLogin(user);
}

function handleOTPVerified(user: AuthUser) {
  authStore.user = user;
  void redirectAfterLogin(user);
}

function handleEmailCodeVerified(user: AuthUser) {
  authStore.user = user;
  void redirectAfterLogin(user);
}
</script>

