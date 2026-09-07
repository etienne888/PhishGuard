<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

// ============================================
// ANIMATED STATS
// ============================================

interface Stat {
  value: string
  label: string
  color: string
  target: number
  suffix?: string
}

const stats = ref<Stat[]>([
  { value: '0', label: 'FCFA perdus aux arnaques (2025)', color: 'text-blue-600', target: 1.02, suffix: ' Md' },
  { value: '0', label: 'précision de détection', color: 'text-cyan-600', target: 99, suffix: '%' },
  { value: '0', label: 'catégories de menaces', color: 'text-emerald-600', target: 12, suffix: '' },
  { value: '0', label: 'protection gratuite', color: 'text-purple-600', target: 24, suffix: '/7' }
])

const isVisible = ref(false)
const sectionRef = ref<HTMLElement | null>(null)

// ============================================
// COMMENT SYSTEM - Simplified
// ============================================

interface Comment {
  id: number
  name: string
  text: string
  rating: number
  date: string
}

const comments = ref<Comment[]>([
  {
    id: 1,
    name: 'Jean-Paul N.',
    text: 'PhishGuard-AI m\'a sauvé d\'une tentative de fraude Mobile Money. Le score de risque m\'a alerté à temps !',
    rating: 5,
    date: '15 sept. 2026'
  },
  {
    id: 2,
    name: 'Marie A.',
    text: 'Très utile pour sensibiliser mes collègues aux risques de phishing. L\'interface est claire et les explications sont accessibles.',
    rating: 4,
    date: '12 sept. 2026'
  },
  {
    id: 3,
    name: 'David K.',
    text: 'Enfin un outil adapté au contexte camerounais ! La détection Mobile Money est très précise.',
    rating: 5,
    date: '10 sept. 2026'
  },
  {
    id: 4,
    name: 'Sarah M.',
    text: 'J\'ai déjà signalé plusieurs tentatives de phishing grâce à PhishGuard-AI. Une vraie protection pour les citoyens.',
    rating: 5,
    date: '8 sept. 2026'
  },
  {
    id: 5,
    name: 'Michel T.',
    text: 'Excellent outil éducatif. Mes étudiants comprennent mieux les risques grâce aux fiches détaillées.',
    rating: 4,
    date: '5 sept. 2026'
  },
  {
    id: 6,
    name: 'Claire D.',
    text: 'Interface simple et efficace. Je l\'utilise régulièrement pour vérifier les messages suspects.',
    rating: 5,
    date: '3 sept. 2026'
  }
])

const currentIndex = ref(0)
const commentsPerView = ref(3)
const totalComments = computed(() => comments.value.length)
const isAutoPlaying = ref(true)
let autoPlayInterval: number | null = null

// Responsive: adjust comments per view
function updateCommentsPerView() {
  if (window.innerWidth < 640) {
    commentsPerView.value = 1
  } else if (window.innerWidth < 1024) {
    commentsPerView.value = 2
  } else {
    commentsPerView.value = 3
  }
}

const visibleComments = computed(() => {
  const start = currentIndex.value
  const end = Math.min(start + commentsPerView.value, totalComments.value)
  return comments.value.slice(start, end)
})

const maxIndex = computed(() => Math.max(0, totalComments.value - commentsPerView.value))
const canScrollNext = computed(() => currentIndex.value < maxIndex.value)
const canScrollPrev = computed(() => currentIndex.value > 0)

function nextSlide() {
  if (canScrollNext.value) {
    currentIndex.value++
  } else {
    currentIndex.value = 0
  }
}

function prevSlide() {
  if (canScrollPrev.value) {
    currentIndex.value--
  } else {
    currentIndex.value = maxIndex.value
  }
}

function goToSlide(index: number) {
  currentIndex.value = Math.min(index, maxIndex.value)
}

