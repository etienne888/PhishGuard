<script setup lang="ts">
import { onMounted, ref } from "vue";
import AppLogo from "./AppLogo.vue";
import { useI18n } from "@/i18n";

const { t } = useI18n();

const emit = defineEmits<{ complete: [] }>();

const isLeaving = ref(false);
const isHidden = ref(false);

// Respect users who've asked for less motion: skip the choreography and
// dismiss quickly rather than holding the screen for a fixed animation.
const prefersReducedMotion = window.matchMedia(
  "(prefers-reduced-motion: reduce)",
).matches;
const HOLD_MS = prefersReducedMotion ? 200 : 2000;

onMounted(() => {
  window.setTimeout(() => {
    isLeaving.value = true;
    window.setTimeout(() => {
      isHidden.value = true;
      emit("complete");
    }, 500);
  }, HOLD_MS);
});
</script>

<template>
  <div
    v-if="!isHidden"
    class="fixed inset-0 z-[9999] flex flex-col items-center justify-center bg-white transition-all duration-500"
    :class="isLeaving ? 'opacity-0 pointer-events-none' : 'opacity-100'"
    role="status"
    aria-live="polite"
    :aria-label="t('preloader.loading')"
  >
    <div class="mb-5 animate-[wordFade_0.7s_ease-out_forwards]">
      <AppLogo :size="88" />
    </div>

    <div
      class="flex items-center gap-1.5 text-4xl sm:text-5xl font-extrabold tracking-tight font-display"
    >
      <span
        class="opacity-0 animate-wordFade text-ink"
        style="animation-delay: 0.35s"
        >Phish</span
      >
      <span
        class="opacity-0 animate-wordFade text-signal-green"
        style="animation-delay: 0.55s"
        >Guard</span
      >
      <span
        class="opacity-0 animate-wordFade text-signal-red"
        style="animation-delay: 0.75s"
        >-AI</span
      >
    </div>

    <div
      class="mt-5 flex items-center gap-3 text-xs font-semibold tracking-widest text-slate-600 opacity-0 animate-fadeUp"
      style="animation-delay: 1.1s"
    >
      <span class="flex items-center gap-1.5"
        >{{ t('preloader.detect') }} <span class="h-1.5 w-1.5 rounded-full bg-signal-green"></span
      ></span>
      <span class="flex items-center gap-1.5"
        >{{ t('preloader.protect') }} <span class="h-1.5 w-1.5 rounded-full bg-signal-red"></span
      ></span>
      <span>{{ t('preloader.educate') }}</span>
    </div>

    <div
      class="mt-3 flex items-center gap-2.5 text-sm text-ink/70 opacity-0 animate-fadeUp"
      style="animation-delay: 1.4s"
    >
      <span class="h-px w-9 bg-signal-green"></span>
      <span>{{ t('preloader.tagline') }}</span>
      <span class="h-px w-9 bg-signal-yellow"></span>
    </div>
  </div>
</template>
