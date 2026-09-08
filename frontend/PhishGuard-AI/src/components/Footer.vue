<script setup lang="ts">
import AppLogo from './AppLogo.vue'

const year = new Date().getFullYear()

const quickLinks = [
  { label: 'Accueil', href: '/' },
  { label: 'Analyser', href: '#analyze' },
  { label: 'Éducation', href: '#education' },
  { label: 'Tableau de bord', href: '/dashboard' }
]

const legalLinks = [
  { label: 'Confidentialité', href: '/privacy' },
  { label: 'Conditions', href: '/terms' },
  { label: 'Mentions légales', href: '/legal' },
  { label: 'Cookies', href: '/cookies' }
]

const securityLinks = [
  { label: 'CIRT-CM', href: 'https://cirt.cm', external: true },
  { label: 'ANTIC', href: 'https://antic.cm', external: true },
  { label: 'Interpol', href: 'https://interpol.int', external: true },
  { label: 'Signalement', href: '#report' }
]

const socialLinks = [
  { icon: 'fab fa-twitter', href: '#', label: 'Twitter' },
  { icon: 'fab fa-linkedin-in', href: '#', label: 'LinkedIn' },
  { icon: 'fab fa-github', href: '#', label: 'GitHub' },
  { icon: 'fab fa-youtube', href: '#', label: 'YouTube' }
]
</script>

<template>
  <footer class="bg-slate-900 text-slate-300">
    <!-- Main Footer -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="grid md:grid-cols-4 gap-8">
        
        <!-- Column 1: Brand -->
        <div class="space-y-4">
          <div class="flex items-center gap-2">
            <!-- Logo -->
            <AppLogo :size="36" />
            <span class="text-xl font-bold font-display text-white">
              Phish<span class="text-blue-400">Guard</span><span class="text-cyan-400">-AI</span>
            </span>
          </div>
          <p class="text-sm text-slate-400 leading-relaxed max-w-xs">
            Protégez-vous contre le phishing, la fraude Mobile Money et les cyberarnaques au Cameroun.
          </p>
          <!-- Security Badge -->
          <div class="flex items-center gap-2">
            <span class="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-400 bg-emerald-400/10 px-3 py-1.5 rounded-full border border-emerald-400/20">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Sécurisé
            </span>
            <span class="inline-flex items-center gap-1.5 text-xs font-medium text-blue-400 bg-blue-400/10 px-3 py-1.5 rounded-full border border-blue-400/20">
              <i class="fas fa-shield-halved text-[10px]"></i>
              IA puissante
            </span>
          </div>
        </div>

        <!-- Column 2: Quick Links -->
        <div>
          <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
            Navigation
          </h4>
          <ul class="space-y-2.5">
            <li v-for="link in quickLinks" :key="link.label">
              <a 
                :href="link.href" 
                class="text-sm text-slate-400 hover:text-white transition hover:translate-x-1 inline-flex items-center gap-1.5"
              >
                <i class="fas fa-chevron-right text-[8px] text-slate-600"></i>
                {{ link.label }}
              </a>
            </li>
          </ul>
        </div>

        <!-- Column 3: Legal & Security -->
        <div>
          <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
            Légal & Sécurité
          </h4>
          <ul class="space-y-2.5">
            <li v-for="link in legalLinks" :key="link.label">
              <a 
                :href="link.href" 
                class="text-sm text-slate-400 hover:text-white transition hover:translate-x-1 inline-flex items-center gap-1.5"
              >
                <i class="fas fa-chevron-right text-[8px] text-slate-600"></i>
                {{ link.label }}
              </a>
            </li>
          </ul>
          <div class="mt-4 pt-4 border-t border-slate-800/50">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
              Signalement
            </h4>
            <div class="space-y-1 text-sm">
              <p class="text-slate-400 flex items-center gap-2">
                <i class="fas fa-phone text-emerald-400 text-xs"></i>
                <span class="font-mono">8202</span>
              </p>
              <p class="text-slate-400 flex items-center gap-2">
                <i class="fas fa-envelope text-emerald-400 text-xs"></i>
                <a href="mailto:alerts@cirt.cm" class="hover:text-white transition">alerts@cirt.cm</a>
              </p>
            </div>
          </div>
        </div>

        <!-- Column 4: Resources & Social -->
        <div>
          <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-4">
            Ressources
          </h4>
          <ul class="space-y-2.5">
            <li v-for="link in securityLinks" :key="link.label">
              <a 
                :href="link.href" 
                target="_blank"
                rel="noopener noreferrer"
                class="text-sm text-slate-400 hover:text-white transition hover:translate-x-1 inline-flex items-center gap-1.5"
              >
                <i class="fas fa-external-link-alt text-[8px] text-slate-600"></i>
                {{ link.label }}
              </a>
            </li>
          </ul>
          
          <!-- Social Links -->
          <div class="mt-4 pt-4 border-t border-slate-800/50">
            <h4 class="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">
              Suivez-nous
            </h4>
            <div class="flex gap-3">
              <a 
                v-for="social in socialLinks" 
                :key="social.label"
                :href="social.href"
                target="_blank"
                rel="noopener noreferrer"
                class="w-8 h-8 rounded-lg bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-400 hover:text-white transition group"
                :aria-label="social.label"
              >
                <i :class="[social.icon, 'text-sm group-hover:scale-110 transition']"></i>
              </a>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Bar -->
      <div class="mt-8 pt-6 border-t border-slate-800/50 flex flex-col sm:flex-row justify-between items-center gap-3">
        <div class="flex items-center gap-4 text-xs text-slate-500">
          <span>© {{ year }} PhishGuard-AI · Cameroun</span>
          <span class="hidden sm:inline">|</span>
          <span class="flex items-center gap-1.5">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            <span>Protection active</span>
          </span>
        </div>
        <div class="flex items-center gap-4 text-xs text-slate-500">
          <span>Version 1.0.0</span>
          <span>|</span>
          <span class="flex items-center gap-1">
            <i class="fas fa-shield-check text-emerald-500 text-[10px]"></i>
            Sécurisé par <span class="text-slate-400 font-medium">PhishGuard-AI</span>
          </span>
        </div>
      </div>
    </div>
  </footer>
</template>

<style scoped>
/* Smooth hover transitions */
a {
  transition: all 0.2s ease;
}

/* Subtle animation for the security badge */
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.animate-pulse {
  animation: pulse-dot 2s ease-in-out infinite;
}
</style>