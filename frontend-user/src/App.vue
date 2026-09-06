<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import gzuOfficialLogo from '@/assets/culture/gzu-official-logo.png'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const immersive = computed(() => Boolean(route.meta.immersive))

async function restoreSession() {
  if (!auth.isLoggedIn || auth.user) return
  try {
    await auth.fetchMe()
  } catch {
    auth.logout()
    if (router.currentRoute.value.meta.requiresAuth) {
      await router.replace({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
    }
  }
}

async function logout() {
  auth.logout()
  await router.push('/')
}

function followNavigation(event: PointerEvent) {
  if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey) return
  const link = (event.target as HTMLElement).closest<HTMLAnchorElement>('a[href]')
  if (link?.closest('.desktop-nav, .bottom-nav')) window.location.assign(link.href)
}

onMounted(restoreSession)
</script>

<template>
  <div class="app-shell">
    <header class="site-header">
      <RouterLink class="site-brand" to="/" aria-label="岭潮共创首页">
        <span class="brand-seal">岭</span>
        <span class="brand-title">岭潮共创<small>LINGNAN · GZHU</small></span>
        <span class="brand-divider" aria-hidden="true" />
        <img :src="gzuOfficialLogo" alt="广州大学" />
      </RouterLink>
      <nav class="desktop-nav" aria-label="主导航" @pointerdown="followNavigation">
        <a href="/">探索</a>
        <a href="/cultures">文化</a>
        <a href="/routes">寻迹</a>
        <a href="/creation">共创</a>
        <a href="/community">社区</a>
      </nav>
      <div class="account-actions">
        <template v-if="auth.user">
          <RouterLink class="account-user" to="/profile">
            <strong>{{ auth.user.nickname }}</strong>
            <small>{{ auth.user.points_total }} 积分</small>
          </RouterLink>
          <button type="button" @click="logout">退出</button>
        </template>
        <template v-else>
          <RouterLink to="/login">登录</RouterLink>
          <RouterLink class="account-primary" to="/register">注册</RouterLink>
        </template>
      </div>
    </header>
    <main class="app-main" :class="{ 'is-immersive': immersive }"><RouterView /></main>
    <nav class="bottom-nav" aria-label="移动端主导航" @pointerdown="followNavigation">
      <a href="/">探索</a>
      <a href="/cultures">文化</a>
      <a href="/routes">寻迹</a>
      <a href="/creation">共创</a>
      <a href="/community">社区</a>
    </nav>
  </div>
</template>

<style>
.site-header { z-index: 100; }
.desktop-nav, .account-actions { position: relative; z-index: 101; }
</style>
