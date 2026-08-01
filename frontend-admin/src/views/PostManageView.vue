<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { api } from '@/services/api'

interface AdminPost {
  id: number
  author_id: number
  author_name?: string | null
  culture_item_id?: number | null
  culture_item_title?: string | null
  creation_id?: number | null
  creation_title?: string | null
  creation_preview_url?: string | null
  title: string
  content: string
  cover_image_url?: string | null
  status: string
  like_count: number
  comment_count: number
  favorite_count: number
  tags: string[]
  created_at: string
}

interface PostPage {
  total: number
  items: AdminPost[]
  page: number
  pageSize: number
  statusCounts: Record<string, number>
}

const posts = ref<AdminPost[]>([])
const loading = ref(false)
const error = ref('')
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const status = ref('')
const keyword = ref('')
const appliedKeyword = ref('')
const counts = reactive<Record<string, number>>({
  PENDING: 0,
  PUBLISHED: 0,
  REJECTED: 0,
  OFFLINE: 0,
})
const drawerOpen = ref(false)
const selectedPost = ref<AdminPost | null>(null)
const reviewing = ref(false)

const statusTabs = [
  { value: '', label: '全部' },
  { value: 'PENDING', label: '待审核' },
  { value: 'PUBLISHED', label: '已发布' },
  { value: 'REJECTED', label: '已驳回' },
  { value: 'OFFLINE', label: '已下架' },
]

const totalCount = computed(
  () => counts.PENDING + counts.PUBLISHED + counts.REJECTED + counts.OFFLINE,
)

const metricItems = computed(() => [
  { label: '全部内容', value: totalCount.value, tone: 'neutral' },
  { label: '待审核', value: counts.PENDING, tone: 'pending' },
  { label: '已发布', value: counts.PUBLISHED, tone: 'published' },
  { label: '已下架', value: counts.OFFLINE, tone: 'offline' },
])

const statusLabel: Record<string, string> = {
  PENDING: '待审核',
  PUBLISHED: '已发布',
  REJECTED: '已驳回',
  OFFLINE: '已下架',
}

const statusType: Record<string, 'warning' | 'success' | 'danger' | 'info'> = {
  PENDING: 'warning',
  PUBLISHED: 'success',
  REJECTED: 'danger',
  OFFLINE: 'info',
}

async function loadPosts() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/admin/posts', {
      params: {
        page: page.value,
        pageSize: pageSize.value,
        status: status.value || undefined,
        keyword: appliedKeyword.value || undefined,
      },
    })
    const result = data.data as PostPage
    posts.value = result.items
    total.value = result.total
    Object.assign(counts, result.statusCounts)
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    loading.value = false
  }
}

function selectStatus(nextStatus: string) {
  status.value = nextStatus
  page.value = 1
  void loadPosts()
}

function search() {
  appliedKeyword.value = keyword.value.trim()
  page.value = 1
  void loadPosts()
}

function resetSearch() {
  keyword.value = ''
  appliedKeyword.value = ''
  page.value = 1
  void loadPosts()
}

function preview(post: AdminPost) {
  selectedPost.value = post
  drawerOpen.value = true
}

