<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/api'

const router = useRouter()
const form = reactive({ phone: '', verificationCode: '', password: '', confirmPassword: '' })
const codeSent = ref(false)
const demoCode = ref('')
const sending = ref(false)
const submitting = ref(false)
const error = ref('')
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
const passwordReady = computed(() => form.password.length >= 8 && form.password === form.confirmPassword)

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
    const response = await api.post('/auth/sms/send', { phone: form.phone.trim(), purpose: 'RESET' })
    demoCode.value = response.data.data.demoCode || ''
    codeExpiresIn.value = response.data.data.expiresIn || 300
    startCountdown(response.data.data.retryAfter || 60)
    codeSent.value = true
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    sending.value = false
  }
}

async function resetPassword() {
  error.value = ''
  if (!passwordReady.value) {
    error.value = '密码至少8位，且两次输入必须一致'
    return
  }
  submitting.value = true
  try {
    await api.post('/auth/password/reset', {
      phone: form.phone.trim(),
      verification_code: form.verificationCode.trim(),
      new_password: form.password,
    })
    await router.push('/login')
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <section class="recovery-page">
    <aside>
      <p>LINGCHAO ACCOUNT</p>
      <h1>找回你的岭潮账号。</h1>
      <span>通过注册时绑定的手机号验证身份，设置新的登录密码。</span>
      <ol><li><b>01</b>验证手机号</li><li><b>02</b>重置密码</li><li><b>03</b>重新登录</li></ol>
    </aside>
    <form @submit.prevent="resetPassword">
      <header><small>PASSWORD RECOVERY</small><h2>找回密码</h2><p>想起密码了？<RouterLink to="/login">返回登录</RouterLink></p></header>
      <label><span>已绑定手机号</span><input v-model="form.phone" inputmode="numeric" maxlength="11" autocomplete="tel" placeholder="请输入11位手机号" :disabled="codeSent" required /></label>
      <button v-if="!codeSent" class="primary" type="button" :disabled="sending" @click="sendCode">{{ sending ? '正在生成…' : '获取验证码' }}</button>
      <template v-else>
        <p v-if="demoCode" class="demo-code">比赛演示验证码：<b>{{ demoCode }}</b>（{{ Math.ceil(codeExpiresIn / 60) }}分钟内有效）</p>
        <label><span>验证码</span><input v-model="form.verificationCode" inputmode="numeric" maxlength="6" placeholder="请输入6位验证码" required /></label>
        <button class="secondary" type="button" :disabled="sending || resendCountdown > 0" @click="sendCode">{{ sending ? '正在生成…' : resendCountdown > 0 ? `${resendCountdown}s后可重新获取` : '重新获取验证码' }}</button>
        <label><span>新密码</span><input v-model="form.password" type="password" maxlength="72" autocomplete="new-password" placeholder="至少8位" required /></label>
        <label><span>确认新密码</span><input v-model="form.confirmPassword" type="password" maxlength="72" autocomplete="new-password" placeholder="再次输入新密码" required /></label>
        <button class="primary" type="submit" :disabled="submitting">{{ submitting ? '正在重置…' : '重置密码' }}</button>
      </template>
      <p v-if="error" class="auth-error" role="alert">{{ error }}</p>
    </form>
  </section>
</template>

<style scoped>
.recovery-page{display:grid;grid-template-columns:.9fr 1.1fr;min-height:650px;overflow:hidden;border:1px solid #e1d7c9;border-radius:22px;background:#fff;box-shadow:0 24px 70px rgba(80,48,34,.12)}.recovery-page>aside{padding:52px;color:#fff;background:linear-gradient(145deg,#173d31,#84212a 55%,#d58b43)}.recovery-page>aside>p{margin:0;color:#f0ca82;font-size:10px;font-weight:900;letter-spacing:.18em}.recovery-page h1{margin:22px 0;font-size:48px;line-height:1.08}.recovery-page>aside>span{color:#f4dfd1;line-height:1.8}.recovery-page ol{display:grid;gap:15px;margin:48px 0 0;padding:0;list-style:none}.recovery-page li{display:flex;gap:12px;padding:13px 0;border-top:1px solid rgba(255,255,255,.22)}.recovery-page li b{color:#f2cc82}.recovery-page>form{display:grid;align-content:center;gap:16px;padding:45px 52px}.recovery-page header small{color:#a9282f;font-weight:900;letter-spacing:.15em}.recovery-page h2{margin:5px 0;font-size:34px}.recovery-page header p{margin:0;color:#746d66;font-size:12px}.recovery-page a{color:#a9282f;font-weight:800}.recovery-page label{display:grid;gap:7px;color:#4e4944;font-size:12px;font-weight:700}.recovery-page input{height:47px;padding:0 13px;border:1px solid #d9cec0;border-radius:9px;background:#fffdfa}.primary{min-height:49px;border:0;border-radius:9px;color:#fff;background:#a9282f;font-weight:900}.primary:disabled{opacity:.6}.demo-code,.auth-error{margin:0;padding:11px 13px;border-radius:8px;font-size:12px}.demo-code{color:#285a47;background:#edf6f1}.auth-error{color:#9d252d;background:#fff0ef}
.secondary{justify-self:end;border:0;color:#285a47;background:transparent;font-size:12px;font-weight:800}.secondary:disabled{color:#8b8178}
@media(max-width:820px){.recovery-page{grid-template-columns:1fr}.recovery-page>aside{padding:35px}.recovery-page h1{font-size:38px}.recovery-page ol{display:none}.recovery-page>form{padding:35px}}@media(max-width:520px){.recovery-page>form{padding:27px 22px}}
</style>
