<script setup lang="ts">
/**
 * Line icons (24×24, stroke = currentColor) used across the user experience.
 * Decorative by default; pass `label` when the icon carries meaning on its own.
 */
import { computed } from 'vue'
import { ICON_PATHS, type IconName } from './icons'

const props = withDefaults(defineProps<{ name: IconName; size?: number | string; stroke?: number; label?: string }>(), {
  size: 20,
  stroke: 1.9,
})

const d = computed(() => ICON_PATHS[props.name])
</script>

<template>
  <svg :width="size" :height="size" viewBox="0 0 24 24" fill="none" stroke="currentColor" :stroke-width="stroke"
       stroke-linecap="round" stroke-linejoin="round" :role="label ? 'img' : undefined"
       :aria-hidden="label ? undefined : 'true'" :aria-label="label" class="shrink-0">
    <path :d="d" />
  </svg>
</template>
