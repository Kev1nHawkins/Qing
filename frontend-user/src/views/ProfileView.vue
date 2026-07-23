<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
onMounted(() => { if (auth.isLoggedIn) auth.fetchMe() })
</script>
<template>
  <h1>我的岭潮</h1>
  <div v-if="auth.user" class="card">
    <h3>{{ auth.user.nickname }}</h3><p class="muted">@{{ auth.user.username }}</p>
    <strong>{{ auth.user.points_total }} 积分</strong>
  </div>
  <div v-else class="status">登录后查看任务进度、作品、积分与徽章。<RouterLink to="/login">去登录</RouterLink></div>
</template>

