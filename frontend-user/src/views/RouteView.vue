<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/services/api'
const routes = ref<any[]>([])
const error = ref('')
onMounted(async () => {
  try { routes.value = (await api.get('/routes')).data.data.items }
  catch (event) { error.value = (event as Error).message }
})
</script>
<template>
  <h1>校园寻迹</h1>
  <p class="muted">沿着校园路线边走边探索，完成有趣的文化任务吧！</p>
  <RouterLink class="button" to="/routes/journey">进入路线任务与积分兑换</RouterLink>
  <p v-if="error" class="status">{{ error }}</p>
  <div class="grid">
    <article v-for="route in routes" :key="route.id" class="card">
      <div class="eyebrow">{{ route.distance_km }} KM · {{ route.duration_minutes }} MIN</div>
      <h3>{{ route.title }}</h3><p class="muted">{{ route.summary }}</p>
    </article>
  </div>
</template>
