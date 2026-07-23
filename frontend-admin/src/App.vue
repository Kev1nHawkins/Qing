<script setup lang="ts">
import { useRoute } from 'vue-router'
const route = useRoute()
</script>
<template>
  <RouterView v-if="route.path === '/login'" />
  <el-container v-else class="layout">
    <el-aside width="220px" class="sidebar">
      <div class="logo">岭潮共创<small>ADMIN CONSOLE</small></div>
      <el-menu router background-color="#19221f" text-color="#cdd8d2" active-text-color="#f1b35b">
        <el-menu-item index="/">数据看板</el-menu-item>
        <el-menu-item index="/cultures">文化内容</el-menu-item>
        <el-menu-item index="/routes">路线任务</el-menu-item>
        <el-menu-item index="/templates">AI 模板</el-menu-item>
        <el-menu-item index="/posts">社区审核</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">岭南文化与校园文化 AI 共创传播平台</el-header>
      <el-main><RouterView /></el-main>
    </el-container>
  </el-container>
</template>

