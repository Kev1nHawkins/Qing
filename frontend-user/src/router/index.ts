import { createRouter, createWebHistory } from 'vue-router'
import ExperienceView from '@/views/ExperienceView.vue'

export default createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    { path: '/', name: 'home', component: ExperienceView },
    { path: '/cultures', name: 'cultures', component: ExperienceView },
    { path: '/cultures/:slug', name: 'culture-detail', component: ExperienceView },
    { path: '/routes', name: 'routes', component: ExperienceView },
    { path: '/guide', name: 'guide', component: ExperienceView },
    { path: '/create', name: 'create', component: ExperienceView },
    { path: '/community', name: 'community', component: ExperienceView },
    { path: '/profile', name: 'profile', component: ExperienceView },
    { path: '/login', redirect: { name: 'profile' } },
    { path: '/:pathMatch(.*)*', redirect: { name: 'home' } },
  ],
})
