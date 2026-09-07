<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { authService } from '@/services/auth.service'

const route = useRoute()
const router = useRouter()
const status = ref<'loading' | 'success' | 'error'>('loading')
const message = ref('Vérification de votre adresse email...')

onMounted(async () => {
  const email = typeof route.query.email === 'string' ? route.query.email : ''
  const token = typeof route.query.token === 'string' ? route.query.token : ''
  if (!email || !token) {
    status.value = 'error'
    message.value = 'Ce lien de vérification est incomplet.'
    return
  }

  try {
    await authService.verifyEmail(email, token)
    status.value = 'success'
    message.value = 'Votre email est vérifié. Vous pouvez maintenant vous connecter.'
  } catch {
    status.value = 'error'
    message.value = 'Ce lien est invalide ou a expiré.'
  }
})
</script>

<template>
  <main class="min-h-screen bg-slate-50 flex items-center justify-center p-6">
    <section class="bg-white rounded-2xl shadow-xl max-w-md w-full p-8 text-center">
      <div
        class="w-16 h-16 mx-auto rounded-full flex items-center justify-center text-2xl"
        :class="status === 'success' ? 'bg-emerald-100 text-emerald-600' : status === 'error' ? 'bg-red-100 text-red-600' : 'bg-blue-100 text-blue-600'"
      >
        <i :class="status === 'success' ? 'fas fa-check' : status === 'error' ? 'fas fa-xmark' : 'fas fa-spinner fa-spin'"></i>
      </div>
      <h1 class="text-2xl font-bold text-slate-800 mt-5">Vérification email</h1>
      <p class="text-slate-500 mt-3">{{ message }}</p>
      <button
        v-if="status !== 'loading'"
        class="mt-6 px-6 py-3 rounded-xl bg-blue-600 text-white font-semibold"
        @click="router.push({ name: 'home', query: { auth: 'login' } })"
      >
        Se connecter
      </button>
    </section>
  </main>
</template>
