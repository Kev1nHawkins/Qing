<script setup lang="ts">
import { computed } from 'vue'
import CommunityIcon from '@/components/CommunityIcon.vue'
import MediaImage from '@/components/MediaImage.vue'
import type { CommunityPost } from '@/types/community'

const props = defineProps<{
  post: CommunityPost
  featured?: boolean
  liked?: boolean
  favorited?: boolean
  busy?: boolean
}>()

const mediaUrls = computed(() => {
  if (props.post.image_urls?.length) return props.post.image_urls.slice(0, 6)
  const fallback = props.post.cover_image_url || props.post.creation_preview_url
  return fallback ? [fallback] : []
})

defineEmits<{
  like: [post: CommunityPost]
  favorite: [post: CommunityPost]
  comments: [post: CommunityPost]
}>()

function formatTime(value: string) {
  const date = new Date(value)
  const diff = Date.now() - date.getTime()
  if (diff < 3_600_000) return `${Math.max(1, Math.floor(diff / 60_000))} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
  }).format(date)
}
</script>

<template>
  <article class="community-post" :class="{ 'community-post--featured': featured }">
    <header class="post-author">
      <div class="post-avatar" aria-hidden="true">
        <img
          v-if="post.author_avatar_url"
          :src="post.author_avatar_url"
          :alt="post.author_name || '作者头像'"
        />
        <span v-else>{{ (post.author_name || '共').slice(0, 1) }}</span>
      </div>
      <div>
        <strong>{{ post.author_name || `共创者 ${post.author_id}` }}</strong>
        <p>
          {{ formatTime(post.created_at) }}
          <template v-if="post.culture_item_title">
            · {{ post.culture_item_title }}
          </template>
        </p>
      </div>
      <span v-if="post.creation_id" class="post-kind">
        <CommunityIcon name="sparkles" /> AI 作品
      </span>
      <span v-else-if="post.culture_item_id" class="post-kind">
        <CommunityIcon name="map" /> 文化寻迹
      </span>
      <span v-else class="post-kind">
        <CommunityIcon name="map" /> 校园打卡
      </span>
    </header>

    <div class="post-body" :class="{ 'post-body--with-media': featured && mediaUrls.length }">
      <div v-if="mediaUrls.length" class="post-media-grid" :class="`post-media-grid--${Math.min(mediaUrls.length, 4)}`">
        <MediaImage
          v-for="(url, index) in mediaUrls"
          :key="url"
          class="post-cover"
          :src="url"
          :alt="`${post.title} · 图片 ${index + 1}`"
        />
      </div>
      <div class="post-copy">
        <h2>{{ post.title }}</h2>
        <p>{{ post.content }}</p>
        <div v-if="post.tags?.length" class="post-tags" aria-label="文化标签">
          <span v-for="tag in post.tags" :key="tag"># {{ tag }}</span>
        </div>
        <div v-if="post.creation_title" class="linked-creation">
          <CommunityIcon name="sparkles" />
          关联 AI 作品《{{ post.creation_title }}》
        </div>
      </div>
    </div>

    <footer class="post-actions">
      <button
        type="button"
        :class="{ active: liked }"
        :disabled="busy"
        :aria-pressed="liked"
        @click="$emit('like', post)"
      >
        <CommunityIcon name="heart" />
        <span>点赞</span>
        <strong>{{ post.like_count }}</strong>
      </button>
      <button type="button" @click="$emit('comments', post)">
        <CommunityIcon name="comment" />
        <span>评论</span>
        <strong>{{ post.comment_count }}</strong>
      </button>
      <button
        type="button"
        :class="{ active: favorited }"
        :disabled="busy"
        :aria-pressed="favorited"
        @click="$emit('favorite', post)"
      >
        <CommunityIcon name="bookmark" />
        <span>收藏</span>
        <strong>{{ post.favorite_count }}</strong>
      </button>
    </footer>
  </article>
</template>
