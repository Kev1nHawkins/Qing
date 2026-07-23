<script setup lang="ts">
defineProps<{ title: string; note: string }>()
</script>
<template>
  <h1 class="page-title">{{ title }}</h1>
  <el-empty :description="note" />
</template>

