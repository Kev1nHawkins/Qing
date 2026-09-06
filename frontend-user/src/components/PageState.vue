<script setup lang="ts">
defineProps<{ loading?: boolean; error?: string; empty?: boolean; emptyText?: string }>()
const emit = defineEmits<{ retry: [] }>()
</script>
<template>
  <div v-if="loading" class="page-state" role="status"><i class="state-spinner" aria-hidden="true" /><strong>正在连接岭潮内容库</strong><span>文化故事正在汇入页面</span></div>
  <div v-else-if="error" class="page-state error-state" role="alert"><strong>内容暂时没有抵达</strong><span>{{ error }}</span><button class="state-button" type="button" @click="emit('retry')">重新加载</button></div>
  <div v-else-if="empty" class="page-state"><strong>{{ emptyText || '这里还没有内容' }}</strong><span>稍后再来看看新的文化故事</span></div>
</template>
<style scoped>
.page-state{min-height:220px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:28px;text-align:center;color:#67716b;background:#fff;border:1px dashed #dce2dc;border-radius:8px}.page-state strong{color:#202522}.state-spinner{width:24px;height:24px;border:3px solid #dde5df;border-top-color:#a72f37;border-radius:50%;animation:spin 1s linear infinite}.state-button{min-height:40px;padding:0 14px;color:#fff;background:#a72f37;border:0;border-radius:6px;font-weight:700;cursor:pointer}@keyframes spin{to{transform:rotate(360deg)}}
</style>
