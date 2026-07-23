import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: HomeView },
    { path: '/cultures', component: () => import('@/views/CultureView.vue') },
    { path: '/routes', component: () => import('@/views/RouteView.vue') },
    { path: '/community', component: () => import('@/views/CommunityView.vue') },
    { path: '/profile', component: () => import('@/views/ProfileView.vue') },
    { path: '/login', component: () => import('@/views/LoginView.vue') },
  ],
})

