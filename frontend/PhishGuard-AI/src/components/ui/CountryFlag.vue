<script setup lang="ts">
/** Country flag as a small image (emoji flags don't render on Windows). Falls back to a globe. */
import { ref } from 'vue'
import AppIcon from './AppIcon.vue'

const props = withDefaults(defineProps<{ code?: string | null; size?: number }>(), { code: null, size: 16 })
const failed = ref(false)
</script>

<template>
  <img v-if="props.code && props.code.length === 2 && !failed" :src="`https://flagcdn.com/w40/${props.code.toLowerCase()}.png`"
       :alt="props.code" :width="props.size" :height="Math.round(props.size * 0.75)" loading="lazy"
       class="inline-block shrink-0 rounded-[3px] object-cover align-[-2px] shadow-[0_0_0_1px_rgba(255,255,255,0.15)]" @error="failed = true" />
  <AppIcon v-else name="globe" :size="props.size" class="inline-block shrink-0 text-slate-400" />
</template>
