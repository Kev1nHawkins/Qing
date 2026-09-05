<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import MediaImage from '@/components/MediaImage.vue'
import { api } from '@/services/api'
import type { Creation, CreationTemplate } from '@/types'

const props = defineProps<{
  templates: CreationTemplate[]
  initialTemplateCode?: string
}>()
const emit = defineEmits<{
  login: []
  templateChange: [code: string]
}>()
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
  AI_IMAGE: 'AI 创作海报',
  AI_TEXT_TEMPLATE: '文化创意海报',
  MOCK_TEMPLATE: '文化主题海报',
  UNKNOWN: '文化共创作品',
}
const selectedTemplateCode = ref('')
const selectedTemplate = computed(
  () => props.templates.find(item => item.code === selectedTemplateCode.value),
)
const schema = computed(() => selectedTemplate.value?.options_schema || fallbackSchema)
const choices = reactive<Record<string, string>>({})
const selectionSummary = computed(() =>
  Object.keys(schema.value).map(key => choices[key]).filter(Boolean).join(' × '),
)
const creation = ref<Creation | null>(null)
const generating = ref(false)
const feedback = ref('')
const feedbackKind = ref<'info' | 'success' | 'error'>('info')
const saveFeedback = ref('')
const savingImage = ref(false)
const isAuthenticated = computed(() => Boolean(localStorage.getItem('accessToken')))
const isMobileDevice = computed(() => {
  if (typeof navigator === 'undefined') return false
  return /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent)
})
const cultureItemId = computed(
  () => selectedTemplate.value?.culture_item_id ?? null,
)
const modeLabel = computed(
  () => modeLabels[creation.value?.generationMode || 'UNKNOWN'],
)

function resetForTemplate(template: CreationTemplate) {
  Object.keys(choices).forEach(key => delete choices[key])
  Object.entries(template.options_schema || fallbackSchema).forEach(([key, values]) => {
    choices[key] = values[0] || ''
  })
  creation.value = null
  feedback.value = ''
  feedbackKind.value = 'info'
  saveFeedback.value = ''
}

function activateTemplate(template: CreationTemplate, notify = true) {
  if (generating.value) return
  if (selectedTemplate.value?.id !== template.id) {
    selectedTemplateCode.value = template.code
    resetForTemplate(template)
  }
  if (notify) emit('templateChange', template.code)
}

watch(
  [() => props.templates, () => props.initialTemplateCode],
  ([templates, requestedCode]) => {
    if (!templates.length) {
      selectedTemplateCode.value = ''
      creation.value = null
      return
    }
    const requested = templates.find(item => item.code === requestedCode)
    const current = templates.find(item => item.code === selectedTemplateCode.value)
    const next = requested || current || templates[0]
    if (selectedTemplate.value?.id !== next.id) {
      selectedTemplateCode.value = next.code
      resetForTemplate(next)
    }
    if (requestedCode !== next.code) emit('templateChange', next.code)
  },
  { immediate: true },
)

function templateTone(code: string) {
  if (code.includes('lion')) return 'lion'
  if (code.includes('guangcai')) return 'guangcai'
  return 'kapok'
}

function optionCount(template: CreationTemplate) {
  return Object.keys(template.options_schema || {}).length
}

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
  if (!selectedTemplate.value) {
    feedback.value = '创作模板暂不可用，请稍后重试。'
    feedbackKind.value = 'error'
    return
  }
  generating.value = true
  saveFeedback.value = ''
  creation.value = null
  feedback.value = '小棉正在为你绘制海报，请稍等一下…'
  feedbackKind.value = 'info'
  try {
    const response = await api.post<{ data: Creation }>('/creations', {
      template_id: selectedTemplate.value.id,
      culture_item_id: cultureItemId.value,
      title: `${selectedTemplate.value.name} · ${selectionSummary.value}`.slice(0, 120),
      options: { ...choices },
    })
    creation.value = response.data.data
    const completed = await waitForResult(creation.value.id)
    if (completed.status === 'FAILED') throw new Error(completed.error_message || '生成失败')
    feedback.value = '你的专属海报出炉啦！快保存下来，或分享到社区吧 🎉'
    feedbackKind.value = 'success'
  } catch (event) {
    feedback.value = (event as Error).message
    feedbackKind.value = 'error'
  } finally {
    generating.value = false
  }
}

