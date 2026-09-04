    <template>
    <div class="space-y-4">
        <div class="text-center">
        <div
            class="w-16 h-16 mx-auto rounded-full bg-purple-50 flex items-center justify-center text-2xl text-purple-600"
        >
            <i class="fas fa-envelope"></i>
        </div>
        <h4 class="text-lg font-bold text-slate-800 mt-3">
            Vérification par Email
        </h4>
        <p class="text-sm text-slate-500">
            Un code de vérification a été envoyé à votre email
        </p>
        </div>

        <form @submit.prevent="sendCode">
        <div>
            <label class="text-xs font-medium text-slate-600 block mb-1">
            Email <span class="text-red-500">*</span>
            </label>
            <input
            v-model="email"
            type="email"
            placeholder="vous@exemple.com"
            class="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-purple-500/30 focus:border-purple-500 outline-none transition"
            :class="error ? 'border-red-400' : ''"
            required
            />
            <p v-if="error" class="text-xs text-red-500 mt-1">{{ error }}</p>
        </div>

        <button
            type="submit"
            :disabled="isSubmitting"
            class="w-full py-3 bg-gradient-to-r from-purple-600 to-blue-500 text-white font-semibold rounded-xl shadow-md shadow-purple-500/25 hover:shadow-purple-500/40 transition disabled:opacity-60"
        >
            <i v-if="isSubmitting" class="fas fa-spinner fa-spin mr-2"></i>
            {{
            isSubmitting
                ? "Envoi en cours..."
                : codeSent
                ? "Vérifier le code"
                : "Envoyer le code"
            }}
        </button>
        </form>

        <div v-if="codeSent">
        <OtpVerificationForm
            method="email"
            :identifier="email"
            @verified="$emit('verified', $event)"
            @back="$emit('back')"
        />
        </div>

        <button
        v-if="!codeSent"
        @click="$emit('back')"
        class="text-sm text-slate-500 hover:text-slate-700 transition"
        >
        <i class="fas fa-arrow-left mr-1"></i> Retour
        </button>
    </div>
    </template>

    <script setup lang="ts">
    import { ref } from "vue";
    import { api } from "@/services/api";
    import OtpVerificationForm from "./OtpVerificationForm.vue";

    const emit = defineEmits(["verified", "back"]);

    const email = ref("");
    const codeSent = ref(false);
    const isSubmitting = ref(false);
    const error = ref("");

    async function sendCode() {
    if (!email.value || !email.value.includes("@")) {
        error.value = "Adresse email invalide.";
        return;
    }

    isSubmitting.value = true;
    error.value = "";

    try {
        await api.post("/verification/send-email-code", { email: email.value });
        codeSent.value = true;
    } catch (err) {
        error.value = "Erreur de connexion";
    } finally {
        isSubmitting.value = false;
    }
    }
    </script>
