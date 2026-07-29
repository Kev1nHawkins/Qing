<script setup lang="ts">
import { ref } from 'vue'
import CommunityIcon from '@/components/CommunityIcon.vue'
import type { CommunityComment, CommunityPost } from '@/types/community'

defineProps<{
  post: CommunityPost
  comments: CommunityComment[]
  loading: boolean
  submitting: boolean
  loggedIn: boolean
  error: string
}>()

const emit = defineEmits<{
  close: []
  submit: [content: string]
}>()

const content = ref('')

function submit() {
  if (!content.value.trim()) return
  emit('submit', content.value.trim())
  content.value = ''
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <div class="comments-backdrop" @click.self="$emit('close')">
    <section class="comments-panel" aria-labelledby="comments-title">
      <header>
        <div>
          <p>正在讨论</p>
          <h2 id="comments-title">{{ post.title }}</h2>
        </div>
        <button type="button" aria-label="关闭评论" @click="$emit('close')">×</button>
      </header>
      <div class="comments-list">
        <p v-if="loading" class="comments-state">正在加载评论…</p>
        <p v-else-if="error" class="comments-state comments-state--error">{{ error }}</p>
        <p v-else-if="!comments.length" class="comments-state">
          还没有评论，来写下第一条回应。
        </p>
        <article v-for="comment in comments" :key="comment.id">
          <div class="comment-avatar">
            {{ (comment.author_name || '同').slice(0, 1) }}
          </div>
          <div>
            <strong>{{ comment.author_name || `同学 ${comment.user_id}` }}</strong>
            <time>{{ formatDate(comment.created_at) }}</time>
            <p>{{ comment.content }}</p>
          </div>
        </article>
      </div>
      <form class="comment-form" @submit.prevent="submit">
        <textarea
          v-model="content"
          rows="3"
          maxlength="1000"
          :disabled="!loggedIn || submitting"
          :placeholder="loggedIn ? '写下你的回应…' : '登录后参与讨论'"
        />
        <button type="submit" :disabled="!loggedIn || submitting || !content.trim()">
          <CommunityIcon name="send" />
          {{ submitting ? '发送中…' : '发表评论' }}
        </button>
      </form>
    </section>
  </div>
</template>
