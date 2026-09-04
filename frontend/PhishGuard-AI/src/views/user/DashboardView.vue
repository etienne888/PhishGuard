<script setup lang="ts">
import Navbar from "@/components/Navbar.vue";
import DashboardStats from "@/components/DashboardStats.vue";

const stats = [
  { label: "Messages analysés", value: "0", tone: "text-blue-600" },
  { label: "Menaces détectées", value: "0", tone: "text-red-600" },
  { label: "Signalements envoyés", value: "0", tone: "text-emerald-600" },
  { label: "Score de vigilance", value: "—", tone: "text-purple-600" },
];
</script>

<template>
  <Navbar />
  <main class="pt-28 pb-16 px-4 min-h-screen bg-slate-50">
    <div class="max-w-6xl mx-auto">
      <h1 class="text-3xl font-bold text-slate-800 font-display">
        Votre tableau de bord
      </h1>
      <p class="text-slate-500 mt-1">
        Suivez votre activité de protection contre le phishing.
      </p>
      <RouterLink
        to="/dashboard/security"
        class="inline-flex mt-4 px-4 py-2 rounded-lg border border-slate-200 bg-white text-sm font-semibold text-slate-700 hover:border-blue-300 hover:text-blue-600 transition"
      >
        Sécurité du compte
      </RouterLink>
      <div class="mt-8">
        <DashboardStats :stats="stats" />
      </div>
      <div
        class="mt-10 bg-white rounded-xl border border-slate-100 shadow-card p-8 text-center text-slate-500 text-sm"
      >
        Aucune analyse pour le moment. Rendez-vous sur la page d'accueil pour
        tester un message.
      </div>
    </div>
  </main>
</template>
