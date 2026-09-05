import { createRouter, createWebHistory } from 'vue-router'

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

router.beforeEach((to) => {
  if (to.path !== '/login' && !localStorage.getItem('adminAccessToken')) return '/login'
})

export default router
