<script setup lang="ts">
// Imported (not referenced by path) so Vite fingerprints it and it works in production builds
import logoMark from '@/assets/Images/logo-mark.png'

withDefaults(defineProps<{ size?: number }>(), { size: 40 })
</script>

<template>
  <img :src="logoMark" :width="size" :height="size" class="object-contain" alt="PhishGuard-AI" />
</template>
