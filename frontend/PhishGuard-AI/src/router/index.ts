import { createRouter, createWebHistory } from 'vue-router'
import { authService } from '@/services/auth.service'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to) {
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue')
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      meta: { requiresAuth: true },
      component: () => import('@/views/user/DashboardView.vue')
    },
    {
      path: '/dashboard/security',
      name: 'security',
      meta: { requiresAuth: true },
      component: () => import('@/views/user/SecurityView.vue')
    },
    {
      path: '/admin',
      name: 'admin',
      meta: { requiresAuth: true, requiresAdmin: true },
      component: () => import('@/views/admin/AdminView.vue')
    }
  ]
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true
  const user = await authService.me()
  if (!user) return { name: 'home', query: { auth: 'login' } }
  if (to.meta.requiresAdmin && !user.is_admin) return { name: 'dashboard' }
  return true
})

export default router
