<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/services/api'

interface RouteTask {
  id: number
  route_id: number
  culture_item_id: number | null
  location_id: number
  order_no: number
  title: string
  description: string
  task_type: string
  question: string | null
  options: string[] | null
  points: number
}

interface CultureRoute {
  id: number
  title: string
  slug: string
  summary: string
  duration_minutes: number
  distance_km: string
  status: string
  tasks: RouteTask[]
}

interface Location {
  id: number
  name: string
  address: string
  latitude: string
  longitude: string
  culture_item_id: number | null
}

interface PageData<T> {
  items: T[]
  total: number
}

const routes = ref<CultureRoute[]>([])
const locations = ref<Location[]>([])
const selectedRouteId = ref<number>()
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const routeDialogVisible = ref(false)
const taskDialogVisible = ref(false)
const taskMode = ref<'create' | 'edit'>('create')
const editingTaskId = ref<number>()
const taskOptionsText = ref('')

const routeForm = reactive({
  title: '',
  summary: '',
  duration_minutes: 60,
  distance_km: 0,
  status: 'PUBLISHED',
})

const taskForm = reactive({
  route_id: 0,
  culture_item_id: null as number | null,
  location_id: 0,
  order_no: 1,
  title: '',
  description: '',
  task_type: 'CHECK_IN',
  question: '',
  correct_answer: '',
  points: 10,
})

const selectedRoute = computed(() =>
  routes.value.find(item => item.id === selectedRouteId.value),
)
const locationMap = computed(() =>
  new Map(locations.value.map(item => [item.id, item])),
)
const allTasks = computed(() => routes.value.flatMap(item => item.tasks || []))
const photoTaskCount = computed(() =>
  allTasks.value.filter(item => item.task_type !== 'QUIZ').length,
)
const quizTaskCount = computed(() =>
  allTasks.value.filter(item => item.task_type === 'QUIZ').length,
)
const totalPoints = computed(() =>
  allTasks.value.reduce((total, item) => total + item.points, 0),
)

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [routeResponse, locationResponse] = await Promise.all([
      api.get<{ data: PageData<CultureRoute> }>('/routes', { params: { pageSize: 100 } }),
      api.get<{ data: PageData<Location> }>('/locations', { params: { pageSize: 100 } }),
    ])
    const details = await Promise.all(
      routeResponse.data.data.items.map(async route => {
        const response = await api.get<{ data: CultureRoute }>(`/routes/${route.id}`)
        return response.data.data
      }),
    )
    routes.value = details
    locations.value = locationResponse.data.data.items
    if (!routes.value.some(item => item.id === selectedRouteId.value)) {
      selectedRouteId.value = routes.value[0]?.id
    }
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    loading.value = false
  }
}

function selectRoute(route: CultureRoute) {
  selectedRouteId.value = route.id
}

function openRouteEditor() {
  if (!selectedRoute.value) return
  Object.assign(routeForm, {
    title: selectedRoute.value.title,
    summary: selectedRoute.value.summary,
    duration_minutes: selectedRoute.value.duration_minutes,
    distance_km: Number(selectedRoute.value.distance_km),
    status: selectedRoute.value.status,
  })
  routeDialogVisible.value = true
}

async function saveRoute() {
  if (!selectedRoute.value || !routeForm.title.trim() || !routeForm.summary.trim()) {
    ElMessage.warning('请完整填写路线标题和简介')
    return
  }
  saving.value = true
  try {
    await api.put(`/routes/${selectedRoute.value.id}`, {
      ...routeForm,
      title: routeForm.title.trim(),
      summary: routeForm.summary.trim(),
    })
    routeDialogVisible.value = false
    ElMessage.success('路线信息已更新')
    await loadData()
  } catch (event) {
    ElMessage.error((event as Error).message)
  } finally {
    saving.value = false
  }
}

function resetTaskForm() {
  const tasks = selectedRoute.value?.tasks || []
  const firstTask = tasks[0]
  Object.assign(taskForm, {
    route_id: selectedRoute.value?.id || 0,
    culture_item_id: firstTask?.culture_item_id ?? locations.value[0]?.culture_item_id ?? null,
    location_id: firstTask?.location_id ?? locations.value[0]?.id ?? 0,
    order_no: Math.max(0, ...tasks.map(item => item.order_no)) + 1,
    title: '',
    description: '',
    task_type: 'CHECK_IN',
    question: '请上传任务点现场照片完成图片打卡',
    correct_answer: '',
    points: 10,
  })
  taskOptionsText.value = ''
  editingTaskId.value = undefined
}

