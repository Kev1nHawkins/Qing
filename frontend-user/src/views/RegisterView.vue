<script setup lang="ts">
import { computed, onUnmounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const form = reactive({ username: '', nickname: '', email: '', phone: '', phoneCode: '', password: '', confirmPassword: '', agreed: false })
const submitting = ref(false)
const sendingCode = ref(false)
const error = ref('')
const phoneChallengeId = ref('')
const debugCode = ref('')
const countdown = ref(0)
let countdownTimer: number | undefined

const passwordHint = computed(() => {
  if (!form.password) return '至少8位，建议同时包含字母和数字'
  if (form.password.length < 8) return '密码长度不足8位'
  return '密码长度符合要求'
})

function beginCountdown(seconds = 60) {
  countdown.value = seconds
  window.clearInterval(countdownTimer)
  countdownTimer = window.setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) window.clearInterval(countdownTimer)
  }, 1000)
}

async function sendPhoneCode() {
  error.value = ''
  const phone = form.phone.trim()
  if (!/^1[3-9]\d{9}$/.test(phone)) {
    error.value = '请输入正确的中国大陆手机号'
    return
  }
  sendingCode.value = true
  try {
    const { data } = await api.post('/auth/register/phone-code', { phone })
    phoneChallengeId.value = data.data.challengeId
    debugCode.value = data.data.debugCode || ''
    beginCountdown(data.data.retryAfter || 60)
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    sendingCode.value = false
  }
}

async function submit() {
  error.value = ''
  const username = form.username.trim()
  const nickname = form.nickname.trim()
  const email = form.email.trim()
  const phone = form.phone.trim()
  if (!/^[a-zA-Z0-9_-]{3,64}$/.test(username)) { error.value = '用户名需为3—64位字母、数字、下划线或短横线'; return }
  if (!nickname) { error.value = '请填写展示昵称'; return }
  if (phone && !/^1[3-9]\d{9}$/.test(phone)) { error.value = '请输入正确的中国大陆手机号'; return }
  if (phone && (!phoneChallengeId.value || !/^\d{6}$/.test(form.phoneCode))) { error.value = '请先获取并填写六位手机验证码'; return }
  if (form.password.length < 8 || form.password.length > 72) { error.value = '密码长度必须为8—72位'; return }
  if (form.password !== form.confirmPassword) { error.value = '两次输入的密码不一致'; return }
  if (!form.agreed) { error.value = '请先阅读并同意平台使用说明'; return }
  submitting.value = true
  try {
    await auth.register({ username, nickname, email: email || undefined, password: form.password, phone: phone || undefined, phoneChallengeId: phone ? phoneChallengeId.value : undefined, phoneCode: phone ? form.phoneCode : undefined })
    const requested = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    const redirect = requested.startsWith('/') && !requested.startsWith('//') ? requested : '/'
    await router.push(redirect)
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    submitting.value = false
  }
}

onUnmounted(() => window.clearInterval(countdownTimer))
</script>

