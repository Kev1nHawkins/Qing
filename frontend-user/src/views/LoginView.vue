<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
const username = ref('')
const password = ref('')
const error = ref('')
const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const resetSuccess = computed(() => route.query.reset === 'success')
async function submit() {
  try {
    await auth.login(username.value, password.value)
    const requested = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    const redirect = requested.startsWith('/') && !requested.startsWith('//') ? requested : '/'
    await router.push(redirect)
  }
  catch (event) { error.value = (event as Error).message }
}
</script>
<template>
  <h1>登录</h1>
  <form class="form" @submit.prevent="submit">
    <p v-if="resetSuccess" class="success-status">密码已重置，请重新登录。</p>
    <input v-model="username" placeholder="用户名" autocomplete="username" />
    <input v-model="password" type="password" placeholder="密码" autocomplete="current-password" />
    <button class="button" type="submit">登录</button>
    <p v-if="error" class="status">{{ error }}</p>
    <p class="auth-switch">还没有岭潮账号？<RouterLink to="/register">立即注册</RouterLink></p>
    <p class="recover-link"><RouterLink to="/forgot-password">忘记密码？找回密码</RouterLink></p>
  </form>
</template>

<style scoped>
.auth-switch{margin:2px 0;color:#756b63;font-size:13px}.auth-switch a,.recover-link a{color:#a9282f;font-weight:800}.recover-link{margin:0;font-size:13px}.success-status{margin:0;padding:11px 13px;color:#285f4d;background:#edf7f1;border-radius:8px;font-size:13px}
</style>

