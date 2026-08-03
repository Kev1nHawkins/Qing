<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { api } from '@/services/api'

interface AdminUserItem {
  id: number
  username: string
  email: string | null
  nickname: string
  avatar_url: string | null
  is_active: boolean
  points_total: number
  role: { code: string; name: string }
  created_at: string
}

interface PageData<T> {
  total: number
  items: T[]
  page: number
  pageSize: number
}

const users = ref<AdminUserItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const error = ref('')
const keyword = ref('')

const visibleUsers = computed(() => {
  const normalized = keyword.value.trim().toLowerCase()
  if (!normalized) return users.value
  return users.value.filter(user =>
    [user.username, user.nickname, user.email || '', user.role.name]
      .some(value => value.toLowerCase().includes(normalized)),
  )
})
const activeCount = computed(() => users.value.filter(user => user.is_active).length)
const normalUserCount = computed(() => users.value.filter(user => user.role.code === 'user').length)

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

async function loadUsers() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get<{ data: PageData<AdminUserItem> }>('/admin/users', {
      params: { page: page.value, pageSize: pageSize.value },
    })
    users.value = response.data.data.items
    total.value = response.data.data.total
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    loading.value = false
  }
}

function changePage(value: number) {
  page.value = value
  loadUsers()
}

onMounted(loadUsers)
</script>

<template>
  <section class="user-admin">
    <header>
      <div>
        <p>REAL USER DIRECTORY</p>
        <h1 class="page-title">用户管理</h1>
        <span>用户端注册成功后会立即写入真实 MySQL，并出现在此列表中。</span>
      </div>
      <button type="button" @click="loadUsers">刷新用户</button>
    </header>

    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" />

    <div class="user-metrics">
      <article><small>全部账号</small><strong>{{ total }}</strong></article>
      <article><small>本页普通用户</small><strong>{{ normalUserCount }}</strong></article>
      <article><small>本页正常账号</small><strong>{{ activeCount }}</strong></article>
    </div>

    <div class="user-toolbar">
      <el-input v-model="keyword" clearable placeholder="筛选当前页用户名、昵称、邮箱或角色" />
      <small>当前页显示 {{ visibleUsers.length }} / {{ users.length }} 条</small>
    </div>

    <el-table v-loading="loading" :data="visibleUsers" stripe class="user-table">
      <el-table-column label="用户" min-width="180">
        <template #default="{ row }">
          <div class="user-identity">
            <span>{{ row.nickname.slice(0, 1) }}</span>
            <div><b>{{ row.nickname }}</b><small>@{{ row.username }}</small></div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="邮箱" min-width="190">
        <template #default="{ row }">{{ row.email || '未填写' }}</template>
      </el-table-column>
      <el-table-column label="角色" width="110" align="center">
        <template #default="{ row }">
          <el-tag :type="row.role.code === 'admin' ? 'danger' : 'success'">{{ row.role.name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="积分" width="100" align="center">
        <template #default="{ row }"><b class="points">{{ row.points_total }}</b></template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'">{{ row.is_active ? '正常' : '停用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="注册时间" min-width="170">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
    </el-table>

    <footer>
      <span>账号密码哈希不会在管理端返回或展示。</span>
      <el-pagination
        background
        layout="prev, pager, next"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        @current-change="changePage"
      />
    </footer>
  </section>
</template>

<style scoped>
.user-admin{display:grid;gap:20px}.user-admin>header{display:flex;align-items:flex-end;justify-content:space-between;gap:24px}.user-admin>header p{margin:0 0 5px;color:#9e3138;font-size:10px;font-weight:900;letter-spacing:.14em}.user-admin>header h1{margin-bottom:4px}.user-admin>header span{color:#68746e}.user-admin>header button{min-height:39px;padding:0 15px;border:1px solid #d6ddd8;border-radius:7px;background:#fff}.user-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.user-metrics article{padding:18px 20px;background:#fff;border:1px solid #dfe5e1;border-radius:10px}.user-metrics small{color:#6c7771}.user-metrics strong{display:block;margin-top:4px;color:#9e3138;font-size:29px}.user-toolbar{display:flex;align-items:center;justify-content:space-between;gap:20px;padding:14px;background:#fff;border:1px solid #e0e5e1;border-radius:9px}.user-toolbar :deep(.el-input){max-width:430px}.user-toolbar small{color:#75807a}.user-table{border:1px solid #e0e5e1;border-radius:10px}.user-identity{display:flex;align-items:center;gap:11px}.user-identity>span{display:grid;place-items:center;width:38px;height:38px;color:#fff;background:#29483b;border-radius:50%;font-family:serif;font-size:17px}.user-identity>div{display:grid}.user-identity small{color:#7b8580}.points{color:#9e3138;font-size:16px}.user-admin>footer{display:flex;align-items:center;justify-content:space-between;gap:18px;color:#75807a;font-size:11px}
@media(max-width:720px){.user-admin>header,.user-admin>footer,.user-toolbar{align-items:flex-start;flex-direction:column}.user-metrics{grid-template-columns:1fr}.user-toolbar :deep(.el-input){max-width:none;width:100%}}
</style>
