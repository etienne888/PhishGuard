<script setup lang="ts">
import AppLogo from '@/components/AppLogo.vue'

defineProps<{ title: string; subtitle?: string }>()
</script>

<template>
  <div class="text-center mb-6">
    <div class="auth-logo mx-auto mb-3">
      <AppLogo :size="52" />
    </div>
    <p class="text-sm font-extrabold tracking-tight text-slate-700">
      Phish<span class="text-blue-600">Guard</span><span class="text-cyan-500">-AI</span>
    </p>
    <h3 class="mt-3 text-2xl font-bold text-slate-800 font-display">{{ title }}</h3>
    <p v-if="subtitle" class="mt-1 text-sm text-slate-500">{{ subtitle }}</p>
  </div>
</template>

<style scoped>
.auth-logo {
  width: 76px;
  height: 76px;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle, #eff6ff 0%, #ecfeff 60%, rgba(236, 254, 255, 0) 100%);
  box-shadow: 0 0 0 6px rgba(219, 234, 254, 0.45);
}
</style>
