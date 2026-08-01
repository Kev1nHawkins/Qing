<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { CultureRoute, Location, RouteTask } from '@/types'

const props = defineProps<{
  route: CultureRoute
  locations: Location[]
  completedTaskIds: number[]
  activeTaskId?: number
}>()
const emit = defineEmits<{ selectTask: [task: RouteTask] }>()

const mapElement = ref<HTMLElement | null>(null)
const mapMode = ref<'loading' | 'amap' | 'fallback'>('loading')
const mapMessage = ref('正在加载校园地图')
let mapInstance: any = null
let markers: any[] = []
let polyline: any = null

const locationMap = computed(() => new Map(props.locations.map(item => [item.id, item])))
const tasks = computed(() => props.route.tasks || [])
const fallbackPoints = computed(() => {
  const points = tasks.value.map(task => ({
    task,
    latitude: Number(task.latitude ?? locationMap.value.get(task.location_id)?.latitude),
    longitude: Number(task.longitude ?? locationMap.value.get(task.location_id)?.longitude),
  })).filter(item => Number.isFinite(item.latitude) && Number.isFinite(item.longitude))
  if (!points.length) return []
  const latitudes = points.map(item => item.latitude)
  const longitudes = points.map(item => item.longitude)
  const minLat = Math.min(...latitudes)
  const maxLat = Math.max(...latitudes)
  const minLng = Math.min(...longitudes)
  const maxLng = Math.max(...longitudes)
  return points.map(item => ({
    ...item,
    x: 10 + ((item.longitude - minLng) / (maxLng - minLng || 1)) * 80,
    y: 86 - ((item.latitude - minLat) / (maxLat - minLat || 1)) * 72,
  }))
})
const polylinePoints = computed(() => fallbackPoints.value.map(item => `${item.x},${item.y}`).join(' '))

