<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import type { Location, RouteTask, TaskSubmission } from '@/types'

const props = defineProps<{
  task: RouteTask
  location?: Location
  completed?: boolean
  busy?: boolean
  tokenTitle?: string
}>()
const emit = defineEmits<{ close: []; submit: [submission: TaskSubmission] }>()

const answer = ref('')
const qrCode = ref('')
const photo = ref<File>()
const photoPreview = ref('')
const localError = ref('')
const locating = ref(false)
const evidenceConfirmed = ref(false)

const typeLabels: Record<string, string> = {
  CHECK_IN: '图片打卡',
  QUIZ: '文化问答',
  QR_CODE: '二维码打卡',
  SIMULATED_LOCATION: '位置打卡',
}
const isPhotoTask = computed(() => props.task.task_type === 'CHECK_IN')

watch(() => props.task.id, () => {
  answer.value = ''
  qrCode.value = ''
  photo.value = undefined
  evidenceConfirmed.value = false
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  photoPreview.value = ''
  localError.value = ''
}, { immediate: true })

onBeforeUnmount(() => {
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
})

function choosePhoto(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    localError.value = '请选择 JPG、PNG 或 WebP 图片'
    return
  }
  if (file.size > 8 * 1024 * 1024) {
    localError.value = '图片不能超过 8 MB'
    return
  }
  photo.value = file
  if (photoPreview.value) URL.revokeObjectURL(photoPreview.value)
  photoPreview.value = URL.createObjectURL(file)
  localError.value = ''
}

