<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import MediaImage from '@/components/MediaImage.vue'
import { api } from '@/services/api'
import type { Creation, CreationTemplate, Culture } from '@/types'

const props = defineProps<{ template?: CreationTemplate; cultures: Culture[] }>()
const emit = defineEmits<{ login: [] }>()
const fallbackSchema: Record<string, string[]> = {
  culture_element: ['木棉', '醒狮', '广彩'],
  campus_landmark: ['广州大学图书馆', '红棉广场'],
  style: ['国潮', '剪纸', '现代插画'],
}
const labels: Record<string, string> = {
  culture_element: '文化元素',
  campus_landmark: '校园地标',
  style: '视觉风格',
}
const modeLabels: Record<string, string> = {
  AI_IMAGE: 'AI 图像生成',
  AI_TEXT_TEMPLATE: 'AI 文案＋模板生成',
  MOCK_TEMPLATE: '演示降级模板',
  UNKNOWN: '生成模式确认中',
}
const schema = computed(() => props.template?.options_schema || fallbackSchema)
const choices = reactive<Record<string, string>>({})
const creation = ref<Creation | null>(null)
const generating = ref(false)
const feedback = ref('')
const feedbackKind = ref<'info' | 'success' | 'error'>('info')
const isAuthenticated = computed(() => Boolean(localStorage.getItem('accessToken')))
const cultureItemId = computed(
  () => props.template?.culture_item_id || props.cultures[0]?.id || null,
)
const modeLabel = computed(
  () => modeLabels[creation.value?.generationMode || 'UNKNOWN'],
)

watch(
  schema,
  (next) => {
    Object.entries(next).forEach(([key, values]) => {
      if (!choices[key] || !values.includes(choices[key])) choices[key] = values[0] || ''
    })
  },
  { immediate: true },
)

async function loadCreation(id: number) {
  const response = await api.get<{ data: Creation }>(`/creations/${id}`)
  creation.value = response.data.data
  return creation.value
}

async function waitForResult(id: number) {
  for (let attempt = 0; attempt < 45; attempt += 1) {
    const current = await loadCreation(id)
    if (current.status === 'SUCCESS' || current.status === 'FAILED') return current
    await new Promise(resolve => window.setTimeout(resolve, 750))
  }
  throw new Error('生成仍在处理中，请稍后刷新状态。')
}

async function generatePoster() {
  if (!isAuthenticated.value) {
    emit('login')
    return
  }
  if (!props.template) {
    feedback.value = '创作模板暂不可用，请稍后重试。'
    feedbackKind.value = 'error'
    return
  }
  generating.value = true
  creation.value = null
  feedback.value = '正在提交独立创作任务，生成成功前不会显示模板预览。'
  feedbackKind.value = 'info'
  try {
    const response = await api.post<{ data: Creation }>('/creations', {
      template_id: props.template.id,
      culture_item_id: cultureItemId.value,
      title: `${choices.culture_element} × ${choices.campus_landmark}文化海报`,
      options: { ...choices },
    })
    creation.value = response.data.data
    const completed = await waitForResult(creation.value.id)
    if (completed.status === 'FAILED') throw new Error(completed.error_message || '生成失败')
    feedback.value = `作品 #${completed.id} 已生成：${modeLabels[completed.generationMode] || completed.generationMode}`
    feedbackKind.value = 'success'
  } catch (event) {
    feedback.value = (event as Error).message
    feedbackKind.value = 'error'
  } finally {
    generating.value = false
  }
}

async function refreshStatus() {
  if (!creation.value) return
  try {
    const current = await loadCreation(creation.value.id)
    feedback.value = `作品 #${current.id} 当前状态：${current.status}`
    feedbackKind.value = current.status === 'FAILED' ? 'error' : 'success'
  } catch (event) {
    feedback.value = (event as Error).message
    feedbackKind.value = 'error'
  }
}
</script>

<template>
  <section class="poster-studio">
    <aside class="poster-controls">
      <div class="studio-step"><span>01</span><div><small>SELECT ELEMENTS</small><h2>组合你的文化表达</h2></div></div>
      <p>选择文化元素、校园地标与视觉风格。每次点击都会建立独立作品记录，只有后端返回 SUCCESS 后才展示最终图片。</p>
      <fieldset v-for="(values, key) in schema" :key="key">
        <legend>{{ labels[String(key)] || key }}</legend>
        <div class="poster-options">
          <button v-for="value in values" :key="value" type="button" :class="{ active: choices[String(key)] === value }" :aria-pressed="choices[String(key)] === value" @click="choices[String(key)] = value">{{ value }}</button>
        </div>
      </fieldset>
      <div class="selection-summary"><small>本次组合</small><strong>{{ choices.culture_element }} × {{ choices.campus_landmark }} × {{ choices.style }}</strong></div>
      <button class="studio-generate" type="button" :disabled="generating" @click="generatePoster">
        {{ generating ? '正在生成…' : creation?.status === 'SUCCESS' ? '换一个版式' : '生成文化海报' }}
      </button>
      <p v-if="feedback" class="studio-feedback" :class="feedbackKind">{{ feedback }}</p>
      <button v-if="creation && creation.status !== 'SUCCESS'" class="studio-refresh" type="button" @click="refreshStatus">刷新生成状态</button>
      <RouterLink v-if="creation?.status === 'SUCCESS'" class="studio-publish" :to="{ path: '/community', query: { creationId: String(creation.id) }, hash: '#community-composer' }">
        前往共创社区发布 →
      </RouterLink>
    </aside>

    <div class="poster-canvas-shell">
      <div v-if="!creation" class="poster-empty">
        <span>02</span><div class="empty-sheet"><i /><i /><i /></div><h3>等待真实生成结果</h3><p>右侧不会用固定校园照片冒充生成结果。</p>
      </div>
      <div v-else-if="creation.status === 'SUCCESS' && creation.output_url" class="poster-result">
        <MediaImage :src="creation.output_url" :alt="creation.title" eager />
        <div class="result-meta">
          <strong>{{ modeLabel }}</strong>
          <span>{{ creation.provider }} · {{ creation.model }}</span>
          <small v-if="creation.fallbackUsed">真实模型不可用，本次使用了降级模板</small>
          <small v-else-if="creation.generationMode === 'MOCK_TEMPLATE'">本图来自本地 SVG 模板，不是 AI 图片模型生成</small>
          <small v-else-if="creation.generationMode === 'AI_TEXT_TEMPLATE'">DeepSeek 生成文案与视觉 Prompt，背景由本地模板渲染</small>
          <small v-else>图片由已配置的独立图像 Provider 返回</small>
        </div>
      </div>
      <div v-else-if="creation.status === 'FAILED'" class="poster-state failed"><b>生成失败</b><p>{{ creation.error_message }}</p></div>
      <div v-else class="poster-state"><span class="studio-spinner" /><b>{{ creation.status }}</b><p>后端正在推进真实任务状态，请勿把当前状态作为可发布作品。</p></div>
    </div>
  </section>
