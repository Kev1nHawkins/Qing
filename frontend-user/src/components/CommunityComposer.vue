<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import CommunityIcon from '@/components/CommunityIcon.vue'
import MediaImage from '@/components/MediaImage.vue'
import { api } from '@/services/api'
import type { CommunityPostDraft, CreationOption, CultureOption, PublishPostPayload } from '@/types/community'

const props = defineProps<{
  cultures: CultureOption[]
  creations: CreationOption[]
  loggedIn: boolean
  submitting: boolean
  initialCreation?: CreationOption | null
  initialCreationError?: string
  initialDraft?: CommunityPostDraft | null
}>()
const emit = defineEmits<{ publish: [payload: PublishPostPayload] }>()
const form = reactive({ title: '', content: '', cultureItemId: '', creationId: '', coverImageUrl: '', tags: '' })
const localError = ref('')
const uploadingImage = ref(false)
const imageInput = ref<HTMLInputElement | null>(null)
const characterCount = computed(() => form.content.length)
const selectedCreation = computed(() => props.creations.find(item => String(item.id) === form.creationId) || null)

function applyCreation(creation: CreationOption | null) {
  if (!creation || creation.status !== 'SUCCESS') return
  form.creationId = String(creation.id)
  form.title = creation.title
  form.content = creation.description || `分享我的岭潮 AI 共创作品《${creation.title}》。`
  form.cultureItemId = creation.culture_item_id ? String(creation.culture_item_id) : ''
  form.coverImageUrl = ''
  form.tags = (creation.tags || []).join('，')
}

function applyDraft(draft: CommunityPostDraft | null) {
  if (!draft) return
  form.creationId = ''
  form.title = draft.title
  form.content = draft.content
  form.tags = draft.tags.join('，')
}

watch(() => props.initialCreation, creation => applyCreation(creation || null), { immediate: true })
watch(() => props.initialDraft, draft => applyDraft(draft || null), { immediate: true })
watch(
  () => form.creationId,
  (value, previous) => {
    if (value && value !== previous) applyCreation(props.creations.find(item => String(item.id) === value) || null)
  },
)

function submit() {
  localError.value = ''
  if (!props.loggedIn) return void (localError.value = '请先登录，再发布你的文化作品。')
  if (!form.title.trim() || !form.content.trim()) return void (localError.value = '请填写标题和正文。')
  if (uploadingImage.value) return void (localError.value = '图片仍在上传，请稍候。')
  if (selectedCreation.value?.status !== 'SUCCESS' && form.creationId) return void (localError.value = '只有生成成功的 AI 作品可以发布。')
  emit('publish', {
    title: form.title.trim(),
    content: form.content.trim(),
    culture_item_id: form.cultureItemId ? Number(form.cultureItemId) : null,
    creation_id: form.creationId ? Number(form.creationId) : null,
    cover_image_url: selectedCreation.value ? null : form.coverImageUrl.trim() || null,
    tags: form.tags.split(/[,，]/).map(tag => tag.trim()).filter(Boolean).slice(0, 10),
  })
}

async function selectImage(event: Event) {
  localError.value = ''
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!props.loggedIn) {
    localError.value = '请先登录，再添加帖子图片。'
    input.value = ''
    return
  }
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    localError.value = '仅支持 JPG、PNG 或 WebP 图片。'
    input.value = ''
    return
  }
  if (file.size > 8 * 1024 * 1024) {
    localError.value = '图片大小不能超过 8 MB。'
    input.value = ''
    return
  }
  uploadingImage.value = true
  try {
    const { data } = await api.post<{ data: { publicUrl: string } }>(
      '/community/uploads',
      file,
      { headers: { 'Content-Type': file.type } },
    )
    form.coverImageUrl = data.data.publicUrl
  } catch (event) {
    localError.value = (event as Error).message
    input.value = ''
  } finally {
    uploadingImage.value = false
  }
}

function removeImage() {
  form.coverImageUrl = ''
  if (imageInput.value) imageInput.value.value = ''
}

function reset() {
  Object.assign(form, { title: '', content: '', cultureItemId: '', creationId: '', coverImageUrl: '', tags: '' })
  if (imageInput.value) imageInput.value.value = ''
}
defineExpose({ reset })
</script>

