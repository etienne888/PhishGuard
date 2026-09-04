<script setup lang="ts">
import Navbar from '@/components/Navbar.vue'
</script>

<template>
  <Navbar />
  <main class="pt-28 pb-16 px-4 min-h-screen bg-slate-50">
    <div class="max-w-6xl mx-auto">
      <h1 class="text-3xl font-bold text-slate-800 font-display">Administration</h1>
      <p class="text-slate-500 mt-1">Gestion des catégories de menaces et de la veille — réservé à l'équipe CIRT.</p>
      <div class="mt-10 bg-white rounded-xl border border-slate-100 shadow-card p-8 text-center text-slate-500 text-sm">
        Panneau d'administration à connecter à l'API backend (routes /admin).
      </div>
    </div>
  </main>
</template>
