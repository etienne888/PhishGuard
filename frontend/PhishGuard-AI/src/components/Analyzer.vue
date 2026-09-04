<script setup lang="ts">
import { computed, ref } from 'vue'
import { useAnalysis } from '@/composables'
import { useNotificationsStore } from '@/stores'

const { result, isAnalyzing, error, examples, analyze, reset, report } = useAnalysis()
const notifications = useNotificationsStore()

const draft = ref('')

function runAnalysis(text?: string) {
  const value = text ?? draft.value
  draft.value = value
  analyze(value)
}

function loadExample(text: string) {
  draft.value = text
  runAnalysis(text)
}

function clearAll() {
  draft.value = ''
  reset()
}

async function handleReport() {
  await report()
  notifications.push('Message signalé au CIRT-CM (démo).', 'success')
}

const verdictLabel = computed(() => {
  if (!result.value) return ''
  return { phishing: 'Phishing probable', suspicious: 'Suspect', legitimate: 'Légitime' }[result.value.verdict]
})

const verdictTone = computed(() => {
  if (!result.value) return { text: '', bar: '', chip: '' }
  return {
    phishing: { text: 'text-red-600', bar: 'bg-red-500', chip: 'text-red-400' },
    suspicious: { text: 'text-amber-600', bar: 'bg-amber-500', chip: 'text-amber-400' },
    legitimate: { text: 'text-emerald-600', bar: 'bg-emerald-500', chip: 'text-emerald-400' }
  }[result.value.verdict]
})
</script>

<template>
  <section id="analyze" class="py-20 px-4 bg-white">
    <div class="max-w-4xl mx-auto">
      <div class="text-center mb-12">
        <h2 class="text-3xl sm:text-4xl font-bold text-slate-800 font-display">Collez &amp; détectez</h2>
        <p class="text-slate-500 mt-2">Copiez un message suspect, collez-le ci-dessous, et obtenez un score de risque instantané.</p>
      </div>

      <div class="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
        <div class="p-6 sm:p-8">
          <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 font-semibold">Aa</div>
            <div>
              <span class="text-sm font-semibold text-slate-700">Collez votre message</span>
              <p class="text-xs text-slate-400">SMS, email, WhatsApp, ou tout autre texte</p>
            </div>
          </div>

          <textarea
            v-model="draft"
            rows="5"
            class="w-full p-4 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition resize-none text-sm text-slate-700 placeholder:text-slate-400"
            placeholder="Collez un message suspect ici…&#10;Exemple : « Cher client MTN, votre compte a été bloqué... »"
          ></textarea>

          <p v-if="error" class="mt-2 text-sm text-amber-600">{{ error }}</p>

          <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <button
                :disabled="isAnalyzing"
                class="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 text-white font-semibold rounded-xl shadow-md shadow-blue-500/25 hover:shadow-blue-500/40 transition hover:scale-[1.02] active:scale-[0.98] disabled:opacity-60 disabled:hover:scale-100 flex items-center gap-2"
                @click="runAnalysis()"
              >
                <span v-if="isAnalyzing" class="h-3.5 w-3.5 rounded-full border-2 border-white/60 border-t-white animate-spin"></span>
                {{ isAnalyzing ? 'Analyse…' : 'Analyser' }}
              </button>
              <button class="px-4 py-2.5 text-sm text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition" @click="clearAll">
                Effacer
              </button>
            </div>
            <span class="text-xs text-slate-400">Vos données ne sont pas conservées</span>
          </div>
        </div>

        <Transition name="fade">
          <div v-if="result" class="border-t border-slate-100 p-6 sm:p-8 bg-slate-50/80">
            <div class="flex items-start gap-4">
              <div class="flex-1">
                <div class="flex items-center justify-between flex-wrap gap-2">
                  <span class="text-xl font-bold font-display" :class="verdictTone.text">{{ verdictLabel }}</span>
                  <span class="text-sm font-semibold" :class="verdictTone.text">{{ result.score }}% de risque</span>
                </div>
                <div class="mt-2 h-2.5 w-full bg-slate-200 rounded-full overflow-hidden">
                  <div class="h-full rounded-full transition-all duration-500" :class="verdictTone.bar" :style="{ width: result.score + '%' }"></div>
                </div>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span
                    v-for="indicator in result.indicators"
                    :key="indicator.label"
                    class="text-xs px-3 py-1 bg-white/70 rounded-full border border-slate-200 text-slate-600 inline-flex items-center gap-1.5"
                  >
                    <span class="h-1.5 w-1.5 rounded-full" :class="indicator.positive ? 'bg-emerald-400' : 'bg-red-400'"></span>
                    {{ indicator.label }}
                  </span>
                </div>
              </div>
            </div>
            <div class="mt-4 flex gap-2">
              <button
                class="text-xs px-4 py-1.5 bg-red-100 text-red-700 rounded-full hover:bg-red-200 transition font-medium border border-red-200"
                @click="handleReport"
              >
                Signaler
              </button>
              <a
                href="#education"
                class="text-xs px-4 py-1.5 bg-blue-50 text-blue-700 rounded-full hover:bg-blue-100 transition font-medium border border-blue-200"
              >
                En savoir plus
              </a>
            </div>
          </div>
        </Transition>
      </div>

      <div class="mt-6 flex flex-wrap gap-2 justify-center">
        <span class="text-xs text-slate-400 mr-1">Tester avec :</span>
        <button
          v-for="example in examples"
          :key="example.id"
          class="text-xs px-3 py-1.5 bg-slate-100 hover:bg-slate-200 rounded-full transition text-slate-600"
          @click="loadExample(example.text)"
        >
          {{ example.label }}
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