function openTaskCreator() {
  if (!selectedRoute.value) return
  taskMode.value = 'create'
  resetTaskForm()
  taskDialogVisible.value = true
}

function openTaskEditor(task: RouteTask) {
  taskMode.value = 'edit'
  editingTaskId.value = task.id
  Object.assign(taskForm, {
    route_id: task.route_id,
    culture_item_id: task.culture_item_id,
    location_id: task.location_id,
    order_no: task.order_no,
    title: task.title,
    description: task.description,
    task_type: task.task_type === 'QUIZ' ? 'QUIZ' : 'CHECK_IN',
    question: task.question || '',
    correct_answer: '',
    points: task.points,
  })
  taskOptionsText.value = (task.options || []).join('\n')
  taskDialogVisible.value = true
}

function parsedOptions() {
  return taskOptionsText.value
    .split(/\r?\n|,/)
    .map(item => item.trim())
    .filter(Boolean)
}

async function saveTask() {
  if (!taskForm.title.trim() || !taskForm.description.trim() || !taskForm.location_id) {
    ElMessage.warning('请完整填写任务名称、说明和地点')
    return
  }
  const options = parsedOptions()
  if (taskForm.task_type === 'QUIZ' && options.length < 2) {
    ElMessage.warning('问答任务至少需要两个选项')
    return
  }
  if (taskMode.value === 'create' && taskForm.task_type === 'QUIZ' && !taskForm.correct_answer.trim()) {
    ElMessage.warning('新建问答任务必须填写正确答案')
    return
  }

  const payload: Record<string, unknown> = {
    location_id: taskForm.location_id,
    culture_item_id: taskForm.culture_item_id,
    order_no: taskForm.order_no,
    title: taskForm.title.trim(),
    description: taskForm.description.trim(),
    task_type: taskForm.task_type,
    question: taskForm.question.trim() || null,
    options: taskForm.task_type === 'QUIZ' ? options : null,
    points: taskForm.points,
  }
  if (taskMode.value === 'create') payload.route_id = taskForm.route_id
  if (taskForm.task_type === 'QUIZ' && taskForm.correct_answer.trim()) {
    payload.correct_answer = taskForm.correct_answer.trim()
  }
  if (taskForm.task_type === 'CHECK_IN') {
    payload.correct_answer = null
    payload.qr_code = null
  }

  saving.value = true
  try {
    if (taskMode.value === 'create') {
      await api.post('/tasks', payload)
      ElMessage.success('任务已新增')
    } else {
      await api.put(`/tasks/${editingTaskId.value}`, payload)
      ElMessage.success('任务已更新')
    }
    taskDialogVisible.value = false
    await loadData()
  } catch (event) {
    ElMessage.error((event as Error).message)
  } finally {
    saving.value = false
  }
}

async function removeTask(task: RouteTask) {
  try {
    await ElMessageBox.confirm(
      `确认删除任务“${task.title}”？已有用户记录时后端会拒绝删除。`,
      '删除任务',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
    )
    await api.delete(`/tasks/${task.id}`)
    ElMessage.success('任务已删除')
    await loadData()
  } catch (event) {
    if (event === 'cancel' || event === 'close') return
    ElMessage.error((event as Error).message || '删除失败')
  }
}

onMounted(loadData)
</script>

