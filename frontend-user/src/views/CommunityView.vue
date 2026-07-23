<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '@/services/api'
const posts = ref<any[]>([])
onMounted(async () => { posts.value = (await api.get('/community/posts')).data.data.items })
</script>
<template>
  <h1>共创社区</h1>
  <p class="muted">看见同学们如何重新表达岭南文化。</p>
  <div class="grid">
    <article v-for="post in posts" :key="post.id" class="card">
      <h3>{{ post.title }}</h3><p class="muted">{{ post.content }}</p>
      <small>赞 {{ post.like_count }} · 评论 {{ post.comment_count }}</small>
    </article>
  </div>
</template>