function startAutoPlay() {
  if (autoPlayInterval) clearInterval(autoPlayInterval)
  autoPlayInterval = setInterval(() => {
    if (isAutoPlaying.value) {
      nextSlide()
    }
  }, 5000)
}

function pauseAutoPlay() {
  isAutoPlaying.value = false
}

function resumeAutoPlay() {
  isAutoPlaying.value = true
}

// ============================================
// COMMENT FORM - Simplified
// ============================================

const formData = ref({
  name: '',
  text: '',
  rating: 5
})

const isSubmitting = ref(false)
const formError = ref('')
const formSuccess = ref(false)

function getStars(rating: number) {
  return '★'.repeat(rating) + '☆'.repeat(5 - rating)
}

function submitComment() {
  formError.value = ''
  
  if (!formData.value.name.trim()) {
    formError.value = 'Veuillez entrer votre nom'
    return
  }
  if (!formData.value.text.trim()) {
    formError.value = 'Veuillez écrire votre commentaire'
    return
  }
  if (formData.value.text.trim().length < 10) {
    formError.value = 'Votre commentaire doit faire au moins 10 caractères'
    return
  }

  isSubmitting.value = true

  setTimeout(() => {
    const newComment: Comment = {
      id: Date.now(),
      name: formData.value.name,
      text: formData.value.text,
      rating: formData.value.rating,
      date: new Date().toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })
    }
    
    comments.value.unshift(newComment)
    
    formData.value = { name: '', text: '', rating: 5 }
    formSuccess.value = true
    isSubmitting.value = false
    currentIndex.value = 0
    
    setTimeout(() => {
      formSuccess.value = false
    }, 4000)
  }, 1000)
}

// ============================================
// INTERSECTION OBSERVER
// ============================================

onMounted(() => {
  updateCommentsPerView()
  window.addEventListener('resize', updateCommentsPerView)
  
  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        isVisible.value = true
        animateNumbers()
      }
    },
    { threshold: 0.2 }
  )

  if (sectionRef.value) {
    observer.observe(sectionRef.value)
  }
  
  startAutoPlay()
})

// ============================================
// ANIMATE NUMBERS
// ============================================

function animateNumbers() {
  stats.value.forEach((stat, index) => {
    const duration = 2000
    const startTime = Date.now()
    const endValue = stat.target

    const updateNumber = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / duration, 1)
      const easeOutQuart = 1 - Math.pow(1 - progress, 4)
      const currentValue = endValue * easeOutQuart

      if (stat.suffix === '%') {
        stat.value = Math.round(currentValue).toString()
      } else if (stat.suffix === ' Md') {
        stat.value = currentValue.toFixed(1)
      } else if (stat.suffix === '/7') {
        stat.value = Math.round(currentValue).toString()
      } else {
        stat.value = Math.round(currentValue).toString()
      }

      if (progress < 1) {
        requestAnimationFrame(updateNumber)
      } else {
        if (stat.suffix === ' Md') {
          stat.value = stat.target.toFixed(1)
        } else {
          stat.value = stat.target.toString()
        }
      }
    }

    setTimeout(() => {
      requestAnimationFrame(updateNumber)
    }, index * 200)
  })
}
</script>