<template>
  <section class="route-admin">
    <header class="route-admin-head">
      <div><p>MEMBER 4 · ROUTE OPERATIONS</p><h1 class="page-title">路线与任务管理</h1><span>同步管理用户端三条校园路线、图片打卡、文化问答和积分。</span></div>
      <div><button type="button" @click="loadData">刷新数据</button><button class="primary" type="button" :disabled="!selectedRoute" @click="openTaskCreator">新增任务</button></div>
    </header>

    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" />

    <div class="route-admin-metrics">
      <article><small>校园路线</small><strong>{{ routes.length }}</strong></article>
      <article><small>任务节点</small><strong>{{ allTasks.length }}</strong></article>
      <article><small>图片打卡</small><strong>{{ photoTaskCount }}</strong></article>
      <article><small>文化问答</small><strong>{{ quizTaskCount }}</strong></article>
      <article><small>总积分配置</small><strong>{{ totalPoints }}</strong></article>
    </div>

    <div v-loading="loading" class="route-admin-body">
      <aside class="route-admin-picker">
        <button v-for="(route, index) in routes" :key="route.id" type="button" :class="{ active: route.id === selectedRouteId }" @click="selectRoute(route)">
          <span>{{ String(index + 1).padStart(2, '0') }}</span>
          <div><b>{{ route.title }}</b><small>{{ route.distance_km }} km · {{ route.duration_minutes }} 分钟</small></div>
          <em>{{ route.tasks.length }} 项</em>
        </button>
      </aside>

      <main v-if="selectedRoute" class="route-admin-workspace">
        <div class="route-summary">
          <div><p>{{ selectedRoute.slug }}</p><h2>{{ selectedRoute.title }}</h2><span>{{ selectedRoute.summary }}</span></div>
          <div class="route-summary-meta">
            <el-tag :type="selectedRoute.status === 'PUBLISHED' ? 'success' : 'info'">{{ selectedRoute.status }}</el-tag>
            <button type="button" @click="openRouteEditor">编辑路线</button>
          </div>
        </div>

        <el-table :data="selectedRoute.tasks" stripe class="task-table">
          <el-table-column prop="order_no" label="顺序" width="70" align="center" />
          <el-table-column label="任务" min-width="190">
            <template #default="{ row }"><div class="task-title"><b>{{ row.title }}</b><small>{{ row.description }}</small></div></template>
          </el-table-column>
          <el-table-column label="地点" min-width="145">
            <template #default="{ row }">{{ locationMap.get(row.location_id)?.name || `地点 ${row.location_id}` }}</template>
          </el-table-column>
          <el-table-column label="类型" width="100" align="center">
            <template #default="{ row }"><el-tag :type="row.task_type === 'QUIZ' ? 'warning' : 'success'">{{ row.task_type === 'QUIZ' ? '文化问答' : '图片打卡' }}</el-tag></template>
          </el-table-column>
          <el-table-column prop="points" label="积分" width="80" align="center" />
          <el-table-column label="任务要求" min-width="210">
            <template #default="{ row }">{{ row.question || '上传现场图片' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="145" fixed="right">
            <template #default="{ row }"><el-button link type="primary" @click="openTaskEditor(row)">编辑</el-button><el-button link type="danger" @click="removeTask(row)">删除</el-button></template>
          </el-table-column>
        </el-table>
      </main>
    </div>

    <el-dialog v-model="routeDialogVisible" title="编辑路线信息" width="min(620px, 92vw)">
      <el-form label-position="top">
        <el-form-item label="路线名称"><el-input v-model="routeForm.title" /></el-form-item>
        <el-form-item label="路线简介"><el-input v-model="routeForm.summary" type="textarea" :rows="3" maxlength="500" show-word-limit /></el-form-item>
        <div class="dialog-grid">
          <el-form-item label="预计时长（分钟）"><el-input-number v-model="routeForm.duration_minutes" :min="1" /></el-form-item>
          <el-form-item label="路线距离（公里）"><el-input-number v-model="routeForm.distance_km" :min="0" :precision="2" :step="0.1" /></el-form-item>
          <el-form-item label="发布状态"><el-select v-model="routeForm.status"><el-option label="已发布" value="PUBLISHED" /><el-option label="草稿" value="DRAFT" /></el-select></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="routeDialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveRoute">保存路线</el-button></template>
    </el-dialog>

    <el-dialog v-model="taskDialogVisible" :title="taskMode === 'create' ? '新增任务节点' : '编辑任务节点'" width="min(720px, 94vw)">
      <el-form label-position="top">
        <div class="dialog-grid task-basic-grid">
          <el-form-item label="任务顺序"><el-input-number v-model="taskForm.order_no" :min="1" /></el-form-item>
          <el-form-item label="任务类型"><el-select v-model="taskForm.task_type"><el-option label="图片打卡" value="CHECK_IN" /><el-option label="文化问答" value="QUIZ" /></el-select></el-form-item>
          <el-form-item label="完成积分"><el-input-number v-model="taskForm.points" :min="0" :max="1000" /></el-form-item>
        </div>
        <el-form-item label="任务名称"><el-input v-model="taskForm.title" maxlength="120" /></el-form-item>
        <el-form-item label="校园地点"><el-select v-model="taskForm.location_id" filterable style="width:100%"><el-option v-for="location in locations" :key="location.id" :label="`${location.name} · ${location.address}`" :value="location.id" /></el-select></el-form-item>
        <el-form-item label="任务说明"><el-input v-model="taskForm.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item :label="taskForm.task_type === 'QUIZ' ? '问题' : '图片要求'"><el-input v-model="taskForm.question" /></el-form-item>
        <template v-if="taskForm.task_type === 'QUIZ'">
          <el-form-item label="选项（每行一个）"><el-input v-model="taskOptionsText" type="textarea" :rows="4" placeholder="选项 A&#10;选项 B&#10;选项 C" /></el-form-item>
          <el-form-item :label="taskMode === 'create' ? '正确答案' : '新正确答案（留空则不修改）'"><el-input v-model="taskForm.correct_answer" /></el-form-item>
        </template>
      </el-form>
      <template #footer><el-button @click="taskDialogVisible = false">取消</el-button><el-button type="primary" :loading="saving" @click="saveTask">{{ taskMode === 'create' ? '新增任务' : '保存修改' }}</el-button></template>
    </el-dialog>
  </section>