function imageFileName(blob: Blob) {
  const safeTitle = (creation.value?.title || '岭潮文化海报')
    .replace(/[\\/:*?"<>|]+/g, '-')
    .slice(0, 60)
  const extension = blob.type === 'image/png' ? 'png' : blob.type === 'image/webp' ? 'webp' : 'jpg'
  return `${safeTitle}.${extension}`
}

async function savePosterImage() {
  const url = creation.value?.resultUrl || creation.value?.output_url
  if (!url || savingImage.value) return
  savingImage.value = true
  saveFeedback.value = ''
  try {
    const response = await fetch(new URL(url, window.location.origin))
    if (!response.ok) throw new Error('图片下载失败')
    const blob = await response.blob()
    const filename = imageFileName(blob)
    const file = new File([blob], filename, { type: blob.type || 'image/jpeg' })
    if (
      isMobileDevice.value
      && typeof navigator.share === 'function'
      && typeof navigator.canShare === 'function'
      && navigator.canShare({ files: [file] })
    ) {
      await navigator.share({ files: [file], title: creation.value?.title || '岭潮文化海报' })
      saveFeedback.value = '已打开系统保存/分享面板。'
      return
    }
    const objectUrl = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = objectUrl
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 1500)
    saveFeedback.value = isMobileDevice.value
      ? '已打开图片保存；如浏览器未自动保存，请长按图片保存到相册。'
      : '图片已交给浏览器下载。'
  } catch (event) {
    if ((event as Error).name === 'AbortError') {
      saveFeedback.value = '已取消保存。'
    } else {
      window.open(new URL(url, window.location.origin), '_blank', 'noopener,noreferrer')
      saveFeedback.value = '自动保存失败，已打开原图；可长按或使用浏览器另存为。'
    }
  } finally {
    savingImage.value = false
  }
}

async function refreshStatus() {
  if (!creation.value) return
  try {
    const current = await loadCreation(creation.value.id)
    feedback.value = current.status === 'FAILED' ? '这次创作没有完成，再试一次吧！' : '小棉正在为你绘制海报，请稍等一下…'
    feedbackKind.value = current.status === 'FAILED' ? 'error' : 'success'
  } catch (event) {
    feedback.value = (event as Error).message
    feedbackKind.value = 'error'
  }
}
</script>

<template>
  <section class="poster-workbench">
    <div class="template-selector">
      <div class="template-selector-heading">
        <div><small>CHOOSE A TEMPLATE</small><h2>选择你的创作模板</h2></div>
        <span>模板会决定可选元素与 AI 创作方向</span>
      </div>
      <div class="template-card-list" role="list">
        <button
          v-for="item in templates"
          :key="item.id"
          type="button"
          class="template-card"
          :class="[{ active: selectedTemplate?.id === item.id }, `tone-${templateTone(item.code)}`]"
          :disabled="generating"
          :aria-pressed="selectedTemplate?.id === item.id"
          @click="activateTemplate(item)"
        >
          <span class="template-visual">
            <MediaImage v-if="item.preview_url" :src="item.preview_url" :alt="item.name" />
            <span v-else class="template-fallback" aria-hidden="true">
              <b>{{ item.name.slice(0, 1) }}</b><i>{{ item.code }}</i>
            </span>
          </span>
          <span class="template-card-copy">
            <small>{{ optionCount(item) }} 个创作维度</small>
            <strong>{{ item.name }}</strong>
            <span>{{ item.description }}</span>
          </span>
          <em>{{ selectedTemplate?.id === item.id ? '当前模板' : '选择模板' }}</em>
        </button>
      </div>
    </div>

    <div class="poster-studio">
    <aside class="poster-controls">
      <div class="studio-step"><span>01</span><div><small>SELECT ELEMENTS</small><h2>组合你的文化表达</h2></div></div>
      <p>选一选元素、地标和风格，马上开始你的岭南文化创作 🎨</p>
      <fieldset v-for="(values, key) in schema" :key="key">
        <legend>{{ labels[String(key)] || key }}</legend>
        <div class="poster-options">
          <button v-for="value in values" :key="value" type="button" :class="{ active: choices[String(key)] === value }" :aria-pressed="choices[String(key)] === value" @click="choices[String(key)] = value">{{ value }}</button>
        </div>
      </fieldset>
      <div class="selection-summary"><small>本次组合</small><strong>{{ selectionSummary }}</strong></div>
      <button class="studio-generate" type="button" :disabled="generating" @click="generatePoster">
        {{ generating ? '正在生成…' : creation?.status === 'SUCCESS' ? '换一个版式' : '生成文化海报' }}
      </button>
      <p v-if="feedback" class="studio-feedback" :class="feedbackKind">{{ feedback }}</p>
      <button v-if="creation && creation.status !== 'SUCCESS'" class="studio-refresh" type="button" @click="refreshStatus">看看创作进度</button>
      <RouterLink v-if="creation?.status === 'SUCCESS'" class="studio-publish" :to="{ path: '/community', query: { creationId: String(creation.id) }, hash: '#community-composer' }">
        去社区分享作品 →
      </RouterLink>
    </aside>

    <div class="poster-canvas-shell">
      <div v-if="!creation" class="poster-empty">
        <span>02</span><div class="empty-sheet"><i /><i /><i /></div><h3>你的创意画布</h3><p>准备好了吗？选好灵感，点击下方按钮开始创作吧！</p>
      </div>
      <div v-else-if="creation.status === 'SUCCESS' && creation.output_url" class="poster-result">
        <MediaImage :src="creation.output_url" :alt="creation.title" eager />
        <div class="result-meta">
          <strong>{{ modeLabel }}</strong>
          <span>{{ selectionSummary }}</span>
          <button class="poster-save" type="button" :disabled="savingImage" @click="savePosterImage">
            {{ savingImage ? '正在准备…' : isMobileDevice ? '保存图片到手机' : '下载生成图片' }}
          </button>
          <small v-if="saveFeedback" class="save-feedback" role="status">{{ saveFeedback }}</small>
        </div>
      </div>
      <div v-else-if="creation.status === 'FAILED'" class="poster-state failed"><b>生成失败</b><p>{{ creation.error_message }}</p></div>
      <div v-else class="poster-state"><span class="studio-spinner" /><b>正在创作</b><p>正在融合你选择的文化元素，请稍候…</p></div>
    </div>
    </div>
  </section>
</template>

<style scoped>
.poster-workbench{display:grid;gap:18px}.template-selector{display:grid;gap:14px;padding:22px;background:#fff;border:1px solid #dfe3dd;border-radius:10px}.template-selector-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:20px}.template-selector-heading small{color:#9f2d35;font-size:9px;font-weight:900;letter-spacing:.16em}.template-selector-heading h2{margin:4px 0 0;font-size:25px}.template-selector-heading>span{color:#68736d;font-size:12px}.template-card-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}.template-card{position:relative;display:grid;grid-template-columns:82px minmax(0,1fr);gap:12px;min-height:118px;overflow:hidden;padding:10px;border:1px solid #dce2dd;border-radius:9px;color:#33423b;background:#fff;text-align:left;cursor:pointer;transition:border-color .2s ease,box-shadow .2s ease,transform .2s ease}.template-card:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(34,55,45,.1)}.template-card.active{border-color:#9f2d35;box-shadow:0 0 0 2px rgba(159,45,53,.12)}.template-card:disabled{cursor:not-allowed;opacity:.68;transform:none}.template-visual{display:block;overflow:hidden;border-radius:7px;background:#f1e4d1}.template-visual :deep(.media-image){height:96px}.template-fallback{display:grid;place-items:center;height:96px;color:#fff;background:linear-gradient(145deg,#922c36,#d59b48)}.tone-lion .template-fallback{background:linear-gradient(145deg,#c13d2d,#e2aa31)}.tone-guangcai .template-fallback{background:linear-gradient(145deg,#235f71,#d59643)}.template-fallback b{font-family:serif;font-size:38px}.template-fallback i{max-width:70px;overflow:hidden;font-size:7px;font-style:normal;letter-spacing:.08em;text-overflow:ellipsis;white-space:nowrap}.template-card-copy{display:grid;align-content:center;gap:4px;min-width:0}.template-card-copy small{color:#9f2d35;font-size:9px;font-weight:800}.template-card-copy strong{font-size:15px}.template-card-copy>span{display:-webkit-box;overflow:hidden;color:#6b7771;font-size:10px;line-height:1.5;-webkit-box-orient:vertical;-webkit-line-clamp:2}.template-card>em{position:absolute;right:8px;top:7px;padding:3px 6px;color:#fff;background:rgba(39,81,65,.86);border-radius:999px;font-size:8px;font-style:normal}.template-card.active>em{background:#9f2d35}
.poster-studio{display:grid;grid-template-columns:minmax(340px,.8fr) minmax(420px,1.2fr);min-height:690px;overflow:hidden;border:1px solid #dfe3dd;border-radius:8px;background:#fff}.poster-controls{padding:36px}.studio-step{display:flex;align-items:center;gap:14px}.studio-step>span{display:grid;place-items:center;width:46px;height:46px;color:#fff;background:#9f2d35;font-family:serif;font-size:20px}.studio-step small{color:#9f2d35;font-size:9px;font-weight:900}.studio-step h2{margin:4px 0 0;font-size:27px}.poster-controls>p{color:#66716b;font-size:13px;line-height:1.75}.poster-controls fieldset{margin:24px 0 0;padding:0;border:0}.poster-controls legend{margin-bottom:10px;font-size:13px;font-weight:800}.poster-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.poster-options button{min-height:42px;padding:7px;border:1px solid #dfe3dd;border-radius:6px;color:#53605a;background:#fff}.poster-options button.active{color:#fff;background:#285a47;border-color:#285a47}.selection-summary{display:grid;gap:4px;margin-top:26px;padding:14px 16px;background:#f2f5f1;border-left:3px solid #cb9138}.selection-summary small{color:#66716b}.selection-summary strong{font-size:12px}.studio-generate{width:100%;min-height:50px;margin-top:16px;border:0;border-radius:6px;color:#fff;background:#9f2d35;font-weight:800}.studio-generate:disabled{opacity:.6}.studio-feedback{margin:12px 0 0!important;padding:10px 12px;border-radius:5px;background:#eef2ef}.studio-feedback.success{color:#245b47;background:#e7f2ec}.studio-feedback.error{color:#8e2730;background:#f8e7e5}.studio-refresh{margin-top:8px;padding:8px 0;border:0;color:#9f2d35;background:transparent;font-weight:800}.studio-publish{display:flex;align-items:center;justify-content:center;min-height:46px;margin-top:10px;color:#fff;background:#285a47;border-radius:6px;font-weight:800}.poster-canvas-shell{display:grid;place-items:center;min-width:0;padding:42px;background:#e7ece7}.poster-empty,.poster-state{width:min(420px,100%);text-align:center}.poster-empty>span{color:#9f2d35;font-family:serif;font-weight:800}.empty-sheet{position:relative;width:230px;height:330px;margin:18px auto 26px;background:#f8faf7;border:1px solid #cfd7d1;box-shadow:12px 14px 0 #d2dbd4}.empty-sheet:before{content:"";position:absolute;inset:14px;border:1px dashed #cad2cc}.empty-sheet i{position:absolute;left:42px;right:42px;height:8px;background:#e0e6e1}.empty-sheet i:nth-child(1){top:75px}.empty-sheet i:nth-child(2){top:96px}.empty-sheet i:nth-child(3){left:78px;right:78px;bottom:65px}.poster-empty p,.poster-state p{color:#66716b}.poster-result{position:relative;width:min(470px,100%);aspect-ratio:4/5;box-shadow:0 22px 48px rgba(43,57,49,.23)}.result-meta{position:absolute;left:12px;right:12px;bottom:12px;display:grid;gap:3px;padding:11px 13px;color:#fff;background:rgba(18,39,31,.88);border-radius:6px}.result-meta span,.result-meta small{font-size:11px}.poster-state{padding:35px;background:#fff;border-radius:12px}.poster-state.failed{color:#8e2730}.studio-spinner{display:block;width:40px;height:40px;margin:0 auto 18px;border:4px solid #cbd8d1;border-top-color:#285a47;border-radius:50%;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:900px){.poster-studio{grid-template-columns:1fr}.poster-canvas-shell{min-height:620px}}@media(max-width:560px){.poster-controls{padding:24px}.poster-options{grid-template-columns:1fr}.poster-canvas-shell{min-height:520px;padding:22px}}
.poster-save{min-height:36px;margin-top:7px;border:1px solid rgba(255,255,255,.55);border-radius:6px;color:#244f3f;background:#fff;font-weight:800;cursor:pointer}.poster-save:disabled{opacity:.65}.save-feedback{color:#e7d38d}
@media(max-width:640px){.template-selector{padding:18px 0;border-left:0;border-right:0}.template-selector-heading{align-items:flex-start;flex-direction:column;padding:0 18px}.template-card-list{display:flex;overflow-x:auto;padding:0 18px 8px;scroll-snap-type:x mandatory}.template-card{flex:0 0 min(280px,84vw);scroll-snap-align:start}}
</style>
