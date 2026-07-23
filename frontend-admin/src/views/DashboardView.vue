<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '@/services/api'
const stats = ref<Record<string, number>>({})
const error = ref('')
onMounted(async () => {
  try { stats.value = (await api.get('/admin/dashboard')).data.data }
  catch (event) { error.value = (event as Error).message }
})
const metrics = [
  ['userCount', '用户数'], ['cultureCount', '文化条目'], ['creationCount', 'AI 作品'],
  ['postCount', '社区帖子'], ['completedTaskCount', '完成任务'],
]
</script>
<template>
  <h1 class="page-title">数据看板</h1>
  <el-alert v-if="error" :title="error" type="error" />
  <div class="metric-grid">
    <div v-for="[key, label] in metrics" :key="key" class="metric">
      <span>{{ label }}</span><strong>{{ stats[key] ?? '—' }}</strong>
    </div>
  </div>
</template>

