<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/services/api'
import type { PostDraft } from '@/types'
import type { CommunityPostDraft } from '@/types/community'

const emit = defineEmits<{ login: []; busyChange: [busy: boolean] }>()
const router = useRouter()
const prompt = ref('')
const generating = ref(false)
const feedback = ref('')
const copied = ref(false)
const draft = reactive({ title: '', content: '', tags: '', provider: '', model: '', fallbackUsed: false })

watch(generating, value => emit('busyChange', value))

async function generate() {
  if (!localStorage.getItem('accessToken')) return emit('login')
  if (!prompt.value.trim()) return void (feedback.value = '请先告诉 AI 你想写什么。')
  generating.value = true
  feedback.value = 'AI 正在整理你的表达…'
  copied.value = false
  try {
    const { data } = await api.post<{ data: PostDraft }>('/ai/post-drafts', { prompt: prompt.value.trim() }, { timeout: 35000 })
    Object.assign(draft, data.data, { tags: data.data.tags.join('，') })
    feedback.value = data.data.fallbackUsed ? '外部 AI 暂不可用，已生成一份本地草稿，你可以继续编辑。' : '推文草稿已生成，修改满意后再去发布。'
  } catch (event) {
    feedback.value = (event as Error).message
  } finally {
    generating.value = false
  }
}

async function copyDraft() {
  if (!draft.title || !draft.content) return
  try {
    await navigator.clipboard.writeText(`${draft.title}\n\n${draft.content}\n\n${draft.tags}`)
    copied.value = true
  } catch {
    feedback.value = '浏览器未允许自动复制，请手动选择文本复制。'
  }
}

async function publish() {
  if (!draft.title.trim() || !draft.content.trim()) return void (feedback.value = '标题和正文不能为空。')
  const payload: CommunityPostDraft = {
    version: 1,
    title: draft.title.trim().slice(0, 120),
    content: draft.content.trim().slice(0, 5000),
    tags: draft.tags.split(/[,，]/).map(item => item.trim()).filter(Boolean).slice(0, 10),
  }
  sessionStorage.setItem('lingchao.community.aiDraft.v1', JSON.stringify(payload))
  await router.push({ path: '/community', query: { draft: 'ai' }, hash: '#community-composer' })
}
</script>

<template>
  <section class="draft-studio">
    <aside class="draft-request">
      <small>AI SOCIAL COPY</small><h2>让 AI 帮你写推文</h2>
      <p>告诉 AI 主题、语气、受众和你希望强调的内容。它会生成标题、正文与标签，发布前都可以修改。</p>
      <label><span>你的写作要求</span><textarea v-model="prompt" maxlength="1000" rows="10" :disabled="generating" placeholder="例如：写一篇轻松活泼的校园推文，介绍我刚生成的醒狮海报，邀请同学留言交流……" /><small>{{ prompt.length }}/1000</small></label>
      <button class="draft-generate" type="button" :disabled="generating || !prompt.trim()" @click="generate">{{ generating ? '正在生成…' : draft.title ? '重新生成' : '生成推文草稿' }}</button>
      <p v-if="feedback" class="draft-feedback" role="status">{{ feedback }}</p>
    </aside>
    <div class="draft-editor">
      <div v-if="!draft.title" class="draft-empty"><b>文字灵感区</b><p>输入你的想法，AI 草稿会出现在这里。</p></div>
      <template v-else>
        <header><div><small>EDITABLE DRAFT</small><h3>发布前再读一遍</h3></div><span>{{ draft.fallbackUsed ? '本地草稿' : draft.provider }}</span></header>
        <label><span>标题</span><input v-model="draft.title" maxlength="120"><small>{{ draft.title.length }}/120</small></label>
        <label><span>正文</span><textarea v-model="draft.content" maxlength="5000" rows="13" /><small>{{ draft.content.length }}/5000</small></label>
        <label><span>标签</span><input v-model="draft.tags" placeholder="用逗号分隔，最多 10 个"></label>
        <div class="draft-actions"><button type="button" @click="copyDraft">{{ copied ? '已复制' : '复制全文' }}</button><button class="publish" type="button" @click="publish">带入社区发布</button></div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.draft-studio{display:grid;grid-template-columns:minmax(330px,.8fr) minmax(440px,1.2fr);min-height:650px;overflow:hidden;border:1px solid #dfe3dd;border-radius:10px;background:#fff}.draft-request{padding:36px;background:#f7f1e7}.draft-request>small,.draft-editor header small{color:#9f2d35;font-weight:900;letter-spacing:.14em}.draft-request h2{margin:7px 0 10px;font-size:30px}.draft-request>p{color:#6b716d;line-height:1.75}.draft-request label,.draft-editor label{display:grid;gap:7px;margin-top:23px;font-size:13px;font-weight:800}.draft-request textarea,.draft-editor textarea,.draft-editor input{box-sizing:border-box;width:100%;padding:12px;border:1px solid #d6d8d2;border-radius:8px;background:#fff;font:inherit;line-height:1.7}.draft-request label small,.draft-editor label small{text-align:right;color:#778079}.draft-generate{width:100%;min-height:50px;margin-top:18px;border:0;border-radius:7px;color:#fff;background:#9f2d35;font-weight:900}.draft-generate:disabled{opacity:.55}.draft-feedback{padding:10px 12px;color:#405249;background:#fff;border-radius:7px;font-size:12px}.draft-editor{padding:36px}.draft-empty{display:grid;place-items:center;align-content:center;height:100%;color:#718078;text-align:center}.draft-empty b{font-family:serif;font-size:34px}.draft-editor header{display:flex;justify-content:space-between;align-items:start}.draft-editor h3{margin:6px 0;font-size:25px}.draft-editor header>span{padding:5px 9px;color:#285a47;background:#e7f0eb;border-radius:999px;font-size:11px}.draft-editor label{margin-top:15px}.draft-actions{display:flex;justify-content:flex-end;gap:8px;margin-top:18px}.draft-actions button{min-height:43px;padding:0 18px;border:1px solid #ccd6d0;border-radius:7px;color:#285a47;background:#fff;font-weight:800}.draft-actions .publish{color:#fff;background:#285a47;border-color:#285a47}@media(max-width:900px){.draft-studio{grid-template-columns:1fr}}@media(max-width:560px){.draft-request,.draft-editor{padding:24px}.draft-actions{flex-direction:column}}
</style>
