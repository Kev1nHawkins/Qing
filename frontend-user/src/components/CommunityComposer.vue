<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import CommunityIcon from '@/components/CommunityIcon.vue'
import type {
  CreationOption,
  CultureOption,
  PublishPostPayload,
} from '@/types/community'

const props = defineProps<{
  cultures: CultureOption[]
  creations: CreationOption[]
  loggedIn: boolean
  submitting: boolean
}>()

const emit = defineEmits<{
  publish: [payload: PublishPostPayload]
}>()

const form = reactive({
  title: '',
  content: '',
  cultureItemId: '',
  creationId: '',
  coverImageUrl: '',
  tags: '',
})
const localError = ref('')
const characterCount = computed(() => form.content.length)

function submit() {
  localError.value = ''
  if (!props.loggedIn) {
    localError.value = '请先登录，再发布你的文化作品。'
    return
  }
  if (!form.title.trim() || !form.content.trim()) {
    localError.value = '请填写标题和正文。'
    return
  }
  emit('publish', {
    title: form.title.trim(),
    content: form.content.trim(),
    culture_item_id: form.cultureItemId ? Number(form.cultureItemId) : null,
    creation_id: form.creationId ? Number(form.creationId) : null,
    cover_image_url: form.coverImageUrl.trim() || null,
    tags: form.tags
      .split(/[,，]/)
      .map((tag) => tag.trim())
      .filter(Boolean)
      .slice(0, 10),
  })
}

function reset() {
  Object.assign(form, {
    title: '',
    content: '',
    cultureItemId: '',
    creationId: '',
    coverImageUrl: '',
    tags: '',
  })
}

defineExpose({ reset })
</script>

<template>
  <aside class="community-composer">
    <div class="composer-title">
      <div>
        <h2>发布作品</h2>
        <p>为岭南文化写下新的注脚</p>
      </div>
      <CommunityIcon name="send" />
    </div>

    <form @submit.prevent="submit">
      <label>
        <span>标题</span>
        <input
          v-model="form.title"
          maxlength="120"
          placeholder="给这次共创取一个名字"
        />
      </label>
      <label>
        <span>正文</span>
        <textarea
          v-model="form.content"
          maxlength="5000"
          rows="6"
          placeholder="分享你的灵感、作品或校园瞬间…"
        />
        <small>{{ characterCount }}/5000</small>
      </label>
      <div class="composer-row">
        <label>
          <span>关联文化</span>
          <select v-model="form.cultureItemId">
            <option value="">不关联</option>
            <option v-for="culture in cultures" :key="culture.id" :value="culture.id">
              {{ culture.title }}
            </option>
          </select>
        </label>
        <label>
          <span>关联 AI 作品</span>
          <select v-model="form.creationId">
            <option value="">不关联</option>
            <option v-for="creation in creations" :key="creation.id" :value="creation.id">
              {{ creation.title }}
            </option>
          </select>
        </label>
      </div>
      <label>
        <span>封面图片地址（可选）</span>
        <input v-model="form.coverImageUrl" type="url" placeholder="https://…" />
      </label>
      <label>
        <span>文化标签</span>
        <input v-model="form.tags" placeholder="木棉，广彩，校园文化" />
      </label>
      <p v-if="localError" class="composer-error">{{ localError }}</p>
      <RouterLink v-if="!loggedIn" class="composer-login" to="/login">
        登录后参与共创
      </RouterLink>
      <button v-else class="composer-submit" type="submit" :disabled="submitting">
        {{ submitting ? '发布中…' : '发布' }}
      </button>
    </form>
  </aside>
</template>