function loadAmap(): Promise<any> {
  const key = import.meta.env.VITE_AMAP_KEY?.trim()
  if (!key) return Promise.reject(new Error('未配置高德地图浏览器端 Key'))
  const securityCode = import.meta.env.VITE_AMAP_SECURITY_CODE?.trim()
  if (securityCode) (window as any)._AMapSecurityConfig = { securityJsCode: securityCode }
  if ((window as any).AMap) return Promise.resolve((window as any).AMap)
  return new Promise((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[data-lingchao-amap]')
    if (existing) {
      existing.addEventListener('load', () => resolve((window as any).AMap), { once: true })
      existing.addEventListener('error', () => reject(new Error('高德地图脚本加载失败')), { once: true })
      return
    }
    const script = document.createElement('script')
    script.dataset.lingchaoAmap = 'true'
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(key)}`
    script.async = true
    script.onload = () => resolve((window as any).AMap)
    script.onerror = () => reject(new Error('高德地图脚本加载失败'))
    document.head.appendChild(script)
  })
}

function clearAmap() {
  markers.forEach(marker => marker.setMap?.(null))
  markers = []
  polyline?.setMap?.(null)
  polyline = null
}

function renderAmap() {
  const AMap = (window as any).AMap
  if (!AMap || !mapElement.value || !mapInstance) return
  clearAmap()
  const path: number[][] = []
  tasks.value.forEach(task => {
    const location = locationMap.value.get(task.location_id)
    const latitude = Number(task.latitude ?? location?.latitude)
    const longitude = Number(task.longitude ?? location?.longitude)
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) return
    const point = [longitude, latitude]
    path.push(point)
    const button = document.createElement('button')
    button.type = 'button'
    button.className = [
      'campus-map-marker',
      props.completedTaskIds.includes(task.id) ? 'completed' : '',
      props.activeTaskId === task.id ? 'active' : '',
    ].filter(Boolean).join(' ')
    button.textContent = String(task.order_no).padStart(2, '0')
    button.setAttribute('aria-label', `任务点 ${task.order_no}：${task.title}`)
    button.addEventListener('click', () => emit('selectTask', task))
    const marker = new AMap.Marker({
      position: point,
      content: button,
      offset: new AMap.Pixel(-18, -18),
      title: task.title,
    })
    marker.setMap(mapInstance)
    markers.push(marker)
  })
  if (path.length > 1) {
    polyline = new AMap.Polyline({
      path,
      strokeColor: '#9f2d35',
      strokeWeight: 6,
      strokeOpacity: 0.9,
      lineJoin: 'round',
      showDir: true,
    })
    polyline.setMap(mapInstance)
  }
  if (markers.length) mapInstance.setFitView(markers, false, [56, 56, 56, 56])
}

async function initializeMap() {
  try {
    const AMap = await loadAmap()
    if (!mapElement.value) return
    mapInstance = new AMap.Map(mapElement.value, {
      zoom: 16,
      viewMode: '2D',
      mapStyle: 'amap://styles/whitesmoke',
    })
    mapMode.value = 'amap'
    mapMessage.value = '高德地图实时校园路线'
    renderAmap()
  } catch (event) {
    mapMode.value = 'fallback'
    mapMessage.value = `${(event as Error).message}，已切换为离线校园示意图`
  }
}

watch(
  () => [props.route.id, props.completedTaskIds.join(','), props.activeTaskId, props.locations.length],
  () => {
    if (mapMode.value === 'amap') renderAmap()
  },
)
onMounted(initializeMap)
onBeforeUnmount(() => {
  clearAmap()
  mapInstance?.destroy?.()
})
</script>

<template>
  <section class="campus-map-shell" aria-label="校园文化地图">
    <header>
      <div><span class="map-status-dot" :class="mapMode" /><b>{{ mapMessage }}</b></div>
      <small>{{ route.tasks?.length || 0 }} 个任务节点 · 点击标记查看任务</small>
    </header>
    <div v-show="mapMode === 'amap'" ref="mapElement" class="campus-amap" />
    <div v-if="mapMode !== 'amap'" class="campus-map-fallback">
      <div class="campus-map-grid" aria-hidden="true" />
      <span class="campus-map-water" aria-hidden="true">中心湖</span>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <polyline :points="polylinePoints" />
      </svg>
      <button
        v-for="point in fallbackPoints"
        :key="point.task.id"
        type="button"
        class="fallback-marker"
        :class="{ completed: completedTaskIds.includes(point.task.id), active: activeTaskId === point.task.id }"
        :style="{ left: `${point.x}%`, top: `${point.y}%` }"
        :aria-label="`任务点 ${point.task.order_no}：${point.task.title}`"
        @click="emit('selectTask', point.task)"
      >
        <span>{{ String(point.task.order_no).padStart(2, '0') }}</span>
        <small>{{ point.task.title }}</small>
      </button>
    </div>
  </section>
</template>

<style scoped>
.campus-map-shell{overflow:hidden;border:1px solid #dfe3dd;border-radius:14px;background:#fff;box-shadow:0 18px 45px rgba(31,57,46,.1)}.campus-map-shell>header{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:15px 18px;border-bottom:1px solid #e3e7e2}.campus-map-shell>header>div{display:flex;align-items:center;gap:9px}.campus-map-shell>header small{color:#68736d}.map-status-dot{width:9px;height:9px;border-radius:50%;background:#c89233}.map-status-dot.amap{background:#2b8a60;box-shadow:0 0 0 5px rgba(43,138,96,.12)}.campus-amap,.campus-map-fallback{height:520px}.campus-map-fallback{position:relative;overflow:hidden;background:linear-gradient(145deg,#e8eee8,#f8f1df)}.campus-map-grid{position:absolute;inset:-30%;transform:rotate(-8deg);background-image:linear-gradient(rgba(40,90,71,.08) 1px,transparent 1px),linear-gradient(90deg,rgba(40,90,71,.08) 1px,transparent 1px);background-size:55px 55px}.campus-map-fallback:before,.campus-map-fallback:after{content:"";position:absolute;background:#d4dccf;border:9px solid rgba(255,255,255,.72);transform:rotate(-14deg)}.campus-map-fallback:before{left:-8%;top:14%;width:120%;height:38px}.campus-map-fallback:after{left:18%;top:-20%;width:34px;height:140%}.campus-map-water{position:absolute;right:8%;bottom:10%;display:grid;place-items:center;width:190px;height:130px;color:#5b8a85;background:#cce2df;border:2px solid rgba(72,130,123,.35);border-radius:55% 45% 58% 42%;font-family:serif;font-size:19px}.campus-map-fallback svg{position:absolute;inset:0;width:100%;height:100%;overflow:visible}.campus-map-fallback polyline{fill:none;stroke:#9f2d35;stroke-width:1.1;stroke-dasharray:2 1;vector-effect:non-scaling-stroke}.fallback-marker{position:absolute;z-index:2;display:grid;justify-items:center;gap:5px;transform:translate(-50%,-50%);padding:0;border:0;background:none;color:#263d34}.fallback-marker>span{display:grid;place-items:center;width:38px;height:38px;color:#fff;background:#285a47;border:4px solid #fff;border-radius:50%;box-shadow:0 5px 15px rgba(31,57,46,.26);font-size:11px;font-weight:900}.fallback-marker small{max-width:105px;padding:4px 7px;background:rgba(255,255,255,.92);border-radius:999px;font-size:10px;white-space:nowrap}.fallback-marker.completed>span{background:#9f2d35}.fallback-marker.completed>span:after{content:"✓";position:absolute;margin:25px 0 0 25px;display:grid;place-items:center;width:17px;height:17px;background:#e4b755;border:2px solid #fff;border-radius:50%;font-size:9px}.fallback-marker.active>span{box-shadow:0 0 0 7px rgba(159,45,53,.2),0 6px 16px rgba(31,57,46,.28)}:global(.campus-map-marker){display:grid;place-items:center;width:36px;height:36px;padding:0;color:#fff;background:#285a47;border:4px solid #fff;border-radius:50%;box-shadow:0 5px 15px rgba(31,57,46,.28);font-size:11px;font-weight:900}:global(.campus-map-marker.completed){background:#9f2d35}:global(.campus-map-marker.active){box-shadow:0 0 0 7px rgba(159,45,53,.22),0 5px 15px rgba(31,57,46,.28)}@media(max-width:700px){.campus-map-shell>header{align-items:flex-start;flex-direction:column;gap:5px}.campus-amap,.campus-map-fallback{height:430px}.fallback-marker small{display:none}.campus-map-water{width:130px;height:90px}}
</style>