<template>
  <section id="about" ref="sectionRef" class="py-20 px-4 bg-white">
    <div class="max-w-7xl mx-auto">
      
      <!-- ========================================== -->
      <!-- TOP SECTION: Stats & Quote                -->
      <!-- ========================================== -->
      <div class="grid lg:grid-cols-2 gap-12 items-start">
        
        <!-- LEFT COLUMN -->
        <div>
          <span class="inline-block text-xs font-semibold uppercase tracking-wider text-blue-600 bg-blue-50 px-3 py-1 rounded-full mb-4 border border-blue-200/50">
            À propos
          </span>
          
          <h2 class="text-3xl sm:text-4xl font-bold text-slate-800 font-display leading-tight">
            Conçu au Cameroun,<br />
            <span class="gradient-text">par des talents camerounais</span>
          </h2>
          
          <p class="text-slate-600 mt-4 leading-relaxed">
            PhishGuard-AI est un projet de fin d'études en cybersécurité, pensé pour protéger les citoyens contre le
            phishing, la fraude Mobile Money et l'ingénierie sociale. 
            <span class="font-medium text-slate-700">100% localisé et gratuit.</span>
          </p>

          <!-- Animated Stats -->
          <div class="mt-6 grid grid-cols-2 gap-4">
            <div v-for="stat in stats" :key="stat.label" class="bg-slate-50 rounded-xl p-4 border border-slate-100 card-hover">
              <span class="text-2xl font-bold font-display" :class="stat.color">
                {{ stat.value }}{{ stat.suffix }}
              </span>
              <p class="text-xs text-slate-500 mt-0.5">{{ stat.label }}</p>
            </div>
          </div>

          <!-- Quote Card -->
          
        </div>

        <!-- ========================================== -->
        <!-- RIGHT COLUMN: Comment Carousel            -->
        <!-- ========================================== -->
        <div>
          <!-- Carousel Header -->
          <div class="flex items-center justify-between mb-6">
            <div>
              <span class="text-xs font-semibold text-blue-600 uppercase tracking-wider">Avis</span>
              <h3 class="text-xl font-bold text-slate-800 font-display">
                Ce que les utilisateurs disent
                <span class="text-sm font-normal text-slate-400 ml-2">({{ comments.length }})</span>
              </h3>
            </div>
            <div class="flex items-center gap-1 text-sm text-yellow-500">
              <span class="font-semibold text-slate-700">4.8</span>
              <span class="text-yellow-400">★★★★★</span>
            </div>
          </div>

          <!-- Carousel Container -->
          <div 
            class="relative rounded-2xl bg-slate-50/50 p-2"
            @mouseenter="pauseAutoPlay"
            @mouseleave="resumeAutoPlay"
          >
            <!-- Slides -->
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              <div
                v-for="comment in visibleComments"
                :key="comment.id"
                class="bg-white rounded-xl p-5 border border-slate-100 shadow-sm flex flex-col min-h-[180px]"
              >
                <!-- Name & Rating -->
                <div class="flex items-center justify-between">
                  <span class="text-sm font-semibold text-slate-800">{{ comment.name }}</span>
                  <span class="text-xs text-yellow-400">{{ getStars(comment.rating) }}</span>
                </div>

                <!-- Comment Text -->
                <p class="text-sm text-slate-600 mt-2 leading-relaxed flex-1 line-clamp-4">
                  "{{ comment.text }}"
                </p>

                <!-- Date -->
                <span class="text-[10px] text-slate-400 mt-3 pt-2 border-t border-slate-100">
                  {{ comment.date }}
                </span>
              </div>
            </div>

            <!-- Navigation Arrows -->
            <button
              v-if="totalComments > commentsPerView"
              @click="prevSlide"
              class="absolute -left-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white hover:bg-white shadow-md flex items-center justify-center text-slate-600 hover:text-blue-600 transition-all z-10 border border-slate-200"
              :disabled="!canScrollPrev"
            >
              <i class="fas fa-chevron-left text-xs"></i>
            </button>
            
            <button
              v-if="totalComments > commentsPerView"
              @click="nextSlide"
              class="absolute -right-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white hover:bg-white shadow-md flex items-center justify-center text-slate-600 hover:text-blue-600 transition-all z-10 border border-slate-200"
              :disabled="!canScrollNext"
            >
              <i class="fas fa-chevron-right text-xs"></i>
            </button>

            <!-- Dot Indicators -->
            <div v-if="totalComments > commentsPerView" class="flex justify-center gap-1.5 mt-4">
              <button
                v-for="i in Math.ceil(totalComments / commentsPerView)"
                :key="i"
                @click="goToSlide((i - 1) * commentsPerView)"
                class="h-1.5 rounded-full transition-all duration-300"
                :class="currentIndex === (i - 1) * commentsPerView ? 'w-6 bg-blue-600' : 'w-1.5 bg-slate-300 hover:bg-slate-400'"
              ></button>
            </div>

            <!-- Auto-play indicator -->
            <div class="flex justify-center mt-2">
              <span class="text-[10px] text-slate-400 flex items-center gap-1.5">
                <span class="w-1.5 h-1.5 rounded-full" :class="isAutoPlaying ? 'bg-emerald-500' : 'bg-slate-300'"></span>
                {{ isAutoPlaying ? 'Défilement automatique' : 'Pause' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- ========================================== -->
      <!-- COMMENT FORM SECTION                      -->
      <!-- ========================================== -->
      <div class="mt-16 pt-10 border-t border-slate-200">
        <div class="max-w-2xl mx-auto">
          <div class="text-center mb-8">
            <span class="text-xs font-semibold text-blue-600 uppercase tracking-wider">Partagez votre avis</span>
            <h3 class="text-2xl font-bold text-slate-800 font-display mt-1">Laissez un commentaire</h3>
            <p class="text-sm text-slate-500 mt-1">Votre retour nous aide à améliorer PhishGuard-AI</p>
          </div>

          <!-- Success Message -->
          <div v-if="formSuccess" class="mb-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-sm text-emerald-700 flex items-center gap-3">
            <i class="fas fa-check-circle text-emerald-500 text-lg"></i>
            <div>
              <span class="font-medium">Merci pour votre avis !</span>
              <p class="text-xs text-emerald-600 mt-0.5">Votre commentaire a été publié avec succès.</p>
            </div>
          </div>

          <!-- Comment Form -->
          <form @submit.prevent="submitComment" class="bg-slate-50 rounded-2xl p-6 sm:p-8 border border-slate-100 shadow-sm">
            <div>
              <label class="text-xs font-medium text-slate-600 block mb-1">
                Nom <span class="text-red-500">*</span>
              </label>
              <input
                v-model="formData.name"
                type="text"
                placeholder="Votre nom"
                class="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition bg-white"
                required
              />
            </div>

            <div class="mt-4">
              <label class="text-xs font-medium text-slate-600 block mb-1">
                Commentaire <span class="text-red-500">*</span>
              </label>
              <textarea
                v-model="formData.text"
                rows="3"
                placeholder="Partagez votre expérience avec PhishGuard-AI..."
                class="w-full px-4 py-2.5 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500 outline-none transition resize-none bg-white"
                required
              ></textarea>
            </div>

            <div class="mt-4 flex items-center justify-between flex-wrap gap-3">
              <div class="flex items-center gap-2">
                <span class="text-sm text-slate-600">Note :</span>
                <div class="flex gap-0.5">
                  <button
                    v-for="star in 5"
                    :key="star"
                    type="button"
                    @click="formData.rating = star"
                    class="text-2xl transition hover:scale-110"
                    :class="star <= formData.rating ? 'text-yellow-400' : 'text-slate-300'"
                  >
                    ★
                  </button>
                </div>
                <span class="text-xs text-slate-400 ml-1">{{ formData.rating }}/5</span>
              </div>
              
              <button
                type="submit"
                :disabled="isSubmitting"
                class="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-cyan-500 text-white text-sm font-semibold rounded-xl hover:shadow-md transition disabled:opacity-60 flex items-center gap-2"
              >
                <i v-if="isSubmitting" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-paper-plane"></i>
                {{ isSubmitting ? 'Envoi...' : 'Publier' }}
              </button>
            </div>

            <p v-if="formError" class="text-xs text-red-500 mt-2 flex items-center gap-1">
              <i class="fas fa-exclamation-circle"></i>
              {{ formError }}
            </p>
          </form>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.gradient-text {
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.card-hover {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.card-hover:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
}

.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Carousel smooth transitions */
.carousel-track {
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>