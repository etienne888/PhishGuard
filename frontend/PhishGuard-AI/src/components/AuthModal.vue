    <script setup lang="ts">
    import { reactive, watch } from "vue";
    import AppLogo from "./AppLogo.vue";
    import { useAuth } from "@/composables";
    import { isValidEmail, isStrongEnoughPassword } from "@/utils";

    const {
    modalMode,
    isSubmitting,
    error,
    closeModal,
    openModal,
    login,
    register,
    } = useAuth();

    const form = reactive({ email: "", password: "", confirmPassword: "" });
    const formError = reactive({ email: "", password: "" });

    watch(modalMode, () => {
    form.email = "";
    form.password = "";
    form.confirmPassword = "";
    formError.email = "";
    formError.password = "";
    });

    function validate(): boolean {
    formError.email = isValidEmail(form.email) ? "" : "Adresse email invalide.";
    formError.password = isStrongEnoughPassword(form.password)
        ? ""
        : "Minimum 8 caractères.";
    return !formError.email && !formError.password;
    }

    function submitLogin() {
    if (!validate()) return;
    login({ email: form.email, password: form.password });
    }

    function submitRegister() {
    if (!validate()) return;
    register({
        email: form.email,
        password: form.password,
        confirmPassword: form.confirmPassword,
    });
    }

    function onBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) closeModal();
    }
    </script>

    <template>
    <Transition name="modal">
        <div
        v-if="modalMode"
        class="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4"
        @click="onBackdropClick"
        >
        <div
            class="bg-white rounded-2xl max-w-md w-full shadow-2xl relative overflow-hidden p-6 sm:p-8"
        >
            <template v-if="modalMode === 'login' || modalMode === 'register'">
            <AppLogo :size="56" class="mx-auto mb-4" />
            <div class="flex justify-between items-start">
                <div>
                <h3 class="text-2xl font-bold text-slate-800 font-display">
                    {{
                    modalMode === "login"
                        ? "Content de vous revoir"
                        : "Créer un compte"
                    }}
                </h3>
                <p class="text-sm text-slate-500">
                    {{
                    modalMode === "login"
                        ? "Connectez-vous à votre compte PhishGuard-AI"
                        : "Rejoignez PhishGuard-AI et restez protégé"
                    }}
                </p>
                </div>
                <button
                class="text-slate-400 hover:text-slate-600 transition"
                aria-label="Fermer"
                @click="closeModal"
                >
                <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                >
                    <path d="M6 6l12 12M18 6L6 18" stroke-linecap="round" />
                </svg>
                </button>
            </div>

            <form
                class="mt-6 space-y-4"
                @submit.prevent="
                modalMode === 'login' ? submitLogin() : submitRegister()
                "
            >
                <div>
                <label class="text-xs font-medium text-slate-600 block mb-1"
                    >Email</label
                >
                <input
                    v-model="form.email"
                    type="email"
                    placeholder="vous@exemple.com"
                    class="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition"
                />
                <p v-if="formError.email" class="text-xs text-red-500 mt-1">
                    {{ formError.email }}
                </p>
                </div>
                <div>
                <label class="text-xs font-medium text-slate-600 block mb-1"
                    >Mot de passe</label
                >
                <input
                    v-model="form.password"
                    type="password"
                    placeholder="••••••••"
                    class="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition"
                />
                <p v-if="formError.password" class="text-xs text-red-500 mt-1">
                    {{ formError.password }}
                </p>
                </div>
                <div v-if="modalMode === 'register'">
                <label class="text-xs font-medium text-slate-600 block mb-1"
                    >Confirmer le mot de passe</label
                >
                <input
                    v-model="form.confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    class="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 transition"
                />
                </div>

                <p v-if="error" class="text-sm text-red-500">{{ error }}</p>

                <button
                type="submit"
                :disabled="isSubmitting"
                class="w-full py-3 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition disabled:opacity-60"
                >
                {{
                    isSubmitting
                    ? "Un instant…"
                    : modalMode === "login"
                        ? "Se connecter"
                        : "Créer le compte"
                }}
                </button>
            </form>

            <p class="mt-4 text-center text-sm text-slate-500">
                <template v-if="modalMode === 'login'">
                Pas encore de compte ?
                <button
                    class="text-blue-600 font-medium hover:underline"
                    @click="openModal('register')"
                >
                    S'inscrire
                </button>
                </template>
                <template v-else>
                Déjà un compte ?
                <button
                    class="text-blue-600 font-medium hover:underline"
                    @click="openModal('login')"
                >
                    Se connecter
                </button>
                </template>
            </p>
            </template>

            <template v-else-if="modalMode === 'demo'">
            <div class="text-center">
                <div
                class="w-20 h-20 mx-auto rounded-full bg-blue-50 flex items-center justify-center text-blue-600 text-3xl font-bold"
                >
                ▶
                </div>
                <h3 class="text-2xl font-bold text-slate-800 mt-4 font-display">
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
            </template>
        </div>
        </div>
    </Transition>
    </template>

    <style scoped>
    .modal-enter-active,
    .modal-leave-active {
    transition: opacity 0.2s ease;
    }
    .modal-enter-from,
    .modal-leave-to {
    opacity: 0;
    }
    </style>
