<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { threatsService } from '@/services'
import { formatDate } from '@/utils'
import type { ThreatIntelItem } from '@/types'

const items = ref<ThreatIntelItem[]>([])
const isLoading = ref(false)
const lastUpdated = ref<string | null>(null)

async function refresh() {
  isLoading.value = true
  try {
    items.value = await threatsService.getThreatIntel()
    lastUpdated.value = new Date().toISOString()
  } finally {
    isLoading.value = false
  }
}

onMounted(refresh)
</script>

<template>
  <section id="threat-intel" class="py-20 px-4 hero-gradient">
    <div class="max-w-7xl mx-auto">
      <div class="text-center mb-12">
        <h2 class="text-3xl sm:text-4xl font-bold text-slate-800 font-display">Veille sur les menaces</h2>
        <p class="text-slate-500 mt-2">Alimentée par des flux RSS et des sources de cybersécurité, classée par catégorie.</p>
        <div class="mt-4 flex flex-col items-center gap-2">
          <button
            :disabled="isLoading"
            class="px-6 py-2.5 bg-emerald-600 text-white font-semibold rounded-xl shadow-md hover:bg-emerald-700 transition disabled:opacity-60 flex items-center gap-2"
            @click="refresh"
          >
            <span v-if="isLoading" class="h-3.5 w-3.5 rounded-full border-2 border-white/60 border-t-white animate-spin"></span>
            {{ isLoading ? 'Actualisation…' : 'Actualiser' }}
          </button>
          <span v-if="lastUpdated && !isLoading" class="text-xs text-slate-400">
            Mis à jour {{ formatDate(lastUpdated) }}
          </span>
        </div>
      </div>

      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <article
          v-for="item in items"
          :key="item.id"
          class="bg-white rounded-xl shadow-card border border-slate-200 overflow-hidden transition hover:-translate-y-0.5 hover:shadow-lift"
        >
          <div class="p-4">
            <h4 class="text-sm font-semibold text-slate-800 mb-1.5">{{ item.title }}</h4>
            <p class="text-xs text-slate-500 leading-relaxed mb-2">{{ item.summary }}</p>
            <div class="flex justify-between text-xs text-slate-400">
              <span>{{ item.category }}</span>
              <span>{{ formatDate(item.date) }}</span>
            </div>
            <div class="mt-2 text-xs text-slate-400 font-medium">Source : {{ item.source }}</div>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>
