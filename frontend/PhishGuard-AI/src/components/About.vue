<script setup lang="ts">
const stats = [
  { value: '1.02 Md', label: 'FCFA perdus aux arnaques (2025)', color: 'text-blue-600' },
  { value: '99%', label: 'précision de détection', color: 'text-cyan-600' },
  { value: '12', label: 'catégories de menaces', color: 'text-emerald-600' },
  { value: '24/7', label: 'protection gratuite', color: 'text-purple-600' }
]
</script>

<template>
  <section id="about" class="py-20 px-4 bg-white">
    <div class="max-w-6xl mx-auto">
      <div class="grid md:grid-cols-2 gap-12 items-center">
        <div>
          <h2 class="text-3xl sm:text-4xl font-bold text-slate-800 font-display">Conçu au Cameroun, par des talents camerounais</h2>
          <p class="text-slate-600 mt-4 leading-relaxed">
            PhishGuard-AI est un projet de fin d'études en cybersécurité, pensé pour protéger les citoyens contre le
            phishing, la fraude Mobile Money et l'ingénierie sociale.
          </p>
          <div class="mt-6 grid grid-cols-2 gap-4">
            <div v-for="stat in stats" :key="stat.label" class="bg-slate-50 rounded-xl p-4 border border-slate-100">
              <span class="text-2xl font-bold font-display" :class="stat.color">{{ stat.value }}</span>
              <p class="text-xs text-slate-500 mt-0.5">{{ stat.label }}</p>
            </div>
          </div>
        </div>
        <div class="bg-gradient-to-br from-blue-50 via-cyan-50 to-white rounded-2xl p-8 border border-slate-100 shadow-lg">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center text-white text-lg font-bold shadow-lg shadow-blue-500/25">
              GC
            </div>
            <div>
              <span class="text-sm font-bold text-slate-800 block">Licence Cybersécurité</span>
              <span class="text-xs text-slate-500">Projet de fin d'études — 2026</span>
            </div>
          </div>
          <p class="text-sm text-slate-600 leading-relaxed">
            « PhishGuard-AI se veut accessible, localisé et efficace. Il ne détecte pas seulement les arnaques — il
            apprend aux citoyens à les reconnaître et à les signaler. »
          </p>
        </div>
      </div>
    </div>
  </section>
</template>
