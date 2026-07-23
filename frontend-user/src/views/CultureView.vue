<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '@/services/api'

const items = ref<any[]>([])
const error = ref('')
onMounted(async () => {
  try {
    const { data } = await api.get('/cultures')
    items.value = data.data.items
  } catch (event) {
    error.value = (event as Error).message
  }
})
</script>
<template>
  <h1>文化探索</h1>
  <p class="muted">岭南文化、广州城市文化与广州大学校园记忆。</p>
  <p v-if="error" class="status">{{ error }}</p>
  <div class="grid">
    <article v-for="item in items" :key="item.id" class="card">
      <div class="eyebrow">{{ item.category }}</div><h3>{{ item.title }}</h3><p class="muted">{{ item.summary }}</p>
    </article>
  </div>
</template>

