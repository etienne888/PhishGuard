<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 40 })

// Unique per instance so multiple logos on the same page (navbar, preloader,
// auth modal) don't collide on a shared SVG gradient id.
const gradientId = `logoGradient-${Math.random().toString(36).slice(2, 9)}`
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PhishGuard-AI">
    <defs>
      <linearGradient :id="gradientId" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#1e3a8a" />
        <stop offset="100%" stop-color="#06b6d4" />
      </linearGradient>
    </defs>
    <path
      d="M32 4 L56 14 V30 C56 46 46 56 32 60 C18 56 8 46 8 30 V14 Z"
      :fill="`url(#${gradientId})`"
    />
    <path
      d="M22 32 L29 39 L43 24"
      stroke="white"
      stroke-width="4.5"
      fill="none"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
</template>
