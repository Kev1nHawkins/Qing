<script setup lang="ts">
import { ref } from 'vue'
withDefaults(defineProps<{ src?: string | null; alt: string; eager?: boolean }>(), { eager: false })
const failed = ref(false)
</script>
<template><div class="media-image" :class="{ failed }"><img v-if="src && !failed" :src="src" :alt="alt" :loading="eager ? 'eager' : 'lazy'" :fetchpriority="eager ? 'high' : 'auto'" @error="failed = true" /><div v-else class="image-fallback" aria-hidden="true"><span>岭</span><i>LINGNAN</i></div></div></template>
<style scoped>
.media-image{position:relative;width:100%;height:100%;overflow:hidden;background:#dce3dc}.media-image img{width:100%;height:100%;display:block;object-fit:cover}.image-fallback{height:100%;display:grid;place-content:center;text-align:center;color:#fff;background:#285d49}.image-fallback span{font-family:serif;font-size:44px}.image-fallback i{font-size:9px}
</style>
