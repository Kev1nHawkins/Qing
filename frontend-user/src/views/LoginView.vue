<script setup lang="ts">
import { onBeforeUnmount, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const mode = ref<'PASSWORD' | 'SMS'>('PASSWORD')
const form = reactive({ username: '', password: '', phone: '', verificationCode: '' })
const error = ref('')
const sending = ref(false)
const submitting = ref(false)
const demoCode = ref('')
const resendCountdown = ref(0)
const codeExpiresIn = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | undefined

function startCountdown(seconds: number) {
  resendCountdown.value = Math.max(1, seconds)
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = setInterval(() => {
    resendCountdown.value -= 1
    if (resendCountdown.value <= 0 && countdownTimer) {
      clearInterval(countdownTimer)
      countdownTimer = undefined
    }
  }, 1000)
}

onBeforeUnmount(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})

function validPhone() {
  return /^1[3-9]\d{9}$/.test(form.phone.trim())
}

async function sendCode() {
  error.value = ''
  demoCode.value = ''
  if (!validPhone()) {
    error.value = '请输入正确的11位手机号'
    return
  }
  sending.value = true
  try {
    const response = await api.post('/auth/sms/send', { phone: form.phone.trim(), purpose: 'LOGIN' })
    demoCode.value = response.data.data.demoCode || ''
    codeExpiresIn.value = response.data.data.expiresIn || 300
    startCountdown(response.data.data.retryAfter || 60)
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    sending.value = false
  }
}

async function submit() {
  error.value = ''
  submitting.value = true
  try {
    if (mode.value === 'PASSWORD') {
      await auth.login(form.username.trim(), form.password)
    } else {
      if (!validPhone()) throw new Error('请输入正确的11位手机号')
      await auth.loginWithSms(form.phone.trim(), form.verificationCode.trim())
    }
    const requested = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    const redirect = requested.startsWith('/') && !requested.startsWith('//') ? requested : '/'
    await router.push(redirect)
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="login-page">
    <aside>
      <p>LINGCHAO ACCOUNT</p>
      <h1>欢迎回来，继续你的文化旅程。</h1>
      <span>使用原有账号密码，或通过已绑定手机号快速进入岭潮。</span>
      <ol><li><b>01</b>探索岭南文化</li><li><b>02</b>继续校园寻迹</li><li><b>03</b>发布共创作品</li></ol>
    </aside>
    <form @submit.prevent="submit">
      <header><small>WELCOME BACK</small><h2>登录岭潮</h2><p>还没有账号？<RouterLink to="/register">立即注册</RouterLink></p></header>
      <div class="login-tabs" aria-label="登录方式">
        <button type="button" :class="{ active: mode === 'PASSWORD' }" @click="mode = 'PASSWORD'; error = ''">账号密码</button>
        <button type="button" :class="{ active: mode === 'SMS' }" @click="mode = 'SMS'; error = ''">手机验证码</button>
      </div>
      <template v-if="mode === 'PASSWORD'">
        <label><span>用户名</span><input v-model="form.username" autocomplete="username" placeholder="请输入用户名" required /></label>
        <label><span>密码</span><input v-model="form.password" type="password" autocomplete="current-password" placeholder="请输入密码" required /></label>
        <RouterLink class="forgot-link" to="/forgot-password">忘记密码？</RouterLink>
      </template>
      <template v-else>
        <label><span>手机号</span><input v-model="form.phone" inputmode="numeric" maxlength="11" autocomplete="tel" placeholder="请输入11位手机号" required /></label>
        <label><span>验证码</span><div class="code-row"><input v-model="form.verificationCode" inputmode="numeric" maxlength="6" placeholder="6位验证码" required /><button type="button" :disabled="sending || resendCountdown > 0" @click="sendCode">{{ sending ? '生成中…' : resendCountdown > 0 ? `${resendCountdown}s后重试` : '获取验证码' }}</button></div></label>
        <p v-if="demoCode" class="demo-code">比赛演示验证码：<b>{{ demoCode }}</b>（{{ Math.ceil(codeExpiresIn / 60) }}分钟内有效）</p>
      </template>
      <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
      <button class="submit-button" type="submit" :disabled="submitting">{{ submitting ? '正在登录…' : '进入岭潮' }}</button>
    </form>
  </section>
</template>

<style scoped>
.login-page{display:grid;grid-template-columns:.9fr 1.1fr;min-height:650px;overflow:hidden;border:1px solid #e1d7c9;border-radius:22px;background:#fff;box-shadow:0 24px 70px rgba(80,48,34,.12)}.login-page>aside{padding:52px;color:#fff;background:linear-gradient(145deg,#173d31,#84212a 55%,#d58b43)}.login-page>aside>p{margin:0;color:#f0ca82;font-size:10px;font-weight:900;letter-spacing:.18em}.login-page h1{margin:22px 0;font-size:46px;line-height:1.08}.login-page>aside>span{color:#f4dfd1;line-height:1.8}.login-page ol{display:grid;gap:15px;margin:48px 0 0;padding:0;list-style:none}.login-page li{display:flex;gap:12px;padding:13px 0;border-top:1px solid rgba(255,255,255,.22)}.login-page li b{color:#f2cc82}.login-page>form{display:grid;align-content:center;gap:16px;padding:45px 52px}.login-page header small{color:#a9282f;font-weight:900;letter-spacing:.15em}.login-page h2{margin:5px 0;font-size:34px}.login-page header p{margin:0;color:#746d66;font-size:12px}.login-page a{color:#a9282f;font-weight:800}.login-page label{display:grid;gap:7px;color:#4e4944;font-size:12px;font-weight:700}.login-page input{width:100%;height:47px;padding:0 13px;border:1px solid #d9cec0;border-radius:9px;background:#fffdfa}.login-tabs{display:grid;grid-template-columns:1fr 1fr;gap:8px}.login-tabs button{min-height:40px;border:1px solid #d9cec0;border-radius:999px;color:#756b63;background:#fff}.login-tabs button.active{color:#fff;background:#a9282f;border-color:#a9282f}.code-row{display:grid;grid-template-columns:1fr 118px;gap:8px}.code-row button{border:0;border-radius:9px;color:#fff;background:#285a47;font-size:12px;font-weight:800}.code-row button:disabled,.submit-button:disabled{opacity:.6}.forgot-link{justify-self:end;font-size:12px}.demo-code,.auth-error{margin:0;padding:11px 13px;border-radius:8px;font-size:12px}.demo-code{color:#285a47;background:#edf6f1}.auth-error{color:#9d252d;background:#fff0ef}.submit-button{min-height:49px;border:0;border-radius:9px;color:#fff;background:#a9282f;font-weight:900}
@media(max-width:820px){.login-page{grid-template-columns:1fr}.login-page>aside{padding:35px}.login-page h1{font-size:38px}.login-page ol{display:none}.login-page>form{padding:35px}}@media(max-width:520px){.login-page>form{padding:27px 22px}.code-row{grid-template-columns:1fr 105px}}
</style>
