import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/cultures', component: () => import('@/views/CultureView.vue') },
    { path: '/routes', component: () => import('@/views/RouteView.vue') },
    {
      path: '/routes/journey',
      component: () => import('@/views/route/RouteJourney.vue'),
    },
    {
      path: '/routes/:routeId/tasks/:taskId/quiz',
      component: () => import('@/views/route/LibraryQuiz.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/creation',
      component: () => import('@/views/CreationView.vue'),
      meta: { requiresAuth: true },
    },
    { path: '/community', component: () => import('@/views/CommunityView.vue') },
    { path: '/profile', component: () => import('@/views/ProfileView.vue'), meta: { requiresAuth: true } },
    { path: '/login', component: () => import('@/views/LoginView.vue') },
    { path: '/register', component: () => import('@/views/RegisterView.vue') },
  ],
})

router.beforeEach((to) => {
  const loggedIn = Boolean(localStorage.getItem('accessToken'))
  if (to.meta.requiresAuth && !loggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if ((to.path === '/login' || to.path === '/register') && loggedIn) return '/'
})

export default router

