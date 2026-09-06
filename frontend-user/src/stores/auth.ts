import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '@/services/api'

interface User {
  id: number
  username: string
  nickname: string
  points_total: number
}

interface RegisterPayload {
  username: string
  email?: string
  password: string
  nickname: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref(localStorage.getItem('accessToken') || '')
  const isLoggedIn = computed(() => Boolean(token.value))

  function applySession(accessToken: string, sessionUser: User) {
    localStorage.setItem('accessToken', accessToken)
    token.value = accessToken
    user.value = sessionUser
  }

  async function login(username: string, password: string) {
    const { data } = await api.post('/auth/login', { username, password })
    applySession(data.data.access_token, data.data.user)
  }

  async function register(payload: RegisterPayload) {
    const { data } = await api.post('/auth/register', {
      ...payload,
      email: payload.email || null,
    })
    applySession(data.data.access_token, data.data.user)
  }

  async function fetchMe() {
    const { data } = await api.get('/auth/me')
    user.value = data.data
  }

  function logout() {
    localStorage.removeItem('accessToken')
    token.value = ''
    user.value = null
  }

  return { user, isLoggedIn, login, register, fetchMe, logout }
})