</template>

<style scoped>
.route-admin{display:grid;gap:20px}.route-admin-head{display:flex;align-items:flex-end;justify-content:space-between;gap:24px}.route-admin-head p,.route-summary p{margin:0 0 5px;color:#9e3138;font-size:10px;font-weight:800;letter-spacing:.13em}.route-admin-head h1{margin-bottom:4px}.route-admin-head span{color:#6a756f}.route-admin-head>div:last-child{display:flex;gap:8px}.route-admin button{min-height:38px;padding:0 14px;border:1px solid #d7ddd9;border-radius:7px;background:#fff;cursor:pointer}.route-admin button.primary{color:#fff;background:#9e3138;border-color:#9e3138}.route-admin-metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}.route-admin-metrics article{padding:17px 19px;background:#fff;border:1px solid #e0e5e1;border-radius:10px}.route-admin-metrics small{color:#6c7771}.route-admin-metrics strong{display:block;margin-top:4px;color:#9e3138;font-size:28px}.route-admin-body{display:grid;grid-template-columns:245px minmax(0,1fr);gap:14px;min-height:480px}.route-admin-picker{display:grid;align-content:start;gap:8px}.route-admin-picker button{display:grid;grid-template-columns:36px 1fr auto;align-items:center;gap:10px;min-height:76px;padding:12px;text-align:left}.route-admin-picker button>span{display:grid;place-items:center;width:34px;height:34px;color:#fff;background:#62746b;border-radius:50%;font-size:11px;font-weight:800}.route-admin-picker button div{display:grid;gap:4px}.route-admin-picker button small{color:#7a8580;font-size:10px}.route-admin-picker button em{color:#9e3138;font-size:10px;font-style:normal}.route-admin-picker button.active{color:#fff;background:#263f35;border-color:#263f35}.route-admin-picker button.active>span{color:#7a252c;background:#edc77d}.route-admin-picker button.active small,.route-admin-picker button.active em{color:#d9e6df}.route-admin-workspace{min-width:0;overflow:hidden;background:#fff;border:1px solid #e0e5e1;border-radius:10px}.route-summary{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;padding:22px}.route-summary h2{margin:0 0 6px}.route-summary span{color:#66736c;line-height:1.65}.route-summary-meta{display:flex;align-items:center;gap:8px;flex-shrink:0}.task-title{display:grid;gap:4px}.task-title small{overflow:hidden;color:#78827d;font-size:11px;text-overflow:ellipsis;white-space:nowrap}.dialog-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.dialog-grid :deep(.el-input-number),.dialog-grid :deep(.el-select){width:100%}@media(max-width:1100px){.route-admin-metrics{grid-template-columns:repeat(3,1fr)}.route-admin-body{grid-template-columns:1fr}.route-admin-picker{grid-template-columns:repeat(3,1fr)}}@media(max-width:720px){.route-admin-head{align-items:flex-start;flex-direction:column}.route-admin-metrics{grid-template-columns:repeat(2,1fr)}.route-admin-picker{grid-template-columns:1fr}.route-summary{flex-direction:column}.dialog-grid{grid-template-columns:1fr}}
</style>
