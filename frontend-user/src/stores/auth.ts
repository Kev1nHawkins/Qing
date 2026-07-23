import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '@/services/api'

interface User {
  id: number
  username: string
  nickname: string
  points_total: number
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const isLoggedIn = computed(() => Boolean(localStorage.getItem('accessToken')))

  async function login(username: string, password: string) {
    const { data } = await api.post('/auth/login', { username, password })
    localStorage.setItem('accessToken', data.data.access_token)
    user.value = data.data.user
  }

  async function fetchMe() {
    const { data } = await api.get('/auth/me')
    user.value = data.data
  }

  function logout() {
    localStorage.removeItem('accessToken')
    user.value = null
  }

  return { user, isLoggedIn, login, fetchMe, logout }
})

