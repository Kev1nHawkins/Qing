<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import CulturalTokenReveal from '@/components/CulturalTokenReveal.vue'
import CampusMap from '@/views/map/CampusMap.vue'
import PointsMall from '@/views/points/PointsMall.vue'
import TaskPanel from '@/views/task/TaskPanel.vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'
import {
  culturalTokenForTask,
  type CulturalToken,
} from '@/views/route/culturalTokens'
import { demoRouteFallback } from '@/views/route/demoFallback'
import type {
  Badge,
  CultureRoute,
  Location,
  PageData,
  PointRecord,
  RouteProgress,
  RouteTask,
  ShopRedeemResult,
  TaskCompleteResult,
  TaskSubmission,
  UserBadge,
} from '@/types'

const router = useRouter()
const auth = useAuthStore()

const routes = ref<CultureRoute[]>([])
const locations = ref<Location[]>([])
const badges = ref<Badge[]>([])
const ownedBadges = ref<UserBadge[]>([])
const pointsTotal = ref(0)
const pointRecords = ref<PointRecord[]>([])
const progress = ref<Record<number, RouteProgress>>({})
const selectedRouteId = ref<number>()
const activeTaskId = ref<number>()
const loading = ref(true)
const busy = ref(false)
const error = ref('')
const toast = ref('')
const unlockedBadge = ref<Badge>()
const unlockedToken = ref<{ token: CulturalToken; points: number }>()
const evidenceUrls = ref<Record<number, string>>({})
const serviceFallback = ref(false)

const isLoggedIn = computed(() => auth.isLoggedIn)
const selectedRoute = computed(() => routes.value.find(item => item.id === selectedRouteId.value) || routes.value[0])
const selectedProgress = computed(() => selectedRoute.value ? progress.value[selectedRoute.value.id] : undefined)
const completedTaskIds = computed(() => selectedProgress.value?.completedTaskIds || [])
const activeTask = computed(() => selectedRoute.value?.tasks?.find(task => task.id === activeTaskId.value))
const activeCulturalToken = computed(() =>
  activeTask.value ? culturalTokenForTask(activeTask.value) : undefined,
)
const locationMap = computed(() => new Map(locations.value.map(item => [item.id, item])))
const totalTaskCount = computed(() => routes.value.reduce((total, route) => total + (route.tasks?.length || 0), 0))
const ownedBadgeIds = computed(() => new Set(ownedBadges.value.map(item => item.badge_id)))
const nextTask = computed(() => selectedRoute.value?.tasks?.find(task => !completedTaskIds.value.includes(task.id)))
const selectedRoutePoints = computed(() =>
  selectedRoute.value?.tasks?.reduce((total, task) => total + task.points, 0) || 0,
)
const earnedRoutePoints = computed(() =>
  selectedProgress.value?.records
    .filter(record => record.status === 'COMPLETED')
    .reduce((total, record) => total + record.awardedPoints, 0) || 0,
)
const completedRouteCount = computed(() =>
  routes.value.filter(route => progress.value[route.id]?.progressPercent === 100).length,
)
const photoFootprints = computed(() =>
  (selectedProgress.value?.records || [])
    .filter(record => record.status === 'COMPLETED' && record.evidenceAssetId)
    .map(record => ({
      record,
      task: selectedRoute.value?.tasks?.find(task => task.id === record.taskId),
      url: evidenceUrls.value[record.recordId],
    })),
)
const selectedRouteTaskIds = computed(() =>
  new Set((selectedRoute.value?.tasks || []).map(task => task.id)),
)
const recentPointRecords = computed(() =>
  pointRecords.value
    .filter(record =>
      record.reason_type === 'TASK_COMPLETE'
      && selectedRouteTaskIds.value.has(Number(record.business_key?.replace('task:', ''))),
    )
    .slice(0, 5),
)

