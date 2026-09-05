<script setup lang="ts">
import { ref, watch } from 'vue'
import FreeImageStudio from '@/components/FreeImageStudio.vue'
import PosterStudio from '@/components/PosterStudio.vue'
import PostDraftStudio from '@/components/PostDraftStudio.vue'
import type { CreationTemplate } from '@/types'

export type WorkbenchMode = 'template' | 'free-image' | 'post'
const modes: Array<{ key: WorkbenchMode; label: string; description: string }> = [
  { key: 'template', label: '模板海报', description: '组合文化元素快速创作' },
  { key: 'free-image', label: '自由图片', description: '用提示词生成任意画面' },
  { key: 'post', label: 'AI 推文', description: '生成可编辑社区文案' },
]
const props = defineProps<{ templates: CreationTemplate[]; initialMode?: WorkbenchMode; initialTemplateCode?: string; templateLoading?: boolean; templateError?: string }>()
const emit = defineEmits<{ login: []; modeChange: [mode: WorkbenchMode]; templateChange: [code: string]; retryTemplates: [] }>()
const activeMode = ref<WorkbenchMode>(props.initialMode || 'template')
const busy = ref(false)

watch(() => props.initialMode, value => { if (value && value !== activeMode.value && !busy.value) activeMode.value = value })
function selectMode(mode: WorkbenchMode) {
  if (busy.value || activeMode.value === mode) return
  activeMode.value = mode
  emit('modeChange', mode)
}
</script>

<template>
  <section class="creative-workbench">
    <nav class="workbench-tabs" aria-label="AI 共创模块">
      <button v-for="mode in modes" :key="mode.key" type="button" :class="{ active: activeMode === mode.key }" :disabled="busy" @click="selectMode(mode.key)"><strong>{{ mode.label }}</strong><span>{{ mode.description }}</span></button>
    </nav>
    <div v-if="activeMode === 'template' && (templateLoading || templateError || !templates.length)" class="template-state">
      <b>{{ templateLoading ? '正在加载共创模板…' : templateError ? '模板暂时没有加载成功' : '创作模板正在准备中' }}</b>
      <p v-if="templateError">{{ templateError }}</p>
      <button v-if="templateError" type="button" @click="emit('retryTemplates')">重新加载模板</button>
    </div>
    <PosterStudio v-else-if="activeMode === 'template'" :templates="templates" :initial-template-code="initialTemplateCode" @login="emit('login')" @template-change="emit('templateChange', $event)" @busy-change="busy = $event" />
    <FreeImageStudio v-else-if="activeMode === 'free-image'" @login="emit('login')" @busy-change="busy = $event" />
    <PostDraftStudio v-else @login="emit('login')" @busy-change="busy = $event" />
  </section>
</template>

<style scoped>
.creative-workbench{display:grid;gap:16px}.workbench-tabs{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:10px;background:#edf1ed;border:1px solid #dce3dd;border-radius:12px}.workbench-tabs button{display:grid;gap:4px;min-height:68px;padding:12px 16px;border:1px solid transparent;border-radius:8px;color:#58645e;background:transparent;text-align:left}.workbench-tabs button strong{font-size:16px}.workbench-tabs button span{font-size:10px}.workbench-tabs button.active{color:#fff;background:#285a47;box-shadow:0 8px 18px rgba(40,90,71,.18)}.workbench-tabs button:disabled{cursor:not-allowed;opacity:.7}.template-state{padding:42px;background:#fff;border:1px solid #dfe3dd;border-radius:10px;text-align:center}.template-state p{color:#8e2730}.template-state button{padding:9px 15px;border:0;border-radius:999px;color:#fff;background:#9f2d35}@media(max-width:600px){.workbench-tabs{display:flex;overflow-x:auto}.workbench-tabs button{flex:0 0 165px}}
</style>
