<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import CommunityCommentsPanel from '@/components/CommunityCommentsPanel.vue'
import CommunityComposer from '@/components/CommunityComposer.vue'
import CommunityPostCard from '@/components/CommunityPostCard.vue'
import { api } from '@/services/api'
import type {
  CommunityComment,
  CommunityPostDraft,
  CommunityPost,
  CreationOption,
  CultureOption,
  PublishPostPayload,
} from '@/types/community'
import '@/community/community.css'

type FilterKey = 'ALL' | 'AI' | 'CAMPUS' | 'CULTURE'

const route = useRoute()
const posts = ref<CommunityPost[]>([])
const cultures = ref<CultureOption[]>([])
const creations = ref<CreationOption[]>([])
const initialCreation = ref<CreationOption | null>(null)
const initialCreationError = ref('')
const initialDraft = ref<CommunityPostDraft | null>(null)
const loading = ref(true)
const error = ref('')
const notice = ref('')
const activeFilter = ref<FilterKey>('ALL')
const submittingPost = ref(false)
const composer = ref<InstanceType<typeof CommunityComposer> | null>(null)
const liked = reactive<Record<number, boolean>>({})
const favorited = reactive<Record<number, boolean>>({})
const busyPosts = reactive<Record<number, boolean>>({})

const selectedPost = ref<CommunityPost | null>(null)
const comments = ref<CommunityComment[]>([])
const commentsLoading = ref(false)
const commentsSubmitting = ref(false)
const commentsError = ref('')

const loggedIn = computed(() => Boolean(localStorage.getItem('accessToken')))
const initialCreationId = computed(() => {
  const value = Number(route.query.creationId)
  return Number.isInteger(value) && value > 0 ? value : null
})
const filters: Array<{ key: FilterKey; label: string }> = [
  { key: 'ALL', label: '全部' },
  { key: 'AI', label: 'AI作品' },
  { key: 'CAMPUS', label: '校园打卡' },
  { key: 'CULTURE', label: '文化寻迹' },
]

function consumePostDraft() {
  if (route.query.draft !== 'ai') return
  const key = 'lingchao.community.aiDraft.v1'
  const raw = sessionStorage.getItem(key)
  sessionStorage.removeItem(key)
  if (!raw) return
  try {
    const value = JSON.parse(raw) as Partial<CommunityPostDraft>
    if (
      value.version !== 1
      || typeof value.title !== 'string'
      || !value.title.trim()
      || value.title.length > 120
      || typeof value.content !== 'string'
      || !value.content.trim()
      || value.content.length > 5000
      || !Array.isArray(value.tags)
      || value.tags.length > 10
      || value.tags.some(tag => typeof tag !== 'string')
    ) return
    initialDraft.value = value as CommunityPostDraft
  } catch {
    initialDraft.value = null
  }
}

async function loadPosts() {
  loading.value = true
  error.value = ''
  try {
    const params: Record<string, string | number> = { pageSize: 20 }
    if (activeFilter.value !== 'ALL') params.contentType = activeFilter.value
    const { data } = await api.get('/community/posts', { params })
    posts.value = data.data.items
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    loading.value = false
  }
}

async function loadReferenceData() {
  try {
    const { data } = await api.get('/cultures', { params: { pageSize: 100 } })
    cultures.value = data.data.items
  } catch {
    cultures.value = []
  }
  if (!loggedIn.value) return
  try {
    const { data } = await api.get('/creations', { params: { pageSize: 100 } })
    creations.value = data.data.items.filter(
      (item: CreationOption) => item.status === 'SUCCESS',
    )
  } catch {
    creations.value = []
  }
  if (!initialCreationId.value) return
  try {
    const { data } = await api.get(`/creations/${initialCreationId.value}`)
    const requested = data.data as CreationOption
    if (requested.status !== 'SUCCESS') {
      initialCreationError.value = '该 AI 作品尚未生成成功，暂时不能关联发布。'
      return
    }
    initialCreation.value = requested
    if (!creations.value.some(item => item.id === requested.id)) creations.value.unshift(requested)
  } catch (event) {
    initialCreationError.value = `无法关联指定 AI 作品：${(event as Error).message}`
  }
}

async function selectFilter(key: FilterKey) {
  activeFilter.value = key
  await loadPosts()
}

async function publish(payload: PublishPostPayload) {
  submittingPost.value = true
  notice.value = ''
  try {
    const { data } = await api.post('/community/posts', payload)
    notice.value = '作品已发布，正在与更多同学相遇。'
    composer.value?.reset()
    if (activeFilter.value === 'ALL') posts.value.unshift(data.data)
    else await loadPosts()
  } catch (event) {
    notice.value = (event as Error).message
  } finally {
    submittingPost.value = false
  }
}

