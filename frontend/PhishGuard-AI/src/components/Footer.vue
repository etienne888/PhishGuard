<script setup lang="ts">
const year = new Date().getFullYear()
const links = ['Confidentialité', 'Conditions', 'Contact', 'CIRT-CM']
</script>

<template>
  <footer class="bg-slate-900 text-slate-300 px-4 py-12">
    <div class="max-w-7xl mx-auto">
      <div class="flex flex-col md:flex-row justify-between items-center gap-4">
        <div class="flex items-center gap-2">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-cyan-400"></div>
          <span class="text-lg font-bold text-white font-display">Phish<span class="text-blue-400">Guard</span><span class="text-cyan-400">-AI</span></span>
        </div>
        <div class="flex flex-wrap gap-6 text-sm">
          <a v-for="link in links" :key="link" href="#" class="hover:text-white transition">{{ link }}</a>
        </div>
        <span class="text-xs text-slate-500">© {{ year }} PhishGuard-AI · Cameroun</span>
      </div>
    </div>
  </footer>
</template>
