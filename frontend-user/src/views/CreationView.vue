<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import CreativeWorkbench, { type WorkbenchMode } from '@/components/CreativeWorkbench.vue'
import { api } from '@/services/api'
import type { CreationTemplate, PageData } from '@/types'

const router = useRouter()
const route = useRoute()
const templates = ref<CreationTemplate[]>([])
const loading = ref(true)
const error = ref('')
const requestedTemplateCode = computed(() =>
  typeof route.query.template === 'string' ? route.query.template : undefined,
)
const requestedMode = computed<WorkbenchMode>(() => {
  const value = route.query.mode
  return value === 'free-image' || value === 'post' || value === 'template' ? value : 'template'
})

async function loadCreationData() {
  loading.value = true
  error.value = ''
  try {
    const templateResponse = await api.get<{ data: PageData<CreationTemplate> }>(
      '/creations/templates',
      { params: { pageSize: 20 } },
    )
    templates.value = templateResponse.data.data.items
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    loading.value = false
  }
}

function requestLogin() {
  router.push({ path: '/login', query: { redirect: route.fullPath } })
}

function syncTemplateCode(code: string) {
  if (route.query.template === code) return
  router.replace({ query: { ...route.query, template: code } })
}

function syncMode(mode: WorkbenchMode) {
  if (route.query.mode === mode) return
  router.replace({ query: { ...route.query, mode } })
}

onMounted(() => {
  syncMode(requestedMode.value)
  loadCreationData()
})
</script>

<template>
  <section class="creation-heading">
    <p>STEP 05 · AI CO-CREATION</p>
    <h1>岭南文化共创工作台</h1>
    <span>选择模板、自由生成图片，或让 AI 帮你整理一篇可编辑的社区推文。</span>
    <ol>
      <li><b>01</b>选择创作模块 🌺</li>
      <li><b>02</b>写下你的灵感 ✨</li>
      <li><b>03</b>编辑并分享作品 📣</li>
    </ol>
  </section>

  <CreativeWorkbench
    :templates="templates"
    :template-loading="loading"
    :template-error="error"
    :initial-mode="requestedMode"
    :initial-template-code="requestedTemplateCode"
    @login="requestLogin"
    @mode-change="syncMode"
    @template-change="syncTemplateCode"
    @retry-templates="loadCreationData"
  />

  <aside class="creation-handoff">
    <div><small>STEP 06 · SHARE</small><b>作品完成啦？去社区和大家分享吧！</b></div>
    <RouterLink to="/community">前往共创社区 →</RouterLink>
  </aside>
</template>

<style scoped>
.creation-heading{margin-bottom:24px;padding:34px;color:#fff;background:linear-gradient(135deg,#7f2029,#b43b3d 58%,#d39546);border-radius:20px}.creation-heading>p{margin:0;color:#f5d494;font-size:11px;font-weight:900;letter-spacing:.18em}.creation-heading h1{margin:10px 0 14px;font-size:clamp(34px,6vw,62px)}.creation-heading>span{display:block;max-width:720px;line-height:1.8}.creation-heading ol{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0 0;padding:0;list-style:none}.creation-heading li{display:flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.22);border-radius:999px;font-size:12px}.creation-heading li b{color:#f5d494}.creation-state{padding:28px;background:#fff;border:1px solid #eaded0;border-radius:12px;text-align:center}.creation-state.error{color:#8e2730}.creation-state button{padding:9px 15px;border:0;border-radius:999px;color:#fff;background:#9f2832}.creation-handoff{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-top:20px;padding:22px 26px;color:#fff;background:#285a47;border-radius:12px}.creation-handoff div{display:grid;gap:5px}.creation-handoff small{color:#d9c17a;font-weight:900}.creation-handoff a{padding:11px 16px;color:#285a47;background:#fff;border-radius:999px;font-weight:800}@media(max-width:640px){.creation-heading{padding:26px 22px}.creation-handoff{align-items:flex-start;flex-direction:column}}
</style>
