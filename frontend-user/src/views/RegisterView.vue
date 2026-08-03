<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const form = reactive({
  username: '',
  nickname: '',
  email: '',
  password: '',
  confirmPassword: '',
  agreed: false,
})
const submitting = ref(false)
const error = ref('')

const passwordHint = computed(() => {
  if (!form.password) return '至少8位，建议同时包含字母和数字'
  if (form.password.length < 8) return '密码长度不足8位'
  return '密码长度符合要求'
})

async function submit() {
  error.value = ''
  const username = form.username.trim()
  const nickname = form.nickname.trim()
  const email = form.email.trim()
  if (!/^[a-zA-Z0-9_-]{3,64}$/.test(username)) {
    error.value = '用户名需为3—64位字母、数字、下划线或短横线'
    return
  }
  if (!nickname) {
    error.value = '请填写展示昵称'
    return
  }
  if (form.password.length < 8 || form.password.length > 72) {
    error.value = '密码长度必须为8—72位'
    return
  }
  if (form.password !== form.confirmPassword) {
    error.value = '两次输入的密码不一致'
    return
  }
  if (!form.agreed) {
    error.value = '请先确认演示平台使用说明'
    return
  }
  submitting.value = true
  try {
    await auth.register({
      username,
      nickname,
      email: email || undefined,
      password: form.password,
    })
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
  <section class="register-page">
    <aside>
      <p>LINGCHAO IDENTITY</p>
      <h1>加入岭潮，领取你的文化身份。</h1>
      <span>注册后即可保存校园寻迹进度、获得文化积分与令牌，并把AI共创作品发布到社区。</span>
      <ol>
        <li><b>01</b>文化探索与知识问答</li>
        <li><b>02</b>校园打卡与文化令牌</li>
        <li><b>03</b>AI共创与社区传播</li>
      </ol>
    </aside>
    <form @submit.prevent="submit">
      <header><small>CREATE ACCOUNT</small><h2>注册岭潮账号</h2><p>已有账号？<RouterLink to="/login">返回登录</RouterLink></p></header>
      <div class="register-grid">
        <label>
          <span>用户名</span>
          <input v-model="form.username" maxlength="64" autocomplete="username" placeholder="字母、数字、_ 或 -" required />
        </label>
        <label>
          <span>展示昵称</span>
          <input v-model="form.nickname" maxlength="64" autocomplete="nickname" placeholder="路线与社区中展示" required />
        </label>
      </div>
      <label>
        <span>邮箱（选填）</span>
        <input v-model="form.email" type="email" maxlength="255" autocomplete="email" placeholder="用于区分账号，不会公开展示" />
      </label>
      <label>
        <span>密码</span>
        <input v-model="form.password" type="password" maxlength="72" autocomplete="new-password" placeholder="设置登录密码" required />
        <small>{{ passwordHint }}</small>
      </label>
      <label>
        <span>确认密码</span>
        <input v-model="form.confirmPassword" type="password" maxlength="72" autocomplete="new-password" placeholder="再次输入密码" required />
      </label>
      <label class="register-agreement">
        <input v-model="form.agreed" type="checkbox" />
        <span>我确认仅将账号用于本比赛演示平台，并遵守校园文化内容发布规范。</span>
      </label>
      <p v-if="error" class="register-error" role="alert">{{ error }}</p>
      <button type="submit" :disabled="submitting">{{ submitting ? '正在创建账号…' : '注册并进入岭潮' }}</button>
    </form>
  </section>
</template>

<style scoped>
.register-page{display:grid;grid-template-columns:.9fr 1.1fr;min-height:670px;overflow:hidden;border:1px solid #e1d7c9;border-radius:22px;background:#fff;box-shadow:0 24px 70px rgba(80,48,34,.12)}.register-page>aside{padding:52px;color:#fff;background:linear-gradient(145deg,#84212a,#b84037 58%,#d58b43)}.register-page>aside>p{margin:0;color:#f0ca82;font-size:10px;font-weight:900;letter-spacing:.18em}.register-page h1{margin:22px 0;font-size:48px;line-height:1.08}.register-page>aside>span{color:#f4dfd1;line-height:1.8}.register-page ol{display:grid;gap:15px;margin:48px 0 0;padding:0;list-style:none}.register-page li{display:flex;align-items:center;gap:12px;padding:13px 0;border-top:1px solid rgba(255,255,255,.22)}.register-page li b{color:#f2cc82}.register-page>form{display:grid;align-content:center;gap:15px;padding:45px 52px}.register-page form header small{color:#a9282f;font-weight:900;letter-spacing:.15em}.register-page form h2{margin:5px 0;font-size:34px}.register-page form header p{margin:0;color:#746d66;font-size:12px}.register-page form header a{color:#a9282f;font-weight:800}.register-page form>label,.register-grid label{display:grid;gap:7px;color:#4e4944;font-size:12px;font-weight:700}.register-page input:not([type=checkbox]){height:47px;padding:0 13px;border:1px solid #d9cec0;border-radius:9px;background:#fffdfa}.register-page label small{color:#837970;font-weight:400}.register-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.register-agreement{grid-template-columns:auto 1fr!important;align-items:start;gap:9px!important;color:#6f665e!important;font-weight:400!important;line-height:1.55}.register-agreement input{margin-top:3px}.register-error{margin:0;padding:11px 13px;color:#9d252d;background:#fff0ef;border-radius:8px;font-size:12px}.register-page form>button{min-height:49px;color:#fff;background:#a9282f;border:0;border-radius:9px;font-weight:900}.register-page form>button:disabled{opacity:.6}
@media(max-width:820px){.register-page{grid-template-columns:1fr}.register-page>aside{padding:35px}.register-page h1{font-size:38px}.register-page ol{display:none}.register-page>form{padding:35px}}@media(max-width:520px){.register-grid{grid-template-columns:1fr}.register-page>form{padding:27px 22px}}
</style>