function submit() {
  localError.value = ''
  if (props.task.task_type === 'QUIZ') {
    if (!answer.value) {
      localError.value = '请选择答案'
      return
    }
    emit('submit', { payload: { answer: answer.value } })
    return
  }
  if (props.task.task_type === 'QR_CODE') {
    const value = qrCode.value.trim()
    if (!value) {
      localError.value = '请输入或扫描任务点二维码内容'
      return
    }
    emit('submit', { payload: { qr_code: value } })
    return
  }
  if (props.task.task_type === 'SIMULATED_LOCATION') {
    if (!navigator.geolocation) {
      localError.value = '当前浏览器不支持位置服务'
      return
    }
    locating.value = true
    navigator.geolocation.getCurrentPosition(
      position => {
        locating.value = false
        emit('submit', {
          payload: {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          },
        })
      },
      () => {
        locating.value = false
        localError.value = '无法获取当前位置，请检查浏览器定位权限'
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
    )
    return
  }
  if (props.task.task_type === 'CHECK_IN') {
    if (!photo.value) {
      localError.value = '请先上传现场照片'
      return
    }
    if (!evidenceConfirmed.value) {
      localError.value = '请确认照片是在当前任务地点拍摄的现场凭证'
      return
    }
    emit('submit', { payload: {}, photo: photo.value })
    return
  }
  localError.value = '暂不支持此任务类型'
}
</script>

<template>
  <aside class="task-panel" aria-live="polite">
    <header>
      <div>
        <span>{{ String(task.order_no).padStart(2, '0') }}</span>
        <div><small>{{ typeLabels[task.task_type] || '图片打卡' }}</small><h2>{{ task.title }}</h2></div>
      </div>
      <button type="button" aria-label="关闭任务详情" @click="emit('close')">×</button>
    </header>
    <div class="task-location"><b>{{ location?.name || '校园任务点' }}</b><span>{{ location?.address }}</span></div>
    <p class="task-description">{{ task.description }}</p>
    <div class="task-reward"><b>+{{ task.points }}</b><span>完成后获得文化积分</span></div>
    <div v-if="tokenTitle" class="token-preview"><span>令</span><div><small>完成后点亮文化令牌</small><b>{{ tokenTitle }}</b></div></div>

    <div v-if="completed" class="task-completed"><span>✓</span><div><b>任务已完成</b><small>重复提交不会重复增加积分</small></div></div>

    <section v-else-if="task.task_type === 'QUIZ'" class="task-action">
      <h3>{{ task.question }}</h3>
      <div class="quiz-options">
        <button v-for="option in task.options" :key="option" type="button" :class="{ selected: answer === option }" @click="answer = option">{{ option }}</button>
      </div>
    </section>

    <section v-else-if="isPhotoTask" class="task-action">
      <h3>{{ task.question || '请上传任务点现场照片完成图片打卡' }}</h3>
      <p>拍摄任务点、校园文化细节或现场观察成果，支持 JPG、PNG、WebP，最大 8 MB。</p>
      <label class="photo-uploader" :class="{ ready: photoPreview }">
        <img v-if="photoPreview" :src="photoPreview" alt="待提交的现场打卡照片" />
        <span v-else>＋<small>拍照或选择图片</small></span>
        <input type="file" accept="image/jpeg,image/png,image/webp" capture="environment" @change="choosePhoto" />
      </label>
      <label class="evidence-confirm">
        <input v-model="evidenceConfirmed" type="checkbox" />
        <span>我确认这是本人在“{{ location?.name || '当前任务点' }}”拍摄的现场照片。服务器将校验图片格式、尺寸、完整性与用户归属。</span>
      </label>
    </section>

    <section v-else-if="task.task_type === 'QR_CODE'" class="task-action">
      <h3>{{ task.question || '请输入任务点二维码中的校验内容' }}</h3>
      <p>二维码内容仅提交给后端校验，页面不会展示正确答案。</p>
      <input v-model="qrCode" class="task-text-input" maxlength="120" autocomplete="off" placeholder="二维码内容" />
    </section>

    <section v-else-if="task.task_type === 'SIMULATED_LOCATION'" class="task-action">
      <h3>{{ task.question || '在任务点附近完成位置打卡' }}</h3>
      <p>提交时获取一次当前位置，由后端按照 {{ task.radius_meters }} 米范围校验。</p>
    </section>

    <p v-if="localError" class="task-error">{{ localError }}</p>
    <button v-if="!completed" class="task-submit" type="button" :disabled="busy || locating" @click="submit">{{ locating ? '正在定位…' : busy ? '正在提交…' : '提交任务' }}</button>
  </aside>
</template>

<style scoped>
.task-panel{position:fixed;z-index:30;right:24px;top:92px;width:min(420px,calc(100vw - 32px));max-height:calc(100vh - 116px);overflow:auto;padding:24px;background:#fff;border:1px solid #dfe3dd;border-radius:16px;box-shadow:0 28px 75px rgba(22,47,38,.28)}.task-panel>header{display:flex;align-items:flex-start;justify-content:space-between;gap:14px}.task-panel>header>div{display:flex;align-items:center;gap:13px}.task-panel>header>div>span{display:grid;place-items:center;width:45px;height:45px;color:#fff;background:#9f2d35;border-radius:50%;font-family:serif;font-size:18px}.task-panel h2{margin:2px 0 0;font-size:24px}.task-panel header small{color:#9f2d35;font-size:10px;font-weight:800}.task-panel>header>button{padding:0;border:0;background:none;color:#78827d;font-size:28px}.task-location{display:grid;gap:3px;margin:20px 0 0;padding:13px 15px;background:#edf3ef;border-radius:9px}.task-location span{color:#64716a;font-size:12px}.task-description{color:#5e6963;line-height:1.75}.task-reward{display:flex;align-items:baseline;gap:10px;padding:12px 0;border-top:1px solid #e5e8e4;border-bottom:1px solid #e5e8e4}.task-reward b{color:#9f2d35;font-size:25px}.task-reward span{color:#68736d;font-size:12px}.task-action{display:grid;gap:12px;margin-top:18px}.task-action h3{margin:0;font-size:17px}.task-action p{margin:0;color:#68736d;font-size:12px;line-height:1.65}.task-text-input{min-height:44px;padding:0 12px;border:1px solid #cfd8d2;border-radius:8px;font:inherit}.quiz-options{display:grid;gap:8px}.quiz-options button{min-height:42px;padding:0 13px;border:1px solid #d7ddd8;border-radius:8px;background:#fff;text-align:left}.quiz-options button.selected{color:#fff;background:#285a47;border-color:#285a47}.photo-uploader input{display:none}.photo-uploader{display:grid;min-height:190px;place-items:center;overflow:hidden;border:2px dashed #bdd0c5;border-radius:10px;background:#f4f8f5;cursor:pointer}.photo-uploader>span{display:grid;justify-items:center;color:#9f2d35;font-size:40px}.photo-uploader small{color:#56645d;font-size:12px}.photo-uploader img{width:100%;height:220px;object-fit:cover}.task-error{padding:10px 12px;color:#a6222b;background:#fff0f0;border-radius:7px;font-size:12px}.task-submit{width:100%;min-height:47px;margin-top:18px;border:0;border-radius:8px;color:#fff;background:#9f2d35;font-weight:800}.task-submit:disabled{opacity:.6}.task-completed{display:flex;align-items:center;gap:12px;margin-top:18px;padding:15px;color:#fff;background:#285a47;border-radius:9px}.task-completed>span{display:grid;place-items:center;width:34px;height:34px;color:#285a47;background:#e2bf72;border-radius:50%;font-weight:900}.task-completed div{display:grid}.task-completed small{color:#c5d9cf}@media(max-width:620px){.task-panel{right:8px;left:8px;bottom:8px;top:auto;width:auto;max-height:78vh}}
.token-preview{display:flex;align-items:center;gap:10px;margin-top:12px;padding:11px 13px;color:#fff;background:linear-gradient(120deg,#285a47,#1e4437);border-radius:9px}.token-preview>span{display:grid;place-items:center;width:36px;height:36px;color:#704712;background:#e9c777;border:3px double #fff5d9;border-radius:50%;font-family:serif}.token-preview>div{display:grid}.token-preview small{color:#cce0d6;font-size:9px}.evidence-confirm{display:grid;grid-template-columns:auto 1fr;align-items:start;gap:9px;padding:11px 12px;background:#fff8e9;border:1px solid #ead7ae;border-radius:8px;color:#665c4b;font-size:11px;line-height:1.6}.evidence-confirm input{margin-top:3px}
</style>