</template>

<style scoped>
.poster-studio{display:grid;grid-template-columns:minmax(340px,.8fr) minmax(420px,1.2fr);min-height:690px;overflow:hidden;border:1px solid #dfe3dd;border-radius:8px;background:#fff}.poster-controls{padding:36px}.studio-step{display:flex;align-items:center;gap:14px}.studio-step>span{display:grid;place-items:center;width:46px;height:46px;color:#fff;background:#9f2d35;font-family:serif;font-size:20px}.studio-step small{color:#9f2d35;font-size:9px;font-weight:900}.studio-step h2{margin:4px 0 0;font-size:27px}.poster-controls>p{color:#66716b;font-size:13px;line-height:1.75}.poster-controls fieldset{margin:24px 0 0;padding:0;border:0}.poster-controls legend{margin-bottom:10px;font-size:13px;font-weight:800}.poster-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.poster-options button{min-height:42px;padding:7px;border:1px solid #dfe3dd;border-radius:6px;color:#53605a;background:#fff}.poster-options button.active{color:#fff;background:#285a47;border-color:#285a47}.selection-summary{display:grid;gap:4px;margin-top:26px;padding:14px 16px;background:#f2f5f1;border-left:3px solid #cb9138}.selection-summary small{color:#66716b}.selection-summary strong{font-size:12px}.studio-generate{width:100%;min-height:50px;margin-top:16px;border:0;border-radius:6px;color:#fff;background:#9f2d35;font-weight:800}.studio-generate:disabled{opacity:.6}.studio-feedback{margin:12px 0 0!important;padding:10px 12px;border-radius:5px;background:#eef2ef}.studio-feedback.success{color:#245b47;background:#e7f2ec}.studio-feedback.error{color:#8e2730;background:#f8e7e5}.studio-refresh{margin-top:8px;padding:8px 0;border:0;color:#9f2d35;background:transparent;font-weight:800}.studio-publish{display:flex;align-items:center;justify-content:center;min-height:46px;margin-top:10px;color:#fff;background:#285a47;border-radius:6px;font-weight:800}.poster-canvas-shell{display:grid;place-items:center;min-width:0;padding:42px;background:#e7ece7}.poster-empty,.poster-state{width:min(420px,100%);text-align:center}.poster-empty>span{color:#9f2d35;font-family:serif;font-weight:800}.empty-sheet{position:relative;width:230px;height:330px;margin:18px auto 26px;background:#f8faf7;border:1px solid #cfd7d1;box-shadow:12px 14px 0 #d2dbd4}.empty-sheet:before{content:"";position:absolute;inset:14px;border:1px dashed #cad2cc}.empty-sheet i{position:absolute;left:42px;right:42px;height:8px;background:#e0e6e1}.empty-sheet i:nth-child(1){top:75px}.empty-sheet i:nth-child(2){top:96px}.empty-sheet i:nth-child(3){left:78px;right:78px;bottom:65px}.poster-empty p,.poster-state p{color:#66716b}.poster-result{position:relative;width:min(470px,100%);aspect-ratio:4/5;box-shadow:0 22px 48px rgba(43,57,49,.23)}.result-meta{position:absolute;left:12px;right:12px;bottom:12px;display:grid;gap:3px;padding:11px 13px;color:#fff;background:rgba(18,39,31,.88);border-radius:6px}.result-meta span,.result-meta small{font-size:11px}.poster-state{padding:35px;background:#fff;border-radius:12px}.poster-state.failed{color:#8e2730}.studio-spinner{display:block;width:40px;height:40px;margin:0 auto 18px;border:4px solid #cbd8d1;border-top-color:#285a47;border-radius:50%;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:900px){.poster-studio{grid-template-columns:1fr}.poster-canvas-shell{min-height:620px}}@media(max-width:560px){.poster-controls{padding:24px}.poster-options{grid-template-columns:1fr}.poster-canvas-shell{min-height:520px;padding:22px}}
</style>
