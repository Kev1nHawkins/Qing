<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import MediaImage from '@/components/MediaImage.vue'
import { api } from '@/services/api'
import type { Creation } from '@/types'

type AspectRatio = 'SQUARE' | 'PORTRAIT' | 'LANDSCAPE'

const emit = defineEmits<{ login: []; busyChange: [busy: boolean] }>()
const prompt = ref('')
const aspectRatio = ref<AspectRatio>('PORTRAIT')
const creation = ref<Creation | null>(null)
const generating = ref(false)
const feedback = ref('')
const saving = ref(false)
const examples = [
  '晨光中的岭南骑楼建筑，写实摄影，温暖光影，丰富细节',
  '身穿红色国潮服饰的青年人物立绘，自信自然，干净背景',
  '未来感校园图书馆，绿色生态建筑，电影级广角构图',
]
const canvasClass = computed(() => `ratio-${aspectRatio.value.toLowerCase()}`)

watch(generating, value => emit('busyChange', value))

async function loadCreation(id: number) {
  const { data } = await api.get<{ data: Creation }>(`/creations/${id}`)
  creation.value = data.data
  return creation.value
}

async function waitForResult(id: number) {
  for (let attempt = 0; attempt < 120; attempt += 1) {
    const current = await loadCreation(id)
    if (current.status === 'SUCCESS' || current.status === 'FAILED') return current
    await new Promise(resolve => window.setTimeout(resolve, 1000))
  }
  throw new Error('生成仍在处理中，可稍后点击“查看最新进度”。')
}

async function generate() {
  if (!localStorage.getItem('accessToken')) return emit('login')
  if (!prompt.value.trim()) return void (feedback.value = '请先描述你想生成的画面。')
  generating.value = true
  creation.value = null
  feedback.value = 'AI 正在理解你的描述并绘制画面…'
  try {
    const { data } = await api.post<{ data: Creation }>('/creations/free-image', {
      prompt: prompt.value.trim(),
      aspectRatio: aspectRatio.value,
    })
    creation.value = data.data
    const completed = await waitForResult(data.data.id)
    if (completed.status === 'FAILED') throw new Error(completed.error_message || '图片生成失败')
    feedback.value = '自由图片已生成，可以下载或分享到社区。'
  } catch (event) {
    feedback.value = (event as Error).message
  } finally {
    generating.value = false
  }
}

async function refresh() {
  if (!creation.value) return
  try {
    const current = await loadCreation(creation.value.id)
    feedback.value = current.status === 'SUCCESS' ? '图片已生成。' : current.status === 'FAILED' ? (current.error_message || '图片生成失败') : '任务仍在处理中。'
  } catch (event) {
    feedback.value = (event as Error).message
  }
}

