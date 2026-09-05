<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import PosterStudio from '@/components/PosterStudio.vue'
import { api } from '@/services/api'
import type { CreationTemplate, Culture, PageData } from '@/types'

const router = useRouter()
const templates = ref<CreationTemplate[]>([])
const cultures = ref<Culture[]>([])
const loading = ref(true)
const error = ref('')

async function loadCreationData() {
  loading.value = true
  error.value = ''
  try {
    const [templateResponse, cultureResponse] = await Promise.all([
      api.get<{ data: PageData<CreationTemplate> }>('/creations/templates', {
        params: { pageSize: 20 },
      }),
      api.get<{ data: PageData<Culture> }>('/cultures', {
        params: { pageSize: 100 },
      }),
    ])
    templates.value = templateResponse.data.data.items
    cultures.value = cultureResponse.data.data.items
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    loading.value = false
  }
}

function requestLogin() {
  router.push({ path: '/login', query: { redirect: '/creation' } })
}

onMounted(loadCreationData)
</script>

<template>
  <section class="creation-heading">
    <p>STEP 05 · AI CO-CREATION</p>
    <h1>岭南文化共创工作台</h1>
    <span>选好文化元素和校园地标，挑一款喜欢的风格，让 AI 帮你把灵感变成海报 🎨</span>
    <ol>
      <li><b>01</b>挑选文化元素 🌺</li>
      <li><b>02</b>生成你的海报 ✨</li>
      <li><b>03</b>分享给社区朋友 📣</li>
    </ol>
  </section>

  <section v-if="loading" class="creation-state">正在加载共创模板…</section>
  <section v-else-if="error" class="creation-state error">
    <b>创作工作台暂时休息一下</b>
    <p>{{ error }}</p>
    <button type="button" @click="loadCreationData">再试一次</button>
  </section>
  <section v-else-if="!templates.length" class="creation-state">
    创作功能正在准备中，稍后再来试试吧！
  </section>
  <PosterStudio
    v-else
    :template="templates[0]"
    :cultures="cultures"
    @login="requestLogin"
  />

  <aside class="creation-handoff">
    <div><small>STEP 06 · SHARE</small><b>作品完成啦？去社区和大家分享吧！</b></div>
    <RouterLink to="/community">前往共创社区 →</RouterLink>
  </aside>
</template>

<style scoped>
.creation-heading{margin-bottom:24px;padding:34px;color:#fff;background:linear-gradient(135deg,#7f2029,#b43b3d 58%,#d39546);border-radius:20px}.creation-heading>p{margin:0;color:#f5d494;font-size:11px;font-weight:900;letter-spacing:.18em}.creation-heading h1{margin:10px 0 14px;font-size:clamp(34px,6vw,62px)}.creation-heading>span{display:block;max-width:720px;line-height:1.8}.creation-heading ol{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0 0;padding:0;list-style:none}.creation-heading li{display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.22);border-radius:999px;font-size:12px}.creation-heading li b{color:#f5d494}.creation-state{padding:28px;background:#fff;border:1px solid #eaded0;border-radius:12px;text-align:center}.creation-state.error{color:#8e2730}.creation-state button{padding:9px 15px;border:0;border-radius:999px;color:#fff;background:#9f2832}.creation-handoff{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-top:20px;padding:22px 26px;color:#fff;background:#285a47;border-radius:12px}.creation-handoff div{display:grid;gap:5px}.creation-handoff small{color:#d9c17a;font-weight:900}.creation-handoff a{padding:11px 16px;color:#285a47;background:#fff;border-radius:999px;font-weight:800}@media(max-width:640px){.creation-heading{padding:26px 22px}.creation-handoff{align-items:flex-start;flex-direction:column}}
</style>
