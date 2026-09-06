<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '@/services/api'
const items = ref<any[]>([])
const loading = ref(true)
async function load() {
  loading.value = true
  try { items.value = (await api.get('/admin/cultures', { params: { pageSize: 100 } })).data.data.items }
  finally { loading.value = false }
}
onMounted(load)
</script>
<template>
  <div style="display:flex; justify-content:space-between; align-items:center">
    <h1 class="page-title">文化内容</h1><el-button type="primary">新增文化条目</el-button>
  </div>
  <el-table v-loading="loading" :data="items" stripe>
    <el-table-column prop="id" label="ID" width="70" />
    <el-table-column prop="title" label="标题" min-width="180" />
    <el-table-column prop="category" label="分类" width="120" />
    <el-table-column prop="source_title" label="来源" min-width="180" />
    <el-table-column prop="status" label="状态" width="110" />
    <el-table-column label="操作" width="150"><template #default><el-button link type="primary">编辑</el-button></template></el-table-column>
  </el-table>
</template>

