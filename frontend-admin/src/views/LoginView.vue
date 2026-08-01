<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/api'
const form = reactive({ username: '', password: '' })
const error = ref('')
const router = useRouter()
async function submit() {
  try {
    const { data } = await api.post('/auth/login', form)
    localStorage.setItem('adminAccessToken', data.data.access_token)
    await router.push('/')
  } catch (event) { error.value = (event as Error).message }
}
</script>
<template>
  <div class="login-page">
    <el-form class="login-card" label-position="top" @submit.prevent="submit">
      <h1>管理后台</h1><p>使用管理员账号进入岭潮共创内容中台。</p>
      <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
      <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
      <el-alert v-if="error" :title="error" type="error" :closable="false" />
      <el-button type="primary" native-type="submit" style="width:100%; margin-top:16px">登录</el-button>
    </el-form>
  </div>
</template>

