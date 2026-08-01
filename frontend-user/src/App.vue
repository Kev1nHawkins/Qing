<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink, RouterView } from 'vue-router'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function restoreSession() {
  if (!auth.isLoggedIn || auth.user) return
  try {
    await auth.fetchMe()
  } catch {
    auth.logout()
    if (router.currentRoute.value.meta.requiresAuth) {
      await router.replace({
        path: '/login',
        query: { redirect: router.currentRoute.value.fullPath },
      })
    }
  }
}

async function logout() {
  auth.logout()
  await router.push('/')
}

onMounted(restoreSession)
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/">岭潮共创</RouterLink>
      <div class="topbar-actions">
        <span class="tagline">岭南文化 × 校园文化 × AI</span>
        <template v-if="auth.user">
          <RouterLink class="topbar-user" to="/profile">
            <strong>{{ auth.user.nickname }}</strong>
            <small>{{ auth.user.points_total }} 积分</small>
          </RouterLink>
          <button class="topbar-logout" type="button" @click="logout">退出</button>
        </template>
        <template v-else>
          <RouterLink class="topbar-login" to="/login">登录</RouterLink>
          <RouterLink class="topbar-register" to="/register">注册</RouterLink>
        </template>
      </div>
    </header>
    <main><RouterView /></main>
    <nav class="bottom-nav" aria-label="主要导航">
      <RouterLink to="/">探索</RouterLink>
      <RouterLink to="/cultures">文化</RouterLink>
      <RouterLink to="/routes">寻迹</RouterLink>
      <RouterLink to="/creation">共创</RouterLink>
      <RouterLink to="/community">社区</RouterLink>
    </nav>
  </div>
</template>