<template>
  <aside class="community-composer">
    <div class="composer-title"><div><h2>发布作品</h2><p>为岭南文化写下新的注脚</p></div><CommunityIcon name="send" /></div>
    <p v-if="initialCreationError" class="composer-error">{{ initialCreationError }}</p>
    <form @submit.prevent="submit">
      <label><span>标题</span><input v-model="form.title" maxlength="120" placeholder="给这次共创取一个名字" /></label>
      <label><span>正文</span><textarea v-model="form.content" maxlength="5000" rows="6" placeholder="分享你的灵感、作品或校园瞬间…" /><small>{{ characterCount }}/5000</small></label>
      <div class="composer-row">
        <label><span>关联文化</span><select v-model="form.cultureItemId"><option value="">不关联</option><option v-for="culture in cultures" :key="culture.id" :value="culture.id">{{ culture.title }}</option></select></label>
        <label><span>关联 AI 作品</span><select v-model="form.creationId"><option value="">不关联 / 取消关联</option><option v-for="creation in creations" :key="creation.id" :value="creation.id">{{ creation.title }}</option></select></label>
      </div>
      <section v-if="selectedCreation" class="creation-preview">
        <MediaImage :src="selectedCreation.output_url" :alt="selectedCreation.title" />
        <div><strong>{{ selectedCreation.title }}</strong><span>我的创作作品</span><small>这张海报会作为帖子封面</small></div>
      </section>
      <section v-else class="composer-media">
        <span>添加图片（可选）</span>
        <div class="composer-media-actions">
          <label class="composer-upload-button">
            <input ref="imageInput" type="file" accept="image/jpeg,image/png,image/webp" @change="selectImage" />
            {{ uploadingImage ? '正在上传…' : form.coverImageUrl ? '更换图片' : '选择本地图片' }}
          </label>
          <button v-if="form.coverImageUrl" type="button" @click="removeImage">移除图片</button>
        </div>
        <div v-if="form.coverImageUrl" class="composer-image-preview">
          <MediaImage :src="form.coverImageUrl" alt="待发布帖子图片预览" />
        </div>
        <label><span>或填写图片地址</span><input v-model="form.coverImageUrl" type="url" placeholder="https://…" /></label>
        <small>支持 JPG、PNG、WebP，最大 8 MB；上传成功后再随帖子发布。</small>
      </section>
      <label><span>文化标签</span><input v-model="form.tags" placeholder="木棉，广彩，校园文化" /></label>
      <p v-if="localError" class="composer-error">{{ localError }}</p>
      <RouterLink v-if="!loggedIn" class="composer-login" to="/login">登录后参与共创</RouterLink>
      <button v-else class="composer-submit" type="submit" :disabled="submitting">{{ submitting ? '发布中…' : '发布' }}</button>
    </form>
  </aside>
</template>

<style scoped>
.community-composer{padding:24px;background:#fff;border:1px solid #ded8ce;border-radius:14px}.composer-title{display:flex;justify-content:space-between;align-items:start}.composer-title h2{margin:0}.composer-title p{margin:5px 0 18px;color:#756d65}.community-composer form,.community-composer label{display:grid;gap:7px}.community-composer form{gap:14px}.community-composer label span{font-size:12px;font-weight:800}.community-composer input,.community-composer textarea,.community-composer select{width:100%;box-sizing:border-box;padding:11px;border:1px solid #d9d1c6;border-radius:8px;background:#fff}.composer-row{display:grid;grid-template-columns:1fr 1fr;gap:10px}.creation-preview{display:grid;grid-template-columns:110px 1fr;gap:12px;padding:10px;background:#edf3ef;border-radius:9px}.creation-preview :deep(.media-image){height:130px;border-radius:6px}.creation-preview div{display:grid;align-content:center;gap:6px}.creation-preview span,.creation-preview small{color:#5f6c65;font-size:11px}.composer-error{margin:0;padding:10px;color:#8e2730;background:#f8e7e5;border-radius:7px}.composer-submit,.composer-login{display:grid;place-items:center;min-height:46px;border:0;border-radius:7px;color:#fff;background:#9f2d35;font-weight:800}.composer-login{background:#285a47}@media(max-width:560px){.composer-row{grid-template-columns:1fr}.creation-preview{grid-template-columns:90px 1fr}}
.composer-media{display:grid;gap:9px}.composer-media>span{font-size:12px;font-weight:800}.composer-media-actions{display:flex;gap:8px}.composer-upload-button,.composer-media-actions>button{display:grid;place-items:center;min-height:42px;padding:0 14px;border:1px solid #cfd7d1;border-radius:8px;color:#285a47;background:#edf3ef;font-weight:800;cursor:pointer}.composer-upload-button input{display:none}.composer-media-actions>button{color:#8e2730;background:#fff}.composer-image-preview{height:210px;overflow:hidden;border-radius:8px}.composer-media>small{color:#69736e;font-size:11px}
</style>
