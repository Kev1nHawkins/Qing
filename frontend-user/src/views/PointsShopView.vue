<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import PointsMall from '@/views/points/PointsMall.vue'
import type { PageData, PointRecord, ShopRedeemResult } from '@/types'

const auth = useAuthStore()
const router = useRouter()
const pointsTotal = ref(auth.user?.points_total ?? 0)
const pointRecords = ref<PointRecord[]>([])

async function refreshPoints() {
  if (!auth.isLoggedIn) {
    pointsTotal.value = 0
    pointRecords.value = []
    return
  }

  const [summaryResponse, recordsResponse] = await Promise.all([
    api.get<{ data: { pointsTotal: number } }>('/points/summary'),
    api.get<{ data: PageData<PointRecord> }>('/points/records', { params: { pageSize: 100 } }),
  ])
  pointsTotal.value = summaryResponse.data.data.pointsTotal
  pointRecords.value = recordsResponse.data.data.items
  if (auth.user) auth.user.points_total = pointsTotal.value
}

function requestLogin() {
  router.push({ path: '/login', query: { redirect: '/points-shop' } })
}

async function handleRedeemed(result: ShopRedeemResult) {
  pointsTotal.value = result.pointsTotal
  if (auth.user) auth.user.points_total = result.pointsTotal
  await refreshPoints()
}

onMounted(() => {
  refreshPoints().catch(() => undefined)
})
</script>

<template>
  <div class="points-shop-page">
    <PointsMall
      :points-total="pointsTotal"
      :logged-in="auth.isLoggedIn"
      :point-records="pointRecords"
      @login="requestLogin"
      @redeemed="handleRedeemed"
    />
  </div>
</template>

<style scoped>
.points-shop-page {
  width: min(1440px, calc(100% - 40px));
  margin: 0 auto;
  padding: 32px 0 72px;
}

.points-shop-page :deep(.points-mall) {
  margin-top: 0;
}

@media (max-width: 720px) {
  .points-shop-page {
    width: min(100% - 24px, 1440px);
    padding-top: 18px;
  }
}
</style>
