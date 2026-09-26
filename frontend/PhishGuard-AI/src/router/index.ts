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
      // The checker on its own page; also the PWA share target and email result links
      path: '/check',
      name: 'check',
      component: () => import('@/views/CheckView.vue')
    },
    {
      path: '/learn',
      name: 'learn',
      component: () => import('@/views/LearnView.vue')
    },
    {
      path: '/privacy',
      name: 'privacy',
      component: () => import('@/views/PrivacyView.vue')
    },
    {
      path: '/dashboard/mailboxes',
      name: 'mailboxes',
      meta: { requiresAuth: true },
      component: () => import('@/views/user/MailboxesView.vue')
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
      path: '/verify-email',
      name: 'verify-email',
      component: () => import('@/views/VerifyEmailView.vue')
    },
    {
      path: '/admin',
      meta: { requiresAuth: true, requiresAdmin: true },
      component: () => import('@/views/admin/AdminLayout.vue'),
      children: [
        { path: '', name: 'admin-overview', component: () => import('@/views/admin/Overview.vue') },
        { path: 'users', name: 'admin-users', component: () => import('@/views/admin/UserManagement.vue') },
        { path: 'reports', name: 'admin-reports', component: () => import('@/views/admin/ReviewQueue.vue') },
        { path: 'whitelist', name: 'admin-whitelist', component: () => import('@/views/admin/Whitelist.vue') },
        // meta.demo: screen still shows sample data (AdminLayout shows a banner)
        { path: 'incidents', name: 'admin-incidents', component: () => import('@/views/admin/Incidents.vue') },
        { path: 'radar', name: 'admin-radar', component: () => import('@/views/admin/RadarView.vue') },
        { path: 'threat-intel', name: 'admin-threat-intel', component: () => import('@/views/admin/ThreatIntelligence.vue') },
        { path: 'models', name: 'admin-models', meta: { demo: true }, component: () => import('@/views/admin/MLModelManagement.vue') },
        { path: 'integrations', name: 'admin-integrations', meta: { demo: true }, component: () => import('@/views/admin/Integrations.vue') },
        { path: 'health', name: 'admin-health', component: () => import('@/views/admin/Health.vue') },
        { path: 'audit', name: 'admin-audit', component: () => import('@/views/admin/AuditLog.vue') },
        { path: 'settings', name: 'admin-settings', component: () => import('@/views/admin/Settings.vue') }
      ]
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