<template>
  <section class="register-page">
    <aside><p>LINGCHAO IDENTITY</p><h1>加入岭潮，领取你的文化身份。</h1><span>注册岭潮账号，保存你的寻迹进度，收集积分徽章，还能分享 AI 共创作品。</span><ol><li><b>01</b>认识岭南文化 🌺</li><li><b>02</b>探索校园地标 📍</li><li><b>03</b>创作并分享 ✨</li></ol></aside>
    <form @submit.prevent="submit">
      <header><small>CREATE ACCOUNT</small><h2>注册岭潮账号</h2><p>已有账号？<RouterLink to="/login">返回登录</RouterLink></p></header>
      <div class="register-grid"><label><span>用户名</span><input v-model="form.username" maxlength="64" autocomplete="username" placeholder="字母、数字、_ 或 -" required /></label><label><span>展示昵称</span><input v-model="form.nickname" maxlength="64" autocomplete="nickname" placeholder="路线与社区中展示" required /></label></div>
      <label><span>邮箱（选填）</span><input v-model="form.email" type="email" maxlength="255" autocomplete="email" placeholder="用于区分账号，不会公开展示" /></label>
      <label><span>手机号（选填）</span><div class="phone-row"><input v-model="form.phone" inputmode="numeric" maxlength="11" autocomplete="tel" placeholder="绑定后可自助找回密码" /><button type="button" :disabled="sendingCode || countdown > 0" @click="sendPhoneCode">{{ countdown > 0 ? `${countdown} 秒` : sendingCode ? '发送中…' : '获取验证码' }}</button></div><small>不填写仍可注册，但将无法通过手机号自助找回密码。</small></label>
      <label v-if="phoneChallengeId"><span>手机验证码</span><input v-model="form.phoneCode" inputmode="numeric" maxlength="6" autocomplete="one-time-code" placeholder="六位验证码" /><small v-if="debugCode" class="debug-code">本地演示验证码：{{ debugCode }}</small></label>
      <label><span>密码</span><input v-model="form.password" type="password" maxlength="72" autocomplete="new-password" placeholder="设置登录密码" required /><small>{{ passwordHint }}</small></label>
      <label><span>确认密码</span><input v-model="form.confirmPassword" type="password" maxlength="72" autocomplete="new-password" placeholder="再次输入密码" required /></label>
      <label class="register-agreement"><input v-model="form.agreed" type="checkbox" /><span>我已阅读并同意平台使用说明，并遵守校园文化内容发布规范。</span></label>
      <p v-if="error" class="register-error" role="alert">{{ error }}</p><button type="submit" :disabled="submitting">{{ submitting ? '正在创建账号…' : '注册并进入岭潮' }}</button>
    </form>
  </section>
</template>

<style scoped>
.register-page{display:grid;grid-template-columns:.9fr 1.1fr;min-height:670px;overflow:hidden;border:1px solid #e1d7c9;border-radius:22px;background:#fff;box-shadow:0 24px 70px rgba(80,48,34,.12)}.register-page>aside{padding:52px;color:#fff;background:linear-gradient(145deg,#84212a,#b84037 58%,#d58b43)}.register-page>aside>p{margin:0;color:#f0ca82;font-size:10px;font-weight:900;letter-spacing:.18em}.register-page h1{margin:22px 0;font-size:48px;line-height:1.08}.register-page>aside>span{color:#f4dfd1;line-height:1.8}.register-page ol{display:grid;gap:15px;margin:48px 0 0;padding:0;list-style:none}.register-page li{display:flex;align-items:center;gap:12px;padding:13px 0;border-top:1px solid rgba(255,255,255,.22)}.register-page li b{color:#f2cc82}.register-page>form{display:grid;align-content:center;gap:15px;padding:45px 52px}.register-page form header small{color:#a9282f;font-weight:900;letter-spacing:.15em}.register-page form h2{margin:5px 0;font-size:34px}.register-page form header p{margin:0;color:#746d66;font-size:12px}.register-page form header a{color:#a9282f;font-weight:800}.register-page form>label,.register-grid label{display:grid;gap:7px;color:#4e4944;font-size:12px;font-weight:700}.register-page input:not([type=checkbox]){box-sizing:border-box;width:100%;height:47px;padding:0 13px;border:1px solid #d9cec0;border-radius:9px;background:#fffdfa}.register-page label small{color:#837970;font-weight:400}.register-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.phone-row{display:grid;grid-template-columns:1fr 125px;gap:9px}.phone-row button{border:1px solid #d9cec0;border-radius:9px;color:#a9282f;background:#fff;font-weight:800}.phone-row button:disabled{opacity:.55}.register-page label .debug-code{padding:8px 10px;color:#285f4d;background:#edf7f1;border-radius:7px}.register-agreement{grid-template-columns:auto 1fr!important;align-items:start;gap:9px!important;color:#6f665e!important;font-weight:400!important;line-height:1.55}.register-agreement input{margin-top:3px}.register-error{margin:0;padding:11px 13px;color:#9d252d;background:#fff0ef;border-radius:8px;font-size:12px}.register-page form>button{min-height:49px;color:#fff;background:#a9282f;border:0;border-radius:9px;font-weight:900}.register-page form>button:disabled{opacity:.6}@media(max-width:820px){.register-page{grid-template-columns:1fr}.register-page>aside{padding:35px}.register-page h1{font-size:38px}.register-page ol{display:none}.register-page>form{padding:35px}}@media(max-width:520px){.register-grid,.phone-row{grid-template-columns:1fr}.register-page>form{padding:27px 22px}}
</style>