function formatRecordTime(value: string | null) {
  if (!value) return '刚刚'
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function handleMallRedeemed(result: ShopRedeemResult) {
  pointsTotal.value = result.pointsTotal
  if (auth.user) auth.user.points_total = result.pointsTotal
  toast.value = result.alreadyRedeemed
    ? `${result.productName}的兑换请求已处理`
    : `${result.productName}兑换成功，消耗 ${result.cost} 积分`
  await refreshAccount()
}

async function loadRoutes() {
  loading.value = true
  error.value = ''
  serviceFallback.value = false
  try {
    const [routeResponse, locationResponse, badgeResponse] = await Promise.all([
      api.get<{ data: PageData<CultureRoute> }>('/routes', { params: { pageSize: 20 } }),
      api.get<{ data: PageData<Location> }>('/locations', { params: { pageSize: 100 } }),
      api.get<{ data: Badge[] }>('/badges'),
    ])
    routes.value = await Promise.all(
      routeResponse.data.data.items.map(async item => {
        const detail = await api.get<{ data: CultureRoute }>(`/routes/${item.id}`)
        return detail.data.data
      }),
    )
    locations.value = locationResponse.data.data.items
    badges.value = badgeResponse.data.data
    if (!selectedRouteId.value && routes.value[0]) selectedRouteId.value = routes.value[0].id
    await refreshAccount()
  } catch (event) {
    routes.value = demoRouteFallback.routes
    locations.value = demoRouteFallback.locations
    selectedRouteId.value = routes.value[0]?.id
    serviceFallback.value = true
    error.value = `路线内容加载失败：${(event as Error).message}`
  } finally {
    loading.value = false
  }
}

async function refreshProgress() {
  if (!isLoggedIn.value) {
    progress.value = {}
    return
  }
  const results = await Promise.all(
    routes.value.map(route => api.get<{ data: RouteProgress }>(`/routes/${route.id}/progress`)),
  )
  progress.value = Object.fromEntries(results.map(result => [result.data.data.routeId, result.data.data]))
  await refreshEvidenceUrls()
}

async function refreshEvidenceUrls() {
  Object.values(evidenceUrls.value).forEach(url => URL.revokeObjectURL(url))
  evidenceUrls.value = {}
  const evidenceRecords = Object.values(progress.value)
    .flatMap(item => item.records)
    .filter(record => record.evidenceAssetId)
  const loaded = await Promise.allSettled(
    evidenceRecords.map(async record => {
      const response = await api.get(
        `/tasks/${record.taskId}/evidence/${record.evidenceAssetId}`,
        { responseType: 'blob' },
      )
      return [record.recordId, URL.createObjectURL(response.data)] as const
    }),
  )
  evidenceUrls.value = Object.fromEntries(
    loaded
      .filter((item): item is PromiseFulfilledResult<readonly [number, string]> => item.status === 'fulfilled')
      .map(item => item.value),
  )
}

async function refreshAccount() {
  if (!isLoggedIn.value) return
  const [pointResponse, recordResponse, badgeResponse] = await Promise.all([
    api.get<{ data: { pointsTotal: number } }>('/points/summary'),
    api.get<{ data: PageData<PointRecord> }>('/points/records', { params: { pageSize: 20 } }),
    api.get<{ data: UserBadge[] }>('/badges/mine'),
  ])
  pointsTotal.value = pointResponse.data.data.pointsTotal
  pointRecords.value = recordResponse.data.data.items
  ownedBadges.value = badgeResponse.data.data
  await refreshProgress()
}

function selectRoute(route: CultureRoute) {
  selectedRouteId.value = route.id
  activeTaskId.value = undefined
}

function selectTask(task: RouteTask) {
  if (serviceFallback.value) {
    activeTaskId.value = task.id
    toast.value = '当前为离线路线预览；恢复 MySQL 后可登录提交任务并获得积分。'
    return
  }
  if (!isLoggedIn.value) {
    const redirect = task.task_type === 'QUIZ' && selectedRoute.value
      ? `/routes/${selectedRoute.value.id}/tasks/${task.id}/quiz`
      : '/routes/journey'
    requestLogin(redirect)
    return
  }
  if (task.task_type === 'QUIZ' && selectedRoute.value) {
    const target = `/routes/${selectedRoute.value.id}/tasks/${task.id}/quiz`
    router.push(target)
    return
  }
  activeTaskId.value = task.id
}

function requestLogin(redirect = '/routes/journey') {
  router.push({ path: '/login', query: { redirect } })
}

function goToCreation() {
  if (!isLoggedIn.value) {
    requestLogin('/creation')
    return
  }
  router.push('/creation')
}

async function startRoute() {
  if (!selectedRoute.value) return
  if (serviceFallback.value) {
    toast.value = '路线服务暂不可用，请稍后再试。'
    return
  }
  if (!isLoggedIn.value) {
    requestLogin()
    return
  }
  busy.value = true
  error.value = ''
  try {
    const response = await api.post(`/routes/${selectedRoute.value.id}/start`)
    toast.value = response.data.message
    await refreshProgress()
    if (nextTask.value) activeTaskId.value = nextTask.value.id
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    busy.value = false
  }
}

async function completeTask(submission: TaskSubmission) {
  if (!activeTask.value) return
  if (serviceFallback.value) {
    error.value = '当前为离线路线预览，不能提交任务或发放积分。请恢复 MySQL 后重试。'
    return
  }
  if (!isLoggedIn.value) {
    requestLogin()
    return
  }
  const completingTask = activeTask.value
  busy.value = true
  error.value = ''
  toast.value = ''
  const beforeBadges = new Set(ownedBadges.value.map(item => item.badge_id))
  try {
    if (!selectedProgress.value?.started && selectedRoute.value) {
      await api.post(`/routes/${selectedRoute.value.id}/start`)
      await refreshProgress()
    }
    const payload = { ...submission.payload }
    if (submission.photo) {
      const upload = await api.post<{ data: { id: number } }>(
        `/tasks/${completingTask.id}/evidence`,
        submission.photo,
        {
          headers: {
            'Content-Type': submission.photo.type,
            'X-File-Name': encodeURIComponent(submission.photo.name),
          },
        },
      )
      payload.file_asset_id = upload.data.data.id
    }
    const response = await api.post<{ data: TaskCompleteResult }>(
      `/tasks/${completingTask.id}/complete`,
      payload,
    )
    const result = response.data.data
    if (auth.user && result.pointsTotal !== undefined) {
      auth.user.points_total = result.pointsTotal
    }
    await refreshAccount()
    const newOwned = ownedBadges.value.find(item => !beforeBadges.has(item.badge_id))
    unlockedBadge.value = newOwned ? badges.value.find(item => item.id === newOwned.badge_id) : undefined
    toast.value = result.alreadyCompleted
      ? '该任务已完成，本次未重复加分'
      : `任务完成，获得 ${result.awardedPoints} 积分`
    if (!result.alreadyCompleted) {
      unlockedToken.value = {
        token: culturalTokenForTask(completingTask),
        points: result.awardedPoints,
      }
    }
    const next = selectedRoute.value?.tasks?.find(task => !completedTaskIds.value.includes(task.id))
    if (next) activeTaskId.value = next.id
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    busy.value = false
  }
}

watch(selectedRoute, route => {
  if (!route) return
  activeTaskId.value = undefined
}, { immediate: true })
onMounted(loadRoutes)
onBeforeUnmount(() => {
  Object.values(evidenceUrls.value).forEach(url => URL.revokeObjectURL(url))
})
</script>

<template>
  <div class="route-journey">
    <section class="route-intro">
      <div><p class="m2-kicker">CAMPUS CULTURE TRAIL</p><h1>校园文化寻迹</h1><p>校园路线连接文化讲解、现场观察、文化问答和多种打卡方式。选择路线后从地图任务点开始探索。</p></div>
      <div class="journey-stats"><article><strong>{{ routes.length }}</strong><span>校园路线</span></article><article><strong>{{ totalTaskCount }}</strong><span>任务节点</span></article><article><strong>{{ pointsTotal }}</strong><span>我的积分</span></article></div>
    </section>

    <PointsMall
      :points-total="pointsTotal"
      :logged-in="isLoggedIn"
      :point-records="pointRecords"
      @login="requestLogin()"
      @redeemed="handleMallRedeemed"
    />

    <div v-if="loading" class="journey-state">正在加载校园路线…</div>
    <div v-else-if="error && !routes.length" class="journey-state error"><b>路线暂时无法加载</b><span>{{ error }}</span><button type="button" @click="loadRoutes">重新加载</button></div>

    <template v-else>
      <div v-if="serviceFallback" class="journey-service-warning">
        <div><b>离线校园路线预览</b><span>{{ error }}</span></div>
        <button type="button" @click="loadRoutes">重新加载</button>
      </div>
      <section class="route-picker" aria-label="校园路线">
        <button v-for="item in routes" :key="item.id" type="button" :class="{ active: selectedRoute?.id === item.id }" @click="selectRoute(item)">
          <span>{{ String(routes.indexOf(item) + 1).padStart(2, '0') }}</span>
          <div><small>{{ item.distance_km }} KM · {{ item.duration_minutes }} MIN</small><h2>{{ item.title }}</h2><p>{{ item.summary }}</p></div>
          <footer><b>{{ item.tasks?.length || 0 }} 个节点</b><em>{{ progress[item.id]?.progressPercent || 0 }}%</em></footer>
          <i><span :style="{ width: `${progress[item.id]?.progressPercent || 0}%` }" /></i>
        </button>
      </section>

      <section v-if="selectedRoute" class="route-workspace">
        <div class="route-map-column">
          <CampusMap
            :route="selectedRoute"
            :locations="locations"
            :completed-task-ids="completedTaskIds"
            :active-task-id="activeTaskId"
            @select-task="selectTask"
          />
          <div class="route-actions">
            <div>
              <b>{{ selectedRoute.title }}</b>
              <span v-if="selectedProgress?.started">{{ selectedProgress.completedTasks }} / {{ selectedProgress.totalTasks }} 个任务已完成</span>
              <span v-else>领取路线后开始记录进度</span>
            </div>
            <button type="button" :disabled="busy" @click="startRoute">{{ !isLoggedIn ? '登录并领取路线' : selectedProgress?.started ? '继续路线' : '领取路线' }}</button>
          </div>
        </div>

        <aside class="route-timeline">
          <header><div><p class="m2-kicker">TASK TIMELINE</p><h2>任务节点</h2></div><strong>{{ selectedProgress?.progressPercent || 0 }}%</strong></header>
          <ol>
            <li v-for="task in selectedRoute.tasks" :key="task.id" :class="{ completed: completedTaskIds.includes(task.id), active: activeTaskId === task.id }">
              <button type="button" @click="selectTask(task)">
                <span>{{ completedTaskIds.includes(task.id) ? '✓' : String(task.order_no).padStart(2, '0') }}</span>
                <div><b>{{ task.title }}</b><small>{{ locationMap.get(task.location_id)?.name }} · +{{ task.points }} 积分</small></div>
                <em>{{ task.task_type === 'QUIZ' ? '问答' : task.task_type === 'CHECK_IN' ? '图片' : task.task_type === 'QR_CODE' ? '扫码' : '定位' }}</em>
              </button>
            </li>
          </ol>
        </aside>
      </section>

      <section v-if="selectedRoute" class="journey-footprints">
        <article class="photo-footprints">
          <header><div><p class="m2-kicker">MY PHOTO FOOTPRINTS</p><h2>我的图片足迹</h2></div><span>{{ photoFootprints.length }} 张</span></header>
          <div v-if="photoFootprints.length" class="footprint-grid">
            <figure v-for="item in photoFootprints" :key="item.record.recordId">
              <img v-if="item.url" :src="item.url" :alt="`${item.task?.title || '校园任务'}打卡照片`" loading="lazy" />
              <figcaption><b>{{ item.task?.title || '校园任务' }}</b><span>{{ formatRecordTime(item.record.completedAt) }}</span></figcaption>
            </figure>
          </div>
          <div v-else class="footprint-empty">
            <span>影</span>
            <div><b>{{ isLoggedIn ? '还没有图片足迹' : '登录后记录图片足迹' }}</b><p>完成图片任务后，现场照片会自动汇入这条路线的个人文化相册。</p></div>
            <button v-if="!isLoggedIn" type="button" @click="requestLogin()">去登录</button>
            <button v-else-if="nextTask" type="button" @click="selectTask(nextTask)">完成下一任务</button>
          </div>
        </article>

        <article class="journey-ledger">
          <header><div><p class="m2-kicker">LIVE ACTIVITY</p><h2>本路线积分动态</h2></div><strong>{{ earnedRoutePoints }} / {{ selectedRoutePoints }}</strong></header>
          <ol v-if="recentPointRecords.length">
            <li v-for="record in recentPointRecords" :key="record.id">
              <span>{{ record.amount > 0 ? '+' : '' }}{{ record.amount }}</span>
              <div><b>{{ record.description }}</b><small>{{ formatRecordTime(record.created_at) }} · 余额 {{ record.balance_after }}</small></div>
            </li>
          </ol>
          <div v-else class="ledger-empty"><b>本路线尚无积分动态</b><p>完成当前路线任务后，对应积分变化将在这里显示。</p></div>
          <footer><span>已完成路线 {{ completedRouteCount }} / {{ routes.length }}</span><span>文化徽章 {{ ownedBadges.length }} / {{ badges.length }}</span></footer>
        </article>
      </section>

      <section v-if="selectedProgress?.progressPercent === 100 && selectedRoute" class="route-certificate">
        <span>岭潮</span>
        <div><p>ROUTE COMPLETION · CAMPUS CULTURE</p><h2>{{ selectedRoute.title }}探索证书</h2><small>已完成 {{ selectedProgress.totalTasks }} 个任务，获得 {{ earnedRoutePoints }} 路线积分。继续把校园发现带入 AI 共创与社区传播。</small></div>
        <button type="button" @click="goToCreation">继续共创 →</button>
      </section>

      <section class="achievement-board">
        <header><div><p class="m2-kicker">CULTURAL BADGES</p><h2>文化徽章</h2></div><span>积分流水 {{ pointRecords.length }} 条</span></header>
        <div class="badge-grid">
          <article v-for="badge in badges" :key="badge.id" :class="{ owned: ownedBadgeIds.has(badge.id) }">
            <span>{{ ownedBadgeIds.has(badge.id) ? '徽' : '锁' }}</span>
            <div><b>{{ badge.name }}</b><p>{{ badge.description }}</p><small>{{ badge.rule_type }} ≥ {{ badge.rule_value }}</small></div>
          </article>
        </div>
        <button v-if="selectedProgress?.progressPercent === 100" class="create-next" type="button" @click="goToCreation">路线完成，进入 AI 共创 →</button>
      </section>
    </template>

    <div v-if="toast" class="journey-toast" role="status">{{ toast }}</div>
    <div v-if="error && routes.length && !serviceFallback" class="journey-error" role="alert">{{ error }}<button type="button" @click="error = ''">关闭</button></div>
    <div v-if="unlockedBadge" class="badge-unlocked" role="status" @animationend="unlockedBadge = undefined"><span>徽</span><div><small>新徽章已解锁</small><b>{{ unlockedBadge.name }}</b><p>{{ unlockedBadge.description }}</p></div></div>
    <CulturalTokenReveal
      v-if="unlockedToken"
      :token="unlockedToken.token"
      :points="unlockedToken.points"
      @close="unlockedToken = undefined"
    />

    <TaskPanel
      v-if="activeTask"
      :task="activeTask"
      :location="locationMap.get(activeTask.location_id)"
      :completed="completedTaskIds.includes(activeTask.id)"
      :busy="busy"
      :token-title="activeCulturalToken?.name"
      @close="activeTaskId = undefined"
      @submit="completeTask"
    />
  </div>
</template>

<style scoped>
.journey-service-warning{display:flex;align-items:center;justify-content:space-between;gap:20px;margin:0 0 18px;padding:14px 18px;border:1px solid #e4c985;border-radius:10px;background:#fff8df;color:#624819}.journey-service-warning>div{display:grid;gap:3px}.journey-service-warning span{font-size:12px}.journey-service-warning button{min-height:36px;padding:0 13px;border:1px solid #9f2d35;border-radius:7px;color:#9f2d35;background:#fff;font-weight:800}@media(max-width:700px){.journey-service-warning{align-items:flex-start;flex-direction:column}}
.route-journey{padding-bottom:30px}.route-intro{display:grid;grid-template-columns:1.25fr .75fr;align-items:end;gap:30px;padding:38px 0 26px}.route-intro h1{margin:0;font-size:clamp(42px,6vw,68px)}.route-intro>div>p:last-child{max-width:720px;color:#66716b;line-height:1.8}.journey-stats{display:grid;grid-template-columns:repeat(3,1fr);background:#dfe3dd;border:1px solid #dfe3dd;gap:1px}.journey-stats article{padding:18px;background:#fff}.journey-stats strong{display:block;color:#9f2d35;font-size:32px}.journey-stats span{font-size:11px}.route-picker{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:12px 0 22px}.route-picker>button{position:relative;display:grid;grid-template-columns:auto 1fr;gap:13px;overflow:hidden;padding:20px;text-align:left;border:1px solid #dfe3dd;border-radius:12px;background:#fff}.route-picker>button>span{display:grid;place-items:center;width:38px;height:38px;color:#fff;background:#285a47;border-radius:50%;font-family:serif}.route-picker h2{margin:4px 0;font-size:21px}.route-picker p{height:43px;overflow:hidden;margin:0;color:#68736d;font-size:12px;line-height:1.7}.route-picker small{color:#9f2d35;font-size:9px;font-weight:800}.route-picker footer{grid-column:1/-1;display:flex;justify-content:space-between;padding:0;color:#5f6a64;background:none;font-size:11px}.route-picker footer em{font-style:normal}.route-picker>button>i{position:absolute;left:0;right:0;bottom:0;height:4px;background:#edf0ec}.route-picker>button>i span{display:block;height:100%;background:#cb9138}.route-picker>button.active{color:#fff;background:#285a47;border-color:#285a47;box-shadow:0 14px 35px rgba(40,90,71,.18)}.route-picker>button.active>span{color:#9f2d35;background:#f0c777}.route-picker>button.active small,.route-picker>button.active p,.route-picker>button.active footer{color:#d8e5df}.route-workspace{display:grid;grid-template-columns:minmax(0,1fr) 350px;gap:16px}.route-map-column{min-width:0}.route-actions{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-top:12px;padding:16px 18px;color:#fff;background:#285a47;border-radius:10px}.route-actions>div{display:grid}.route-actions span{color:#c3d6cd;font-size:11px}.route-actions button,.create-next{min-height:43px;padding:0 16px;border:0;border-radius:7px;color:#fff;background:#9f2d35;font-weight:800}.route-timeline{overflow:hidden;border:1px solid #dfe3dd;border-radius:14px;background:#fff}.route-timeline>header{display:flex;align-items:end;justify-content:space-between;padding:20px;border-bottom:1px solid #e2e6e2}.route-timeline h2{margin:0}.route-timeline>header strong{color:#9f2d35;font-size:29px}.route-timeline ol{display:grid;gap:0;margin:0;padding:0;list-style:none}.route-timeline li{border-bottom:1px solid #edf0ed}.route-timeline li:last-child{border:0}.route-timeline li button{width:100%;display:grid;grid-template-columns:36px 1fr auto;align-items:center;gap:10px;padding:14px;border:0;background:#fff;text-align:left}.route-timeline li button>span{display:grid;place-items:center;width:32px;height:32px;color:#fff;background:#82948b;border-radius:50%;font-size:10px;font-weight:900}.route-timeline li div{display:grid}.route-timeline li small{color:#77817c;font-size:10px}.route-timeline li em{color:#285a47;background:#e9f1ed;border-radius:999px;padding:4px 7px;font-size:9px;font-style:normal}.route-timeline li.active button{background:#fff8e9}.route-timeline li.completed button>span{background:#9f2d35}.achievement-board{margin-top:42px;padding:28px;background:#f3efe4;border-radius:14px}.achievement-board>header{display:flex;align-items:end;justify-content:space-between}.achievement-board h2{margin:0}.achievement-board>header>span{color:#67716c;font-size:12px}.badge-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:18px}.badge-grid article{display:grid;grid-template-columns:54px 1fr;gap:12px;padding:17px;background:rgba(255,255,255,.72);border:1px solid #ded8c9;border-radius:10px;filter:grayscale(1);opacity:.62}.badge-grid article>span{display:grid;place-items:center;width:50px;height:50px;color:#756d5d;background:#ddd6c8;border-radius:50%;font-family:serif;font-size:20px}.badge-grid article b{font-size:16px}.badge-grid article p{margin:4px 0;color:#69726d;font-size:11px}.badge-grid article small{color:#9f2d35;font-size:9px}.badge-grid article.owned{filter:none;opacity:1;background:#fff}.badge-grid article.owned>span{color:#684712;background:#e8c474;box-shadow:0 0 0 5px rgba(232,196,116,.2)}.create-next{margin-top:18px}.journey-state{display:grid;gap:8px;place-items:center;min-height:330px;padding:35px;background:#fff;border:1px solid #dfe3dd;border-radius:12px}.journey-state.error{color:#9f2d35}.journey-state button{min-height:40px;padding:0 14px;border:0;border-radius:7px;color:#fff;background:#9f2d35}.journey-toast,.journey-error{position:fixed;z-index:45;left:50%;bottom:28px;transform:translateX(-50%);padding:13px 18px;color:#fff;background:#285a47;border-radius:999px;box-shadow:0 12px 30px rgba(31,57,46,.25)}.journey-error{display:flex;align-items:center;gap:12px;background:#9f2d35}.journey-error button{border:0;color:#fff;background:none;text-decoration:underline}.badge-unlocked{position:fixed;z-index:50;left:50%;top:50%;display:flex;align-items:center;gap:18px;width:min(420px,calc(100vw - 32px));padding:25px;transform:translate(-50%,-50%);color:#fff;background:linear-gradient(135deg,#8d2630,#b35a35);border:2px solid #f0ca7b;border-radius:16px;box-shadow:0 30px 90px rgba(75,22,28,.45);animation:badgeReveal 4s ease both}.badge-unlocked>span{display:grid;place-items:center;width:80px;height:80px;color:#784d13;background:#edcb81;border:5px solid rgba(255,255,255,.75);border-radius:50%;font-family:serif;font-size:34px}.badge-unlocked div{display:grid}.badge-unlocked small{color:#f2d79d}.badge-unlocked b{font-size:26px}.badge-unlocked p{margin:5px 0 0}@keyframes badgeReveal{0%{opacity:0;transform:translate(-50%,-45%) scale(.72)}10%,85%{opacity:1;transform:translate(-50%,-50%) scale(1)}100%{opacity:0;transform:translate(-50%,-55%) scale(.96)}}@media(max-width:980px){.route-intro{grid-template-columns:1fr}.route-picker{grid-template-columns:1fr}.route-picker p{height:auto}.route-workspace{grid-template-columns:1fr}.route-timeline ol{grid-template-columns:repeat(2,1fr)}.badge-grid{grid-template-columns:1fr 1fr}}@media(max-width:620px){.route-intro{padding-top:22px}.journey-stats{grid-template-columns:repeat(3,1fr)}.journey-stats article{padding:12px 8px}.journey-stats strong{font-size:24px}.route-timeline ol,.badge-grid{grid-template-columns:1fr}.route-actions{align-items:flex-start;flex-direction:column}.route-actions button{width:100%}.achievement-board{padding:20px}.achievement-board>header{align-items:flex-start;flex-direction:column}}

.footprint-empty button{min-height:40px;padding:0 13px;border:0;border-radius:7px;color:#fff;background:#9f2d35;font-weight:800;white-space:nowrap}

.journey-footprints{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(320px,.65fr);gap:16px;margin-top:34px}.journey-footprints>article{padding:24px;border:1px solid #dfe3dd;border-radius:14px;background:#fff}.journey-footprints header{display:flex;align-items:flex-end;justify-content:space-between;gap:16px}.journey-footprints h2{margin:0}.photo-footprints>header>span{color:#9f2d35;font-size:12px;font-weight:800}.footprint-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:17px}.footprint-grid figure{position:relative;min-height:190px;overflow:hidden;margin:0;border-radius:10px;background:#e8eee9}.footprint-grid img{width:100%;height:100%;min-height:190px;object-fit:cover}.footprint-grid figcaption{position:absolute;right:0;bottom:0;left:0;display:grid;padding:34px 12px 11px;color:#fff;background:linear-gradient(transparent,rgba(17,39,31,.9))}.footprint-grid figcaption span{font-size:9px}.footprint-empty{display:grid;grid-template-columns:58px 1fr auto;align-items:center;gap:14px;min-height:150px;margin-top:17px;padding:20px;background:#f1f5f2;border:1px dashed #b9cabf;border-radius:10px}.footprint-empty>span{display:grid;place-items:center;width:54px;height:54px;color:#fff;background:#285a47;border-radius:50%;font-family:serif;font-size:22px}.footprint-empty p,.ledger-empty p{margin:4px 0 0;color:#68756e;font-size:11px;line-height:1.6}.journey-ledger{display:flex;min-width:0;flex-direction:column}.journey-ledger>header>strong{color:#9f2d35;font-size:21px;white-space:nowrap}.journey-ledger ol{display:grid;gap:0;margin:16px 0 0;padding:0;list-style:none}.journey-ledger li{display:grid;grid-template-columns:42px minmax(0,1fr);align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid #edf0ed}.journey-ledger li>span{color:#9f2d35;font-weight:900}.journey-ledger li div{display:grid;min-width:0}.journey-ledger li b{overflow:hidden;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.journey-ledger li small{color:#7b8580;font-size:9px}.ledger-empty{min-height:120px;padding:22px 0}.journey-ledger footer{display:flex;min-height:0;justify-content:space-between;gap:8px;margin-top:auto;padding:13px 0 0;border-top:1px solid #e4e8e4;color:#637069;background:transparent;font-size:9px;line-height:1.5}.route-certificate{display:grid;grid-template-columns:82px 1fr auto;align-items:center;gap:20px;margin-top:24px;padding:24px;color:#fff;background:linear-gradient(125deg,#7e222c,#aa4b36);border:2px solid #eac778;border-radius:14px;box-shadow:0 18px 38px rgba(92,29,35,.2)}.route-certificate>span{display:grid;place-items:center;width:76px;height:76px;color:#774e13;background:#ebc879;border:5px double #fff5d9;border-radius:50%;font-family:serif;font-size:20px}.route-certificate p{margin:0;color:#f1d597;font-size:9px;font-weight:900;letter-spacing:.12em}.route-certificate h2{margin:4px 0}.route-certificate small{color:#f3dfd0;line-height:1.6}.route-certificate button{min-height:42px;padding:0 15px;border:1px solid rgba(255,255,255,.55);border-radius:7px;color:#fff;background:rgba(255,255,255,.09);font-weight:800}

@media(max-width:1180px){.journey-footprints{grid-template-columns:1fr}.footprint-grid{grid-template-columns:repeat(4,1fr)}}@media(max-width:760px){.footprint-grid{grid-template-columns:repeat(2,1fr)}.footprint-empty{grid-template-columns:52px 1fr}.footprint-empty button{grid-column:1/-1}.route-certificate{grid-template-columns:62px 1fr}.route-certificate>span{width:56px;height:56px;font-size:15px}.route-certificate button{grid-column:1/-1}.journey-footprints>article{padding:19px}}@media(max-width:480px){.footprint-grid{grid-template-columns:1fr}}
</style>
