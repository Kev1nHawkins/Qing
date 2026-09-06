import { createRouter, createWebHistory } from 'vue-router'
import {
  clearAdminSession,
  hasValidAdminToken,
  readAdminToken,
  verifyAdminSession,
} from '@/services/adminSession'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/LoginView.vue') },
    { path: '/', component: () => import('@/views/DashboardView.vue') },
    { path: '/users', component: () => import('@/views/UserManageView.vue') },
    { path: '/cultures', component: () => import('@/views/CultureManageView.vue') },
    {
      path: '/routes',
      component: () => import('@/views/RouteTaskManageView.vue'),
    },
    {
      path: '/templates',
      component: () => import('@/views/CreationTemplateManageView.vue'),
    },
    {
      path: '/posts',
      component: () => import('@/views/PostManageView.vue'),
    },
  ],
})

router.beforeEach(async (to) => {
  const token = readAdminToken()
  if (token && !hasValidAdminToken()) {
    clearAdminSession('登录状态已过期，请重新登录。')
  }
  if (!hasValidAdminToken()) {
    if (to.path === '/login') return true
    return { path: '/login', query: { redirect: to.fullPath } }
  }

  const verification = await verifyAdminSession()
  if (!verification.valid) {
    const message = verification.reason === 'forbidden'
      ? '当前账号没有管理员权限。'
      : '登录状态已过期，请重新登录。'
    clearAdminSession(message)
    if (to.path === '/login') return true
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login') return '/'
  return true
})

export default router
