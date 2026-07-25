import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/views/LoginView.vue') },
    { path: '/', component: () => import('@/views/DashboardView.vue') },
    { path: '/cultures', component: () => import('@/views/CultureManageView.vue') },
    {
      path: '/routes',
      component: () => import('@/views/RouteTaskManageView.vue'),
    },
    {
      path: '/templates',
      component: () => import('@/views/PlaceholderView.vue'),
      props: { title: 'AI 模板', note: '由成员 3 在此接入 Prompt 与生成模板管理。' },
    },
    {
      path: '/posts',
      component: () => import('@/views/PlaceholderView.vue'),
      props: { title: '社区审核', note: '由成员 5 在此接入帖子审核与下架操作。' },
    },
  ],
})

router.beforeEach((to) => {
  if (to.path !== '/login' && !localStorage.getItem('adminAccessToken')) return '/login'
})

export default router
