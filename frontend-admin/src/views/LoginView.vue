<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/services/api'
import {
  consumeAdminAuthNotice,
  saveAdminSession,
} from '@/services/adminSession'
const form = reactive({ username: '', password: '' })
const error = ref('')
const notice = ref('')
const router = useRouter()
const route = useRoute()
async function submit() {
  error.value = ''
  try {
    const { data } = await api.post('/auth/login', form)
    if (data.data.user?.role?.code !== 'admin') {
      throw new Error('当前账号没有管理员权限')
    }
    saveAdminSession(data.data.access_token)
    const requested = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    const redirect = requested.startsWith('/') && !requested.startsWith('//') ? requested : '/'
    await router.push(redirect)
  } catch (event) { error.value = (event as Error).message }
}
onMounted(() => { notice.value = consumeAdminAuthNotice() })
</script>
<template>
  <div class="login-page">
    <el-form class="login-card" label-position="top" @submit.prevent="submit">
      <h1>管理后台</h1><p>使用管理员账号进入岭潮共创内容中台。</p>
      <el-alert v-if="notice" :title="notice" type="warning" :closable="false" style="margin-bottom:16px" />
      <el-form-item label="用户名"><el-input v-model="form.username" /></el-form-item>
      <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>
      <el-alert v-if="error" :title="error" type="error" :closable="false" />
      <el-button type="primary" native-type="submit" style="width:100%; margin-top:16px">登录</el-button>
    </el-form>
  </div>
</template>

