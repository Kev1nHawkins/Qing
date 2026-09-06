<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import PointsMall from '@/views/points/PointsMall.vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import gzuOfficialLogo from '@/assets/culture/gzu-official-logo.png'
import type { PageData, PointRecord, ShopRedeemResult } from '@/types'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const immersive = computed(() => Boolean(route.meta.immersive))
const shopOpen = ref(false)
const pointRecords = ref<PointRecord[]>([])

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
  shopOpen.value = false
  auth.logout()
  await router.push('/')
}

async function refreshShopAccount() {
  if (!auth.isLoggedIn) {
    pointRecords.value = []
    return
  }
  const [summaryResponse, recordsResponse] = await Promise.all([
    api.get<{ data: { pointsTotal: number } }>('/points/summary'),
    api.get<{ data: PageData<PointRecord> }>('/points/records', { params: { pageSize: 100 } }),
  ])
  if (auth.user) auth.user.points_total = summaryResponse.data.data.pointsTotal
  pointRecords.value = recordsResponse.data.data.items
}

async function openShop() {
  shopOpen.value = true
  try {
    await refreshShopAccount()
  } catch {
    pointRecords.value = []
  }
}

async function requestShopLogin() {
  shopOpen.value = false
  await router.push({ path: '/login', query: { redirect: route.fullPath } })
}

async function handleShopRedeemed(result: ShopRedeemResult) {
  if (auth.user) auth.user.points_total = result.pointsTotal
  await refreshShopAccount()
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
      <nav class="desktop-nav" aria-label="主导航">
        <RouterLink to="/">探索</RouterLink>
        <RouterLink to="/cultures">文化</RouterLink>
        <RouterLink to="/routes">寻迹</RouterLink>
        <RouterLink to="/creation">共创</RouterLink>
        <RouterLink to="/community">社区</RouterLink>
      </nav>
      <div class="account-actions">
        <template v-if="auth.user">
          <button class="account-user points-entry" type="button" aria-haspopup="dialog" @click="openShop">
            <strong>{{ auth.user.nickname }}</strong>
            <small>{{ auth.user.points_total }} 积分</small>
          </button>
          <button type="button" @click="logout">退出</button>
        </template>
        <template v-else>
          <RouterLink to="/login">登录</RouterLink>
          <RouterLink class="account-primary" to="/register">注册</RouterLink>
        </template>
      </div>
    </header>
    <main class="app-main" :class="{ 'is-immersive': immersive }"><RouterView /></main>
    <div v-if="shopOpen" class="global-shop" role="dialog" aria-modal="true" aria-label="积分商店" @click.self="shopOpen = false">
      <div class="global-shop-panel">
        <button class="global-shop-close" type="button" aria-label="关闭积分商店" @click="shopOpen = false">×</button>
        <PointsMall
          :points-total="auth.user?.points_total || 0"
          :logged-in="auth.isLoggedIn"
          :point-records="pointRecords"
          @login="requestShopLogin"
          @redeemed="handleShopRedeemed"
        />
      </div>
    </div>
    <nav class="bottom-nav" aria-label="移动端主导航">
      <RouterLink to="/">探索</RouterLink>
      <RouterLink to="/cultures">文化</RouterLink>
      <RouterLink to="/routes">寻迹</RouterLink>
      <RouterLink to="/creation">共创</RouterLink>
      <RouterLink to="/community">社区</RouterLink>
    </nav>
  </div>
</template>

<style scoped>
.points-entry {
  text-align: right;
}

.global-shop {
  position: fixed;
  z-index: 70;
  inset: 0;
  overflow: auto;
  padding: 28px;
  background: rgba(17, 34, 28, 0.72);
  backdrop-filter: blur(7px);
}

.global-shop-panel {
  position: relative;
  width: min(1240px, 100%);
  margin: 0 auto;
}

.global-shop-panel :deep(.points-mall) {
  margin-top: 0;
}

.global-shop-close {
  position: sticky;
  z-index: 3;
  top: 12px;
  float: right;
  width: 42px;
  height: 42px;
  margin: 12px 12px -54px 0;
  border: 1px solid rgba(255, 255, 255, 0.45);
  border-radius: 50%;
  color: #fff;
  background: rgba(17, 61, 49, 0.75);
  font-size: 27px;
  line-height: 1;
  cursor: pointer;
}

@media (max-width: 720px) {
  .global-shop {
    padding: 10px;
  }

  .global-shop-close {
    top: 6px;
    margin: 6px 6px -48px 0;
  }
}
</style>
