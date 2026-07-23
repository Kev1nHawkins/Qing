<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/">岭潮共创</RouterLink>
      <span class="tagline">岭南文化 × 校园文化 × AI</span>
    </header>
    <main><RouterView /></main>
    <nav class="bottom-nav" aria-label="主要导航">
      <RouterLink to="/">探索</RouterLink>
      <RouterLink to="/cultures">文化</RouterLink>
      <RouterLink to="/routes">寻迹</RouterLink>
      <RouterLink to="/community">社区</RouterLink>
      <RouterLink to="/profile">我的</RouterLink>
    </nav>
  </div>
</template>

