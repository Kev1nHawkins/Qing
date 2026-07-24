<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { api } from '@/services/api'
import MediaImage from '@/components/MediaImage.vue'
import { visuals } from '@/data/visuals'
import gzuOfficialLogo from '@/assets/culture/gzu-official-logo.png'
import type { Creation, CreationTemplate, Culture } from '@/types'

const props = defineProps<{ template?: CreationTemplate; cultures: Culture[] }>()
const emit = defineEmits<{ login: [] }>()
const fallbackSchema: Record<string, string[]> = {
  culture_element: ['木棉', '醒狮', '广彩'],
  campus_landmark: ['广州大学图书馆', '红棉广场'],
  style: ['国潮', '剪纸', '现代插画'],
}
const labels: Record<string, string> = { culture_element: '文化元素', campus_landmark: '校园地标', style: '视觉风格' }
const schema = computed(() => props.template?.options_schema || fallbackSchema)
const choices = reactive<Record<string, string>>({})
const generating = ref(false)
const hasPreview = ref(false)
const creation = ref<Creation | null>(null)
const feedback = ref('')
const feedbackKind = ref<'info' | 'success' | 'error'>('info')
const isAuthenticated = computed(() => Boolean(localStorage.getItem('accessToken')))

watch(schema, (next) => {
  Object.entries(next).forEach(([key, values]) => { if (!choices[key] || !values.includes(choices[key])) choices[key] = values[0] || '' })
}, { immediate: true })

const posterClass = computed(() => ({
  'is-paper': choices.style === '剪纸',
  'is-modern': choices.style === '现代插画',
  'is-lion': choices.culture_element === '醒狮',
  'is-canton': choices.culture_element === '广彩',
  'is-library': choices.campus_landmark === '广州大学图书馆',
  'is-square': choices.campus_landmark === '红棉广场',
}))
const title = computed(() => choices.culture_element === '木棉' ? '红棉生于城' : `${choices.culture_element || '岭南'}入校园`)
const cultureItemId = computed(() => props.template?.culture_item_id || props.cultures[0]?.id || null)

async function generatePoster() {
  generating.value = true
  hasPreview.value = true
  creation.value = null
  feedback.value = '正在编排文化元素、校园地标与视觉风格…'
  feedbackKind.value = 'info'
  if (!props.template) {
    feedback.value = '模板服务暂不可用，当前已生成本地交互预览。'
    generating.value = false
    return
  }
  if (!isAuthenticated.value) {
    feedback.value = '本地预览已生成。登录后可把这组参数提交到真实创作任务队列。'
    generating.value = false
    return
  }
  try {
    const response = await api.post<{ data: Creation }>('/creations', {
      template_id: props.template.id,
      culture_item_id: cultureItemId.value,
      title: `${choices.culture_element} × ${choices.campus_landmark}文化海报`,
      options: { ...choices },
    })
    creation.value = response.data.data
    feedback.value = `创作任务 #${creation.value.id} 已提交，后端状态：${creation.value.status}`
    feedbackKind.value = 'success'
  } catch (event) {
    feedback.value = (event as Error).message
    feedbackKind.value = 'error'
  } finally { generating.value = false }
}

async function refreshStatus() {
  if (!creation.value) return
  try {
    const response = await api.get<{ data: Creation }>(`/creations/${creation.value.id}`)
    creation.value = response.data.data
    feedback.value = `任务 #${creation.value.id} 当前状态：${creation.value.status}`
    feedbackKind.value = creation.value.status === 'FAILED' ? 'error' : 'success'
  } catch (event) { feedback.value = (event as Error).message; feedbackKind.value = 'error' }
}
</script>

