<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
const username = ref('admin')
const password = ref('Admin123!')
const error = ref('')
const auth = useAuthStore()
const router = useRouter()
async function submit() {
  try { await auth.login(username.value, password.value); await router.push('/profile') }
  catch (event) { error.value = (event as Error).message }
}
</script>
<template>
  <h1>登录</h1>
  <form class="form" @submit.prevent="submit">
    <input v-model="username" placeholder="用户名" autocomplete="username" />
    <input v-model="password" type="password" placeholder="密码" autocomplete="current-password" />
    <button class="button" type="submit">登录</button>
    <p v-if="error" class="status">{{ error }}</p>
  </form>
</template>

