<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const form = reactive({ phone: '', code: '' })
const editingPhone = ref(false)
const sending = ref(false)
const saving = ref(false)
const challengeId = ref('')
const debugCode = ref('')
const countdown = ref(0)
const error = ref('')
const message = ref('')
let countdownTimer: number | undefined

const maskedPhone = computed(() => auth.user?.phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') || '')

function beginCountdown(seconds = 60) {
  countdown.value = seconds
  window.clearInterval(countdownTimer)
  countdownTimer = window.setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) window.clearInterval(countdownTimer)
  }, 1000)
}

async function sendCode() {
  error.value = ''; message.value = ''
  const phone = form.phone.trim()
  if (!/^1[3-9]\d{9}$/.test(phone)) { error.value = '请输入正确的中国大陆手机号'; return }
  sending.value = true
  try {
    const { data } = await api.post('/auth/me/phone-code', { phone })
    challengeId.value = data.data.challengeId
    debugCode.value = data.data.debugCode || ''
    beginCountdown(data.data.retryAfter || 60)
    message.value = '验证码已发送'
  } catch (event) { error.value = (event as Error).message }
  finally { sending.value = false }
}

async function savePhone() {
  error.value = ''; message.value = ''
  if (!challengeId.value || !/^\d{6}$/.test(form.code)) { error.value = '请先获取并填写六位验证码'; return }
  saving.value = true
  try {
    const { data } = await api.put('/auth/me/phone', { phone: form.phone.trim(), challengeId: challengeId.value, code: form.code })
    auth.updateUser(data.data)
    editingPhone.value = false
    form.phone = ''; form.code = ''; challengeId.value = ''; debugCode.value = ''
    message.value = '手机号已更新，可用于找回密码'
  } catch (event) { error.value = (event as Error).message }
  finally { saving.value = false }
}

onMounted(() => { if (auth.isLoggedIn) auth.fetchMe() })
onUnmounted(() => window.clearInterval(countdownTimer))
</script>

<template>
  <section class="profile-page">
    <header><small>MY LINGCHAO</small><h1>我的岭潮</h1><p>管理文化身份、积分和账号安全信息。</p></header>
    <div v-if="auth.user" class="profile-grid">
      <article class="identity-card"><span class="avatar">{{ auth.user.nickname.slice(0, 1) }}</span><div><h2>{{ auth.user.nickname }}</h2><p>@{{ auth.user.username }}</p></div><strong>{{ auth.user.points_total }}<small> 积分</small></strong></article>
      <article class="phone-card">
        <div class="card-heading"><div><small>ACCOUNT SECURITY</small><h2>手机号绑定</h2></div><button v-if="auth.user.phone && !editingPhone" type="button" @click="editingPhone = true">更换手机号</button></div>
        <div v-if="auth.user.phone && !editingPhone" class="bound-phone"><span>已绑定</span><strong>{{ maskedPhone }}</strong><p>该手机号可用于验证码找回密码。</p></div>
        <form v-else @submit.prevent="savePhone">
          <label><span>新手机号</span><div class="phone-row"><input v-model="form.phone" inputmode="numeric" maxlength="11" autocomplete="tel" placeholder="请输入11位手机号" required /><button type="button" :disabled="sending || countdown > 0" @click="sendCode">{{ countdown > 0 ? `${countdown} 秒` : sending ? '发送中…' : '获取验证码' }}</button></div></label>
          <label v-if="challengeId"><span>六位验证码</span><input v-model="form.code" inputmode="numeric" maxlength="6" autocomplete="one-time-code" placeholder="请输入验证码" required /><small v-if="debugCode">本地演示验证码：{{ debugCode }}</small></label>
          <div class="actions"><button type="submit" :disabled="saving">{{ saving ? '正在保存…' : '确认绑定' }}</button><button v-if="auth.user.phone" class="secondary" type="button" @click="editingPhone = false">取消</button></div>
        </form>
        <p v-if="error" class="feedback error" role="alert">{{ error }}</p><p v-if="message" class="feedback success">{{ message }}</p>
      </article>
    </div>
    <div v-else class="status">登录后查看任务进度、作品、积分与徽章。<RouterLink to="/login">去登录</RouterLink></div>
  </section>
</template>

<style scoped>
.profile-page{display:grid;gap:24px}.profile-page>header small,.card-heading small{color:#a9282f;font-size:10px;font-weight:900;letter-spacing:.16em}.profile-page>header h1{margin:6px 0;font-size:42px}.profile-page>header p{margin:0;color:#786f67}.profile-grid{display:grid;grid-template-columns:.75fr 1.25fr;gap:20px}.identity-card,.phone-card{padding:28px;border:1px solid #e2d8ca;border-radius:18px;background:#fff;box-shadow:0 14px 35px rgba(70,44,32,.07)}.identity-card{display:grid;grid-template-columns:auto 1fr;align-content:start;gap:12px 16px;background:linear-gradient(145deg,#163d33,#28594b);color:#fff}.avatar{display:grid;place-items:center;width:58px;height:58px;border-radius:50%;background:#d5a756;color:#fff;font-size:24px;font-weight:900}.identity-card h2{margin:4px 0}.identity-card p{margin:0;color:#cbdcd5}.identity-card>strong{grid-column:1/-1;margin-top:30px;padding-top:20px;border-top:1px solid rgba(255,255,255,.18);color:#f0ca82;font-size:32px}.identity-card strong small{font-size:13px}.card-heading{display:flex;align-items:start;justify-content:space-between;gap:15px}.card-heading h2{margin:5px 0 20px}.card-heading button,.phone-row button,.secondary{border:1px solid #dccfc0;color:#a9282f;background:#fff;border-radius:8px;font-weight:800}.bound-phone{padding:20px;border-radius:12px;background:#f7f3eb}.bound-phone span{display:block;color:#4b765f;font-size:12px}.bound-phone strong{display:block;margin:8px 0;font-size:24px}.bound-phone p{margin:0;color:#7d746c;font-size:13px}.phone-card form{display:grid;gap:15px}.phone-card label{display:grid;gap:7px;color:#514a44;font-size:12px;font-weight:700}.phone-card input{box-sizing:border-box;width:100%;height:45px;padding:0 12px;border:1px solid #d9cec0;border-radius:8px}.phone-row{display:grid;grid-template-columns:1fr 125px;gap:9px}.phone-card label small{padding:8px;color:#285f4d;background:#edf7f1;border-radius:6px}.actions{display:flex;gap:9px}.actions button{min-height:43px;padding:0 20px;border:0;border-radius:8px;color:#fff;background:#a9282f;font-weight:900}.actions .secondary{color:#756b63;background:#fff}.feedback{margin:14px 0 0;padding:10px 12px;border-radius:7px;font-size:12px}.feedback.error{color:#9d252d;background:#fff0ef}.feedback.success{color:#285f4d;background:#edf7f1}@media(max-width:760px){.profile-grid{grid-template-columns:1fr}.phone-row{grid-template-columns:1fr}.profile-page>header h1{font-size:34px}}
</style>
