<script setup lang="ts">
import Navbar from '@/components/Navbar.vue'
import Hero from '@/components/Hero.vue'
import Analyzer from '@/components/Analyzer.vue'
import CommunityAlerts from '@/components/CommunityAlerts.vue'
import Categories from '@/components/Categories.vue'
import ThreatIntel from '@/components/ThreatIntel.vue'
import About from '@/components/About.vue'
import Footer from '@/components/Footer.vue'
import PublicTabBar from '@/components/PublicTabBar.vue'
</script>

<template>
  <Navbar />
  <main class="pb-16 md:pb-0">
    <Hero />
    <Analyzer />
    <CommunityAlerts class="bg-slate-50 dark:bg-slate-950" />
    <Categories />
    <ThreatIntel />
    <About />
  </main>
  <Footer />
  <PublicTabBar />
</template>