<template>
  <section class="poster-studio">
    <aside class="poster-controls">
      <div class="studio-step"><span>01</span><div><small>SELECT ELEMENTS</small><h2>组合你的文化表达</h2></div></div>
      <p>依次选择文化元素、广州大学校园地标和视觉风格。生成前右侧只显示空白画布，结果不会提前出现。</p>
      <fieldset v-for="(values, key) in schema" :key="key">
        <legend>{{ labels[String(key)] || key }}</legend>
        <div class="poster-options">
          <button v-for="value in values" :key="value" type="button" :class="{ active: choices[String(key)] === value }" :aria-pressed="choices[String(key)] === value" @click="choices[String(key)] = value">{{ value }}</button>
        </div>
      </fieldset>
      <div class="selection-summary"><small>本次组合</small><strong>{{ choices.culture_element }} × {{ choices.campus_landmark }} × {{ choices.style }}</strong></div>
      <button class="studio-generate" type="button" :disabled="generating" @click="generatePoster">{{ generating ? '正在生成…' : '生成文化海报' }}</button>
      <p v-if="feedback" class="studio-feedback" :class="feedbackKind">{{ feedback }}</p>
      <button v-if="!isAuthenticated && hasPreview" class="studio-login" type="button" @click="emit('login')">登录并提交真实任务</button>
      <button v-if="creation" class="studio-login" type="button" @click="refreshStatus">刷新生成状态</button>
    </aside>

    <div class="poster-canvas-shell">
      <div v-if="!hasPreview" class="poster-empty">
        <span>02</span><div class="empty-sheet"><i /><i /><i /></div><h3>等待你的创作选择</h3><p>完成左侧三组选项后，点击“生成文化海报”。</p>
      </div>
      <div v-else-if="creation?.status === 'SUCCESS' && creation.output_url" class="poster-result-image"><MediaImage :src="creation.output_url" alt="AI 生成文化海报" /></div>
      <div v-else class="generated-poster" :class="posterClass">
        <MediaImage :src="visuals.campus" :alt="`${choices.campus_landmark}文化海报版式预览`" />
        <div class="generated-wash" /><div class="generated-grid" />
        <div class="generated-landmark"><i /><i /><i /><i /><i /></div>
        <div class="generated-flower"><i /><i /><i /><i /><i /><b /></div>
        <div class="generated-copy">
          <img :src="gzuOfficialLogo" alt="广州大学" />
          <small>LINGNAN CULTURE × GZHU</small>
          <span>{{ choices.culture_element }}</span>
          <h3>{{ title }}<br />文化长于校园</h3>
          <p>{{ choices.campus_landmark }} · {{ choices.style }}</p>
          <footer><em>AI CO-CREATION / 2026</em><b>广</b></footer>
        </div>
        <div class="preview-label">交互版式预览</div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.poster-studio{display:grid;grid-template-columns:minmax(340px,.8fr) minmax(420px,1.2fr);min-height:690px;overflow:hidden;border:1px solid #dfe3dd;border-radius:8px;background:#fff}.poster-controls{padding:36px;background:#fff}.studio-step{display:flex;align-items:center;gap:14px}.studio-step>span{display:grid;place-items:center;width:46px;height:46px;color:#fff;background:#9f2d35;font-family:serif;font-size:20px}.studio-step small{color:#9f2d35;font-size:9px;font-weight:900}.studio-step h2{margin:4px 0 0;font-size:27px}.poster-controls>p{color:#66716b;font-size:13px;line-height:1.75}.poster-controls fieldset{margin:24px 0 0;padding:0;border:0}.poster-controls legend{margin-bottom:10px;font-size:13px;font-weight:800}.poster-options{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.poster-options button{min-height:42px;padding:7px;border:1px solid #dfe3dd;border-radius:6px;color:#53605a;background:#fff;font-size:12px}.poster-options button.active{color:#fff;background:#285a47;border-color:#285a47;box-shadow:0 5px 12px rgba(40,90,71,.18)}.selection-summary{display:grid;gap:4px;margin-top:26px;padding:14px 16px;background:#f2f5f1;border-left:3px solid #cb9138}.selection-summary small{color:#66716b}.selection-summary strong{font-size:12px}.studio-generate{width:100%;min-height:50px;margin-top:16px;border:0;border-radius:6px;color:#fff;background:#9f2d35;font-weight:800}.studio-generate:disabled{opacity:.6}.studio-feedback{margin:12px 0 0!important;padding:10px 12px;border-radius:5px;background:#eef2ef}.studio-feedback.success{color:#245b47;background:#e7f2ec}.studio-feedback.error{color:#8e2730;background:#f8e7e5}.studio-login{margin-top:8px;padding:8px 0;border:0;color:#9f2d35;background:transparent;font-weight:800}.poster-canvas-shell{display:grid;place-items:center;min-width:0;padding:42px;background:#e7ece7}.poster-empty{width:min(400px,100%);text-align:center}.poster-empty>span{color:#9f2d35;font-family:serif;font-size:13px;font-weight:800}.empty-sheet{position:relative;width:230px;height:330px;margin:18px auto 26px;background:#f8faf7;border:1px solid #cfd7d1;box-shadow:12px 14px 0 #d2dbd4}.empty-sheet:before{content:"";position:absolute;inset:14px;border:1px dashed #cad2cc}.empty-sheet i{position:absolute;left:42px;right:42px;height:8px;background:#e0e6e1}.empty-sheet i:nth-child(1){top:75px}.empty-sheet i:nth-child(2){top:96px}.empty-sheet i:nth-child(3){left:78px;right:78px;bottom:65px}.poster-empty h3{margin:0;font-size:20px}.poster-empty p{color:#66716b}.generated-poster{position:relative;width:min(470px,100%);aspect-ratio:4/5;overflow:hidden;isolation:isolate;color:#fff;background:#711c24;box-shadow:0 22px 48px rgba(43,57,49,.23)}.generated-poster>img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:saturate(.72) contrast(1.08)}.generated-wash{position:absolute;z-index:1;inset:0;background:linear-gradient(180deg,rgba(64,8,16,.18),rgba(84,16,26,.55) 53%,rgba(65,8,16,.98))}.generated-grid{position:absolute;z-index:2;inset:12px;border:1px solid rgba(255,235,195,.58)}.generated-flower{position:absolute;z-index:4;right:30px;top:34px;width:76px;height:76px}.generated-flower i{position:absolute;left:27px;top:4px;width:25px;height:41px;background:#d8433e;border-radius:75% 25% 70% 30%;transform-origin:50% 34px}.generated-flower i:nth-child(2){transform:rotate(72deg)}.generated-flower i:nth-child(3){transform:rotate(144deg)}.generated-flower i:nth-child(4){transform:rotate(216deg)}.generated-flower i:nth-child(5){transform:rotate(288deg)}.generated-flower b{position:absolute;z-index:2;left:31px;top:28px;width:17px;height:17px;border-radius:50%;background:#e8ad38}.generated-copy{position:absolute;z-index:5;inset:34px;display:flex;flex-direction:column}.generated-copy>img{width:155px;height:auto;padding:7px;background:rgba(255,255,255,.36);border-radius:4px;backdrop-filter:blur(7px)}.generated-copy>small{align-self:flex-start;margin-top:8px;padding:5px 8px;color:#4d171c;background:#f1cf90;font-size:8px;font-weight:900}.generated-copy>span{margin-top:auto;font-family:serif;font-size:76px;line-height:.9;text-shadow:0 3px 12px rgba(0,0,0,.28)}.generated-copy h3{margin:13px 0 8px;color:#fff4de;font-family:serif;font-size:26px;line-height:1.3}.generated-copy p{margin:0;color:#f1c98f;font-size:11px}.generated-copy footer{display:flex;align-items:end;justify-content:space-between;margin-top:20px;padding:12px 0 0;color:inherit;background:transparent;border-top:1px solid rgba(255,255,255,.36)}.generated-copy footer em{font-size:8px;font-style:normal}.generated-copy footer b{display:grid;place-items:center;width:38px;height:38px;border:2px solid #edc279;font-family:serif;font-size:20px}.preview-label{position:absolute;z-index:7;right:12px;bottom:12px;padding:4px 7px;color:#fff;background:rgba(20,31,26,.72);font-size:9px}.generated-poster.is-paper .generated-wash{background:linear-gradient(180deg,rgba(245,224,190,.12),rgba(130,26,31,.43) 52%,#8f252d)}.generated-poster.is-paper .generated-grid{border-style:dashed}.generated-poster.is-modern .generated-wash{background:linear-gradient(180deg,rgba(17,70,58,.08),rgba(26,92,76,.56) 52%,#184c3f)}.generated-poster.is-modern .generated-copy>small{color:#174c3f;background:#dcebdc}.poster-result-image{width:min(470px,100%);aspect-ratio:4/5;overflow:hidden;box-shadow:0 22px 48px rgba(43,57,49,.23)}@media(max-width:900px){.poster-studio{grid-template-columns:1fr}.poster-canvas-shell{min-height:620px}}@media(max-width:560px){.poster-controls{padding:24px}.poster-options{grid-template-columns:1fr}.poster-canvas-shell{min-height:520px;padding:22px}.generated-copy{inset:26px}.generated-copy>span{font-size:64px}}
</style>