async function download() {
  if (!creation.value?.output_url || saving.value) return
  saving.value = true
  try {
    const response = await fetch(new URL(creation.value.output_url, window.location.origin))
    if (!response.ok) throw new Error('图片下载失败')
    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `${creation.value.title.replace(/[\\/:*?"<>|]+/g, '-')}.${blob.type.includes('svg') ? 'svg' : blob.type.includes('png') ? 'png' : 'jpg'}`
    anchor.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1500)
    feedback.value = '图片已交给浏览器下载。'
  } catch (event) {
    feedback.value = (event as Error).message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="free-studio">
    <aside class="free-controls">
      <small>FREE IMAGE CREATION</small>
      <h2>把任何灵感变成画面</h2>
      <p>可以描述人物、建筑、场景、光线与画面风格。描述越具体，生成结果越接近你的想法。</p>
      <label>
        <span>画面提示词</span>
        <textarea v-model="prompt" maxlength="2000" rows="8" :disabled="generating" placeholder="例如：一位站在岭南骑楼前的青年，黄昏暖光，电影感摄影……" />
        <small>{{ prompt.length }}/2000</small>
      </label>
      <div class="prompt-examples">
        <button v-for="item in examples" :key="item" type="button" :disabled="generating" @click="prompt = item">{{ item }}</button>
      </div>
      <fieldset>
        <legend>图片比例</legend>
        <button type="button" :class="{ active: aspectRatio === 'PORTRAIT' }" :disabled="generating" @click="aspectRatio = 'PORTRAIT'">竖版<br><small>768×1344</small></button>
        <button type="button" :class="{ active: aspectRatio === 'SQUARE' }" :disabled="generating" @click="aspectRatio = 'SQUARE'">方形<br><small>1024×1024</small></button>
        <button type="button" :class="{ active: aspectRatio === 'LANDSCAPE' }" :disabled="generating" @click="aspectRatio = 'LANDSCAPE'">横版<br><small>1344×768</small></button>
      </fieldset>
      <button class="generate" type="button" :disabled="generating || !prompt.trim()" @click="generate">{{ generating ? '正在生成…' : '生成自由图片' }}</button>
      <p v-if="feedback" class="feedback" role="status">{{ feedback }}</p>
      <button v-if="creation && !['SUCCESS', 'FAILED'].includes(creation.status)" class="refresh" type="button" @click="refresh">查看最新进度</button>
    </aside>
    <div class="free-canvas">
      <div v-if="!creation" class="free-empty" :class="canvasClass"><b>自由画布</b><span>你的画面将在这里出现</span></div>
      <div v-else-if="creation.status === 'SUCCESS' && creation.output_url" class="free-result" :class="canvasClass">
        <MediaImage :src="creation.output_url" :alt="creation.title" eager />
        <div><button type="button" :disabled="saving" @click="download">{{ saving ? '准备中…' : '下载图片' }}</button><RouterLink :to="{ path: '/community', query: { creationId: String(creation.id) }, hash: '#community-composer' }">去社区分享</RouterLink></div>
      </div>
      <div v-else-if="creation.status === 'FAILED'" class="free-state"><b>生成失败</b><p>{{ creation.error_message }}</p></div>
      <div v-else class="free-state"><i /><b>正在创作</b><p>生成任务已提交，请稍候…</p></div>
    </div>
  </section>
</template>

<style scoped>
.free-studio{display:grid;grid-template-columns:minmax(340px,.85fr) minmax(420px,1.15fr);min-height:680px;overflow:hidden;border:1px solid #dfe3dd;border-radius:10px;background:#fff}.free-controls{padding:34px}.free-controls>small{color:#9f2d35;font-weight:900;letter-spacing:.14em}.free-controls h2{margin:7px 0 10px;font-size:30px}.free-controls>p{color:#66716b;line-height:1.7}.free-controls label{display:grid;gap:7px;margin-top:22px;font-weight:800}.free-controls textarea{box-sizing:border-box;width:100%;padding:13px;border:1px solid #d4dcd6;border-radius:8px;resize:vertical;font:inherit;line-height:1.65}.free-controls label small{text-align:right;color:#78817c}.prompt-examples{display:grid;gap:6px;margin-top:10px}.prompt-examples button{padding:8px 10px;border:0;border-radius:6px;color:#5f6d66;background:#f1f4f1;text-align:left;font-size:11px}.free-controls fieldset{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:22px 0 0;padding:0;border:0}.free-controls legend{margin-bottom:9px;font-size:13px;font-weight:800}.free-controls fieldset button{min-height:54px;border:1px solid #d8dfda;border-radius:7px;background:#fff}.free-controls fieldset button.active{color:#fff;background:#285a47;border-color:#285a47}.generate{width:100%;min-height:50px;margin-top:18px;border:0;border-radius:7px;color:#fff;background:#9f2d35;font-weight:900}.generate:disabled{opacity:.55}.feedback{padding:10px 12px;color:#395046;background:#edf3ef;border-radius:6px;font-size:12px}.refresh{border:0;color:#9f2d35;background:transparent;font-weight:800}.free-canvas{display:grid;place-items:center;padding:38px;background:#e7ece7}.free-empty,.free-result{position:relative;display:grid;place-items:center;overflow:hidden;max-width:100%;max-height:580px;background:#f8faf8;border:1px dashed #afbbb4;box-shadow:0 18px 42px rgba(34,55,45,.16)}.ratio-portrait{width:330px;aspect-ratio:768/1344}.ratio-square{width:470px;aspect-ratio:1}.ratio-landscape{width:560px;aspect-ratio:1344/768}.free-empty b{font-family:serif;font-size:32px}.free-empty span{color:#7b8780}.free-result :deep(.media-image){position:absolute;inset:0;height:100%}.free-result>div{position:absolute;z-index:2;left:12px;right:12px;bottom:12px;display:flex;gap:8px;padding:10px;background:rgba(18,39,31,.86);border-radius:7px}.free-result button,.free-result a{display:grid;place-items:center;flex:1;min-height:38px;border:0;border-radius:5px;color:#285a47;background:#fff;font-weight:800}.free-state{text-align:center}.free-state i{display:block;width:38px;height:38px;margin:0 auto 16px;border:4px solid #c7d2cb;border-top-color:#285a47;border-radius:50%;animation:spin 1s linear infinite}@keyframes spin{to{transform:rotate(360deg)}}@media(max-width:900px){.free-studio{grid-template-columns:1fr}.free-canvas{min-height:540px}}@media(max-width:560px){.free-controls{padding:24px}.free-canvas{min-height:440px;padding:20px}.free-controls fieldset{grid-template-columns:1fr}.ratio-landscape{width:100%}}
</style>