async function review(nextStatus: 'PUBLISHED' | 'REJECTED' | 'OFFLINE') {
  if (!selectedPost.value) return
  const action = nextStatus === 'PUBLISHED' ? '通过' : nextStatus === 'REJECTED' ? '驳回' : '下架'
  try {
    await ElMessageBox.confirm(
      `确认${action}《${selectedPost.value.title}》？`,
      `${action}内容`,
      {
        confirmButtonText: action,
        cancelButtonText: '取消',
        type: nextStatus === 'PUBLISHED' ? 'success' : 'warning',
      },
    )
  } catch {
    return
  }

  reviewing.value = true
  try {
    await api.patch(`/admin/posts/${selectedPost.value.id}/review`, {
      status: nextStatus,
    })
    selectedPost.value.status = nextStatus
    ElMessage.success(`内容已${action}`)
    await loadPosts()
  } catch (event) {
    ElMessage.error((event as Error).message)
  } finally {
    reviewing.value = false
  }
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

onMounted(loadPosts)
</script>

<template>
  <section class="post-manage">
    <header class="manage-heading">
      <div>
        <h1 class="page-title">社区审核</h1>
        <p>审核社区作品、处理下架，并保持演示内容健康可见。</p>
      </div>
      <el-button :loading="loading" @click="loadPosts">刷新数据</el-button>
    </header>

    <el-alert
      v-if="error"
      class="manage-error"
      :title="error"
      type="error"
      show-icon
      :closable="false"
    />

    <div class="moderation-metrics">
      <article
        v-for="metric in metricItems"
        :key="metric.label"
        :class="`metric-tone--${metric.tone}`"
      >
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
      </article>
    </div>

    <div class="moderation-tabs" role="tablist" aria-label="审核状态">
      <button
        v-for="tab in statusTabs"
        :key="tab.value || 'all'"
        type="button"
        role="tab"
        :aria-selected="status === tab.value"
        :class="{ active: status === tab.value }"
        @click="selectStatus(tab.value)"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="moderation-toolbar">
      <el-input
        v-model="keyword"
        clearable
        placeholder="搜索标题或作者"
        @keyup.enter="search"
        @clear="resetSearch"
      />
      <el-button type="primary" @click="search">搜索</el-button>
      <el-button @click="resetSearch">重置</el-button>
    </div>

    <el-table
      v-loading="loading"
      class="moderation-table"
      :data="posts"
      row-key="id"
      stripe
      @row-dblclick="preview"
    >
      <el-table-column label="内容" min-width="300">
        <template #default="{ row }: { row: AdminPost }">
          <div class="post-cell">
            <el-image
              v-if="row.cover_image_url || row.creation_preview_url"
              class="post-thumb"
              :src="row.cover_image_url || row.creation_preview_url"
              fit="cover"
            />
            <div>
              <strong>{{ row.title }}</strong>
              <p>{{ row.content }}</p>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="作者" min-width="120">
        <template #default="{ row }: { row: AdminPost }">
          <strong class="author-name">{{ row.author_name || `用户 ${row.author_id}` }}</strong>
          <small>ID: {{ row.author_id }}</small>
        </template>
      </el-table-column>
      <el-table-column label="关联内容" min-width="150">
        <template #default="{ row }: { row: AdminPost }">
          <el-tag v-if="row.creation_id" size="small">AI 作品</el-tag>
          <el-tag v-else-if="row.culture_item_id" size="small" type="info">文化内容</el-tag>
          <el-tag v-else size="small" type="warning">校园打卡</el-tag>
          <p class="linked-label">
            {{ row.creation_title || row.culture_item_title || '校园现场记录' }}
          </p>
        </template>
      </el-table-column>
      <el-table-column label="数据" width="105">
        <template #default="{ row }: { row: AdminPost }">
          <div class="data-cell">
            <span>赞 {{ row.like_count }}</span>
            <span>评 {{ row.comment_count }}</span>
            <span>藏 {{ row.favorite_count }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }: { row: AdminPost }">
          <el-tag :type="statusType[row.status]" effect="plain">
            {{ statusLabel[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="发布时间" width="165">
        <template #default="{ row }: { row: AdminPost }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }: { row: AdminPost }">
          <el-button link type="primary" @click="preview(row)">预览</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="当前筛选下没有社区内容" />
      </template>
    </el-table>

    <div class="moderation-pagination">
      <span>共 {{ total }} 条</span>
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        background
        layout="prev, pager, next"
        :total="total"
        @current-change="loadPosts"
      />
    </div>

    <el-drawer
      v-model="drawerOpen"
      class="review-drawer"
      size="min(480px, 92vw)"
      title="内容审核"
    >
      <template v-if="selectedPost">
        <section class="review-section">
          <h3>基本信息</h3>
          <dl>
            <div><dt>标题</dt><dd>{{ selectedPost.title }}</dd></div>
            <div><dt>作者</dt><dd>{{ selectedPost.author_name || `用户 ${selectedPost.author_id}` }}</dd></div>
            <div>
              <dt>关联内容</dt>
              <dd>{{ selectedPost.creation_title || selectedPost.culture_item_title || '校园现场记录' }}</dd>
            </div>
            <div><dt>当前状态</dt><dd>{{ statusLabel[selectedPost.status] }}</dd></div>
          </dl>
        </section>

        <section class="review-section">
          <h3>内容摘要</h3>
          <p class="review-copy">{{ selectedPost.content }}</p>
          <div v-if="selectedPost.tags?.length" class="review-tags">
            <el-tag v-for="tag in selectedPost.tags" :key="tag" size="small">
              {{ tag }}
            </el-tag>
          </div>
        </section>

        <section class="review-section">
          <h3>互动数据</h3>
          <div class="review-data">
            <span><strong>{{ selectedPost.like_count }}</strong> 点赞</span>
            <span><strong>{{ selectedPost.comment_count }}</strong> 评论</span>
            <span><strong>{{ selectedPost.favorite_count }}</strong> 收藏</span>
          </div>
          <p class="review-date">发布时间：{{ formatDate(selectedPost.created_at) }}</p>
        </section>
      </template>

      <template #footer>
        <div class="review-actions">
          <el-button
            type="success"
            :loading="reviewing"
            @click="review('PUBLISHED')"
          >
            通过
          </el-button>
          <el-button
            type="danger"
            plain
            :loading="reviewing"
            @click="review('REJECTED')"
          >
            驳回
          </el-button>
          <el-button
            :loading="reviewing"
            @click="review('OFFLINE')"
          >
            下架
          </el-button>
        </div>
      </template>
    </el-drawer>
  </section>
</template>

<style scoped>
.manage-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
}

.manage-heading p {
  margin: -6px 0 0;
  color: #75817b;
  font-size: 14px;
}

.manage-error {
  margin-top: 18px;
}

.moderation-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(150px, 1fr));
  gap: 16px;
  margin: 24px 0 18px;
}

.moderation-metrics article {
  padding: 18px 20px;
  border: 1px solid #e1e7e3;
  border-radius: 8px;
  background: #fff;
}

.moderation-metrics span {
  display: block;
  color: #68756f;
  font-size: 13px;
}

.moderation-metrics strong {
  display: block;
  margin-top: 8px;
  color: #1f2925;
  font-size: 28px;
  font-variant-numeric: tabular-nums;
}

.metric-tone--pending {
  border-left: 3px solid #e5a53a !important;
}

.metric-tone--published {
  border-left: 3px solid #3c9b60 !important;
}

.metric-tone--offline {
  border-left: 3px solid #8b9791 !important;
}

.moderation-tabs {
  display: flex;
  gap: 28px;
  border-bottom: 1px solid #dce3df;
}

.moderation-tabs button {
  position: relative;
  padding: 13px 2px;
  border: 0;
  color: #53615a;
  background: transparent;
  font: inherit;
  font-size: 14px;
  cursor: pointer;
}

.moderation-tabs button.active {
  color: #a46d14;
  font-weight: 700;
}

.moderation-tabs button.active::after {
  position: absolute;
  right: 0;
  bottom: -1px;
  left: 0;
  height: 2px;
  content: "";
  background: #e4a72f;
}

.moderation-toolbar {
  display: flex;
  gap: 10px;
  margin: 16px 0;
}

.moderation-toolbar .el-input {
  width: min(360px, 100%);
}

.moderation-table {
  border: 1px solid #e0e6e2;
  border-radius: 8px;
  background: #fff;
}

.post-cell {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.post-thumb {
  flex: 0 0 auto;
  width: 64px;
  height: 50px;
  border-radius: 5px;
  background: #edf1ee;
}

.post-cell > div {
  min-width: 0;
}

.post-cell strong {
  display: block;
  overflow: hidden;
  color: #26312d;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.post-cell p,
.linked-label {
  overflow: hidden;
  margin: 5px 0 0;
  color: #7a8580;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.author-name {
  display: block;
  font-size: 13px;
}

.author-name + small {
  display: block;
  margin-top: 4px;
  color: #8a948f;
}

.data-cell {
  display: grid;
  gap: 3px;
  color: #64716b;
  font-size: 12px;
}

.moderation-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 16px;
  color: #68756f;
  font-size: 13px;
}

.review-section {
  padding: 0 0 24px;
  border-bottom: 1px solid #e7ebe8;
  margin-bottom: 24px;
}

.review-section h3 {
  margin: 0 0 16px;
  font-size: 14px;
}

.review-section dl {
  display: grid;
  gap: 14px;
  margin: 0;
}

.review-section dl > div {
  display: grid;
  grid-template-columns: 78px 1fr;
  gap: 12px;
}

.review-section dt {
  color: #7a8580;
  font-size: 12px;
}

.review-section dd {
  margin: 0;
  color: #26312d;
  font-size: 13px;
  line-height: 1.55;
}

.review-copy {
  margin: 0;
  color: #49554f;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.review-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 14px;
}

.review-data {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.review-data span {
  padding: 12px;
  border-radius: 6px;
  color: #69766f;
  background: #f4f7f5;
  font-size: 12px;
}

.review-data strong {
  display: block;
  margin-bottom: 3px;
  color: #26312d;
  font-size: 20px;
}

.review-date {
  margin: 16px 0 0;
  color: #7a8580;
  font-size: 12px;
}

.review-actions {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.review-actions .el-button {
  width: 100%;
  margin: 0;
}

@media (max-width: 900px) {
  .moderation-metrics {
    grid-template-columns: repeat(2, 1fr);
  }

  .moderation-toolbar {
    flex-wrap: wrap;
  }
}
</style>
