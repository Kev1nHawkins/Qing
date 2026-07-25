<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()

const navigation = [
  { path: '/', label: '数据看板' },
  { path: '/cultures', label: '文化内容' },
  { path: '/routes', label: '路线任务' },
  { path: '/templates', label: 'AI 模板' },
  { path: '/posts', label: '社区审核' },
]

function logout() {
  localStorage.removeItem('adminAccessToken')
  window.location.assign('/login')
}
</script>
<template>
  <RouterView v-if="route.path === '/login'" />
  <el-container v-else class="layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">岭潮共创<small>ADMIN CONSOLE</small></div>
      <nav class="admin-nav" aria-label="管理后台导航">
        <a v-for="item in navigation" :key="item.path" :href="item.path" :class="{ active: route.path === item.path }">
          {{ item.label }}
        </a>
      </nav>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span>岭南文化与校园文化 AI 共创传播平台</span>
        <button type="button" @click="logout">退出登录</button>
      </el-header>
      <el-main><RouterView /></el-main>
    </el-container>
  </el-container>
</template>
