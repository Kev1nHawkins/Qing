<script setup lang="ts">
import { computed, onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/api'

const router = useRouter()
const step = ref<1 | 2>(1)
const form = reactive({ phone: '', code: '', password: '', confirmPassword: '' })
const challengeId = ref('')
const debugCode = ref('')
const countdown = ref(0)
const sending = ref(false)
const submitting = ref(false)
const error = ref('')
let countdownTimer: number | undefined

const phoneValid = computed(() => /^1[3-9]\d{9}$/.test(form.phone.trim()))

function beginCountdown(seconds = 60) {
  countdown.value = seconds
  window.clearInterval(countdownTimer)
  countdownTimer = window.setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) window.clearInterval(countdownTimer)
  }, 1000)
}

async function sendCode() {
  error.value = ''
  if (!phoneValid.value) {
    error.value = '请输入正确的中国大陆手机号'
    return
  }
  sending.value = true
  try {
    const { data } = await api.post('/auth/password-reset/code', { phone: form.phone.trim() })
    challengeId.value = data.data.challengeId
    debugCode.value = data.data.debugCode || ''
    step.value = 2
    beginCountdown(data.data.retryAfter || 60)
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    sending.value = false
  }
}

async function resetPassword() {
  error.value = ''
  if (!/^\d{6}$/.test(form.code)) {
    error.value = '请输入六位数字验证码'
    return
  }
  if (form.password.length < 8 || form.password.length > 72) {
    error.value = '密码长度必须为8—72位'
    return
  }
  if (form.password !== form.confirmPassword) {
    error.value = '两次输入的新密码不一致'
    return
  }
  submitting.value = true
  try {
    await api.post('/auth/password-reset', {
      phone: form.phone.trim(),
      challengeId: challengeId.value,
      code: form.code,
      newPassword: form.password,
    })
    form.code = ''
    form.password = ''
    form.confirmPassword = ''
    await router.replace({ path: '/login', query: { reset: 'success' } })
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    submitting.value = false
  }
}

onUnmounted(() => window.clearInterval(countdownTimer))
</script>

<template>
  <section class="recovery-page">
    <aside>
      <p>LINGCHAO ACCOUNT</p>
      <h1>找回你的岭潮账号。</h1>
      <span>通过已绑定手机号验证身份，设置新的登录密码。</span>
      <ol>
        <li :class="{ active: step === 1 }"><b>01</b>验证手机号</li>
        <li :class="{ active: step === 2 }"><b>02</b>重置密码</li>
        <li><b>03</b>重新登录</li>
      </ol>
    </aside>
    <form v-if="step === 1" @submit.prevent="sendCode">
      <header><small>PASSWORD RECOVERY</small><h2>找回密码</h2><p>想起密码了？<RouterLink to="/login">返回登录</RouterLink></p></header>
      <label><span>已绑定手机号</span><input v-model="form.phone" inputmode="numeric" maxlength="11" autocomplete="tel" placeholder="请输入11位手机号" required /></label>
      <p class="hint">只有已在注册或个人中心绑定的手机号可用于找回密码。</p>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <button type="submit" :disabled="sending">{{ sending ? '正在发送…' : '获取验证码' }}</button>
    </form>
    <form v-else @submit.prevent="resetPassword">
      <header><small>VERIFY & RESET</small><h2>设置新密码</h2><p>验证码已发送至 {{ form.phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') }}</p></header>
      <label><span>六位验证码</span><div class="code-row"><input v-model="form.code" inputmode="numeric" maxlength="6" autocomplete="one-time-code" placeholder="请输入验证码" required /><button type="button" :disabled="sending || countdown > 0" @click="sendCode">{{ countdown > 0 ? `${countdown} 秒后重发` : '重新发送' }}</button></div></label>
      <p v-if="debugCode" class="debug-code">本地演示验证码：<strong>{{ debugCode }}</strong></p>
      <label><span>新密码</span><input v-model="form.password" type="password" maxlength="72" autocomplete="new-password" placeholder="8—72位" required /></label>
      <label><span>确认新密码</span><input v-model="form.confirmPassword" type="password" maxlength="72" autocomplete="new-password" placeholder="再次输入新密码" required /></label>
      <p v-if="error" class="form-error" role="alert">{{ error }}</p>
      <button type="submit" :disabled="submitting">{{ submitting ? '正在重置…' : '确认重置密码' }}</button>
      <button class="secondary" type="button" @click="step = 1; error = ''">更换手机号</button>
    </form>
  </section>
</template>

<style scoped>
.recovery-page{display:grid;grid-template-columns:.9fr 1.1fr;min-height:620px;overflow:hidden;border:1px solid #e1d7c9;border-radius:22px;background:#fff;box-shadow:0 24px 70px rgba(80,48,34,.12)}.recovery-page>aside{padding:52px;color:#fff;background:linear-gradient(145deg,#183f35,#8d292e 62%,#d29a4f)}.recovery-page>aside>p{margin:0;color:#f0ca82;font-size:10px;font-weight:900;letter-spacing:.18em}.recovery-page h1{margin:22px 0;font-size:48px;line-height:1.08}.recovery-page>aside>span{color:#f4dfd1;line-height:1.8}.recovery-page ol{display:grid;gap:15px;margin:48px 0 0;padding:0;list-style:none}.recovery-page li{display:flex;align-items:center;gap:12px;padding:13px 0;border-top:1px solid rgba(255,255,255,.22);opacity:.62}.recovery-page li.active{opacity:1}.recovery-page li b{color:#f2cc82}.recovery-page>form{display:grid;align-content:center;gap:16px;padding:45px 52px}.recovery-page header small{color:#a9282f;font-weight:900;letter-spacing:.15em}.recovery-page h2{margin:5px 0;font-size:34px}.recovery-page header p,.hint{margin:0;color:#746d66;font-size:12px}.recovery-page header a{color:#a9282f;font-weight:800}.recovery-page label{display:grid;gap:7px;color:#4e4944;font-size:12px;font-weight:700}.recovery-page input{box-sizing:border-box;width:100%;height:47px;padding:0 13px;border:1px solid #d9cec0;border-radius:9px;background:#fffdfa}.recovery-page form>button{min-height:49px;color:#fff;background:#a9282f;border:0;border-radius:9px;font-weight:900}.recovery-page button:disabled{opacity:.55}.code-row{display:grid;grid-template-columns:1fr 132px;gap:9px}.code-row button,.secondary{border:1px solid #d9cec0!important;color:#8d292e!important;background:#fff!important;border-radius:9px;font-weight:800}.form-error,.debug-code{margin:0;padding:11px 13px;border-radius:8px;font-size:12px}.form-error{color:#9d252d;background:#fff0ef}.debug-code{color:#285f4d;background:#edf7f1}.secondary{min-height:43px!important}@media(max-width:820px){.recovery-page{grid-template-columns:1fr}.recovery-page>aside{padding:35px}.recovery-page h1{font-size:38px}.recovery-page ol{display:none}.recovery-page>form{padding:35px}}@media(max-width:520px){.recovery-page>form{padding:27px 22px}.code-row{grid-template-columns:1fr}}
</style>