async function likePost(post: CommunityPost) {
  busyPosts[post.id] = true
  try {
    const { data } = await api.post(`/community/posts/${post.id}/like`)
    post.like_count = data.data.likeCount
    liked[post.id] = true
    notice.value = data.data.alreadyLiked ? '已经点过赞啦，计数保持不变。' : '已点赞。'
  } catch (event) {
    notice.value = (event as Error).message
  } finally {
    busyPosts[post.id] = false
  }
}

async function favoritePost(post: CommunityPost) {
  busyPosts[post.id] = true
  try {
    const { data } = await api.post(`/community/posts/${post.id}/favorite`)
    post.favorite_count = data.data.favoriteCount
    favorited[post.id] = data.data.favorited
    notice.value = data.data.favorited ? '已收藏。' : '已取消收藏。'
  } catch (event) {
    notice.value = (event as Error).message
  } finally {
    busyPosts[post.id] = false
  }
}

async function openComments(post: CommunityPost) {
  selectedPost.value = post
  comments.value = []
  commentsError.value = ''
  commentsLoading.value = true
  try {
    const { data } = await api.get(`/community/posts/${post.id}/comments`)
    comments.value = data.data
  } catch (event) {
    commentsError.value = (event as Error).message
  } finally {
    commentsLoading.value = false
  }
}

async function submitComment(content: string) {
  if (!selectedPost.value) return
  commentsSubmitting.value = true
  commentsError.value = ''
  try {
    const { data } = await api.post(
      `/community/posts/${selectedPost.value.id}/comments`,
      { content, parent_id: null },
    )
    comments.value.push(data.data)
    selectedPost.value.comment_count += 1
  } catch (event) {
    commentsError.value = (event as Error).message
  } finally {
    commentsSubmitting.value = false
  }
}

onMounted(async () => {
  consumePostDraft()
  await Promise.all([loadPosts(), loadReferenceData()])
})
</script>

<template>
  <div class="community-page">
    <header class="community-heading">
      <div>
        <h1>共创社区</h1>
        <p>来看看大家的岭南灵感，也分享你的校园故事吧！🌺</p>
      </div>
      <a class="community-publish-link" href="#community-composer">分享我的作品</a>
    </header>

    <nav class="community-filters" aria-label="内容筛选">
      <button
        v-for="filter in filters"
        :key="filter.key"
        type="button"
        :class="{ active: activeFilter === filter.key }"
        @click="selectFilter(filter.key)"
      >
        {{ filter.label }}
      </button>
    </nav>

    <p v-if="notice" class="community-notice" role="status">{{ notice }}</p>

    <div class="community-layout">
      <section class="community-feed" aria-live="polite">
        <div v-if="loading" class="community-state">
          <span class="community-loader" />正在寻找新鲜灵感…
        </div>
        <div v-else-if="error" class="community-state community-state--error">
          <strong>信息流暂时没有加载成功</strong>
          <p>{{ error }}</p>
          <button type="button" @click="loadPosts">重新加载</button>
        </div>
        <div v-else-if="!posts.length" class="community-state">
          <strong>这里还在等你的第一份作品呢！</strong>
          <p>换个分类逛逛，或者发布一段你的校园文化记录吧。</p>
        </div>
        <template v-else>
          <CommunityPostCard
            v-for="(post, index) in posts"
            :key="post.id"
            :post="post"
            :featured="index === 0"
            :liked="liked[post.id]"
            :favorited="favorited[post.id]"
            :busy="busyPosts[post.id]"
            @like="likePost"
            @favorite="favoritePost"
            @comments="openComments"
          />
        </template>
      </section>

      <div id="community-composer" class="community-rail">
        <CommunityComposer
          ref="composer"
          :cultures="cultures"
          :creations="creations"
          :initial-creation="initialCreation"
          :initial-creation-error="initialCreationError"
          :initial-draft="initialDraft"
          :logged-in="loggedIn"
          :submitting="submittingPost"
          @publish="publish"
        />
        <section class="culture-tag-rail">
          <h2>文化标签</h2>
          <div>
            <span>木棉</span><span>醒狮文化</span><span>广彩</span>
            <span>粤剧</span><span>校园记忆</span><span>非遗传承</span>
          </div>
        </section>
      </div>
    </div>

    <CommunityCommentsPanel
      v-if="selectedPost"
      :post="selectedPost"
      :comments="comments"
      :loading="commentsLoading"
      :submitting="commentsSubmitting"
      :logged-in="loggedIn"
      :error="commentsError"
      @close="selectedPost = null"
      @submit="submitComment"
    />
  </div>
</template>
