<template>
  <div class="relative">
    <div
      class="flex w-full border rounded-lg text-sm transition overflow-hidden"
      :class="
        error
          ? 'border-red-400'
          : 'border-slate-200 focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-500'
      "
    >
      <button
        type="button"
        class="flex items-center gap-1.5 px-2.5 py-2.5 border-r border-slate-200 bg-slate-50 hover:bg-slate-100 transition shrink-0"
        @click="isOpen = !isOpen"
      >
        <span class="text-base leading-none">{{ selected.flag }}</span>
        <span class="text-xs font-medium text-slate-600">{{ selected.dialCode }}</span>
        <i class="fas fa-chevron-down text-[10px] text-slate-400"></i>
      </button>
      <input
        v-model="nationalNumber"
        type="tel"
        inputmode="numeric"
        placeholder="6XX XXX XXX"
        class="flex-1 min-w-0 px-3 py-2.5 outline-none"
        @input="emitValue"
        @blur="$emit('blur')"
      />
    </div>
    <p v-if="error" class="text-xs text-red-500 mt-1">{{ error }}</p>

    <!-- Country dropdown -->
    <Transition name="fade">
      <div
        v-if="isOpen"
        class="absolute z-20 mt-1 w-64 max-h-56 overflow-y-auto bg-white border border-slate-200 rounded-xl shadow-lg py-1"
      >
        <button
          v-for="country in countries"
          :key="country.iso2"
          type="button"
          class="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-slate-50 transition text-left"
          @click="selectCountry(country)"
        >
          <span class="text-base leading-none">{{ country.flag }}</span>
          <span class="flex-1 text-slate-700">{{ country.name }}</span>
          <span class="text-xs text-slate-400">{{ country.dialCode }}</span>
        </button>
      </div>
    </Transition>
    <div v-if="isOpen" class="fixed inset-0 z-10" @click="isOpen = false"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";

const props = defineProps<{
  modelValue: string;
  error?: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string): void;
  (e: "blur"): void;
}>();

interface Country {
  name: string;
  iso2: string;
  dialCode: string;
  flag: string;
}

const countries: Country[] = [
  { name: "Cameroun", iso2: "CM", dialCode: "+237", flag: "🇨🇲" },
  { name: "Nigeria", iso2: "NG", dialCode: "+234", flag: "🇳🇬" },
  { name: "Ghana", iso2: "GH", dialCode: "+233", flag: "🇬🇭" },
  { name: "Côte d'Ivoire", iso2: "CI", dialCode: "+225", flag: "🇨🇮" },
  { name: "Sénégal", iso2: "SN", dialCode: "+221", flag: "🇸🇳" },
  { name: "Togo", iso2: "TG", dialCode: "+228", flag: "🇹🇬" },
  { name: "Bénin", iso2: "BJ", dialCode: "+229", flag: "🇧🇯" },
  { name: "Gabon", iso2: "GA", dialCode: "+241", flag: "🇬🇦" },
  { name: "Congo (RDC)", iso2: "CD", dialCode: "+243", flag: "🇨🇩" },
  { name: "Congo", iso2: "CG", dialCode: "+242", flag: "🇨🇬" },
  { name: "Mali", iso2: "ML", dialCode: "+223", flag: "🇲🇱" },
  { name: "Burkina Faso", iso2: "BF", dialCode: "+226", flag: "🇧🇫" },
  { name: "Tchad", iso2: "TD", dialCode: "+235", flag: "🇹🇩" },
  { name: "Kenya", iso2: "KE", dialCode: "+254", flag: "🇰🇪" },
  { name: "Afrique du Sud", iso2: "ZA", dialCode: "+27", flag: "🇿🇦" },
  { name: "Maroc", iso2: "MA", dialCode: "+212", flag: "🇲🇦" },
  { name: "Algérie", iso2: "DZ", dialCode: "+213", flag: "🇩🇿" },
  { name: "Tunisie", iso2: "TN", dialCode: "+216", flag: "🇹🇳" },
  { name: "Égypte", iso2: "EG", dialCode: "+20", flag: "🇪🇬" },
  { name: "France", iso2: "FR", dialCode: "+33", flag: "🇫🇷" },
  { name: "Belgique", iso2: "BE", dialCode: "+32", flag: "🇧🇪" },
  { name: "Suisse", iso2: "CH", dialCode: "+41", flag: "🇨🇭" },
  { name: "Canada", iso2: "CA", dialCode: "+1", flag: "🇨🇦" },
  { name: "États-Unis", iso2: "US", dialCode: "+1", flag: "🇺🇸" },
  { name: "Royaume-Uni", iso2: "GB", dialCode: "+44", flag: "🇬🇧" },
];

const defaultCountry: Country = { name: "Cameroun", iso2: "CM", dialCode: "+237", flag: "🇨🇲" };
const isOpen = ref(false);
const selected = ref(defaultCountry);
const nationalNumber = ref("");

function parseModelValue() {
  const value = props.modelValue || "";
  const match = countries
    .slice()
    .sort((a, b) => b.dialCode.length - a.dialCode.length)
    .find((c) => value.startsWith(c.dialCode));
  if (match) {
    selected.value = match;
    nationalNumber.value = value.slice(match.dialCode.length).trim();
  } else {
    nationalNumber.value = value;
  }
}

parseModelValue();

watch(
  () => props.modelValue,
  (value) => {
    const composed = `${selected.value.dialCode}${nationalNumber.value.replace(/\s+/g, "")}`;
    if (value !== composed) parseModelValue();
  },
);

function selectCountry(country: Country) {
  selected.value = country;
  isOpen.value = false;
  emitValue();
}

function emitValue() {
  const digits = nationalNumber.value.replace(/[^\d]/g, "");
  emit("update:modelValue", digits ? `${selected.value.dialCode}${digits}` : "");
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
