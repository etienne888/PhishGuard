<script setup lang="ts">
import { computed } from 'vue'

/** Tiny area chart for a series of numbers (oldest first). */
const props = withDefaults(defineProps<{ values: number[]; color?: string; height?: number; label?: string }>(),
  { color: '#06b6d4', height: 40, label: '' })

const W = 200
const path = computed(() => {
  const values = props.values.length ? props.values : [0]
  const max = Math.max(1, ...values)
  const step = values.length > 1 ? W / (values.length - 1) : W
  const points = values.map((v, i) => [i * step, props.height - (v / max) * (props.height - 4) - 2] as const)
  const line = points.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`).join(' ')
  return { line, area: `${line} L${W},${props.height} L0,${props.height} Z` }
})
const gradientId = `spark-${Math.random().toString(36).slice(2, 8)}`
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${height}`" preserveAspectRatio="none" class="block w-full" :style="{ height: `${height}px` }"
       role="img" :aria-label="label">
    <defs>
      <linearGradient :id="gradientId" x1="0" x2="0" y1="0" y2="1">
        <stop offset="0%" :stop-color="color" stop-opacity="0.35" />
        <stop offset="100%" :stop-color="color" stop-opacity="0" />
      </linearGradient>
    </defs>
    <path :d="path.area" :fill="`url(#${gradientId})`" />
    <path :d="path.line" fill="none" :stroke="color" stroke-width="1.8" vector-effect="non-scaling-stroke" stroke-linejoin="round" />
  </svg>
</template>
