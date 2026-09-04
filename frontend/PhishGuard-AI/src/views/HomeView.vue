<script setup lang="ts">
import Navbar from '@/components/Navbar.vue'
import Hero from '@/components/Hero.vue'
import Analyzer from '@/components/Analyzer.vue'
import Categories from '@/components/Categories.vue'
import ThreatIntel from '@/components/ThreatIntel.vue'
import About from '@/components/About.vue'
import Footer from '@/components/Footer.vue'
</script>

<template>
  <Navbar />
  <main>
    <Hero />
    <Analyzer />
    <Categories />
    <ThreatIntel />
    <About />
  </main>
  <Footer />
</template>
