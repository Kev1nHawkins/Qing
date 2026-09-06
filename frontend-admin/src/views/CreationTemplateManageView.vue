<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { api } from '@/services/api'

type PublishStatus = 'DRAFT' | 'PUBLISHED' | 'OFFLINE'

interface CreationTemplate {
  id: number
  name: string
  code: string
  description: string
  prompt_template: string
  options_schema: Record<string, string[]> | null
  preview_url: string | null
  status: PublishStatus
  culture_item_id: number | null
  created_at: string
  updated_at: string
}

interface CultureItem {
  id: number
  title: string
}

interface TemplatePage {
  total: number
  items: CreationTemplate[]
  page: number
  pageSize: number
  statusCounts: Record<PublishStatus, number>
}

interface OptionField {
  id: number
  key: string
  values: string[]
  draftValue: string
}

const templates = ref<CreationTemplate[]>([])
const cultures = ref<CultureItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const keyword = ref('')
const statusFilter = ref<PublishStatus | ''>('')
const dialogVisible = ref(false)
const mode = ref<'create' | 'edit'>('create')
const editingId = ref<number>()
const optionFields = ref<OptionField[]>([])
const statusCounts = reactive<Record<PublishStatus, number>>({
  DRAFT: 0,
  PUBLISHED: 0,
  OFFLINE: 0,
})
let nextOptionId = 1

const form = reactive({
  name: '',
  code: '',
  description: '',
  prompt_template: '',
  preview_url: '',
  status: 'DRAFT' as PublishStatus,
  culture_item_id: null as number | null,
})

const overallTotal = computed(
  () => statusCounts.DRAFT + statusCounts.PUBLISHED + statusCounts.OFFLINE,
)
const cultureMap = computed(
  () => new Map(cultures.value.map(item => [item.id, item.title])),
)
const promptPlaceholders = computed(() => {
  const names = new Set<string>()
  for (const match of form.prompt_template.matchAll(/\{([A-Za-z_][A-Za-z0-9_]*)\}/g)) {
    names.add(match[1])
  }
  return [...names]
})
const contractIssues = computed(() => {
  const issues: string[] = []
  const keys = optionFields.value.map(item => item.key.trim()).filter(Boolean)
  const keySet = new Set(keys)
  const promptSet = new Set(promptPlaceholders.value)
  const missing = [...promptSet].filter(name => !keySet.has(name))
  const unused = [...keySet].filter(name => !promptSet.has(name))
  if (missing.length) issues.push(`缺少选项配置：${missing.join('、')}`)
  if (unused.length) issues.push(`未在 Prompt 中使用：${unused.join('、')}`)
  return issues
})

function newOptionField(key = '', values: string[] = []): OptionField {
  return { id: nextOptionId++, key, values: [...values], draftValue: '' }
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function statusLabel(status: PublishStatus) {
  return { DRAFT: '草稿', PUBLISHED: '已发布', OFFLINE: '已下线' }[status]
}

function statusTagType(status: PublishStatus) {
  return status === 'PUBLISHED' ? 'success' : status === 'OFFLINE' ? 'danger' : 'info'
}

function optionSummary(template: CreationTemplate) {
  const entries = Object.entries(template.options_schema || {})
  return {
    variables: entries.length,
    values: entries.reduce((sum, [, values]) => sum + values.length, 0),
  }
}

async function loadData() {
  loading.value = true
  error.value = ''
  try {
    const [templateResponse, cultureResponse] = await Promise.all([
      api.get<{ data: TemplatePage }>('/admin/creation-templates', {
        params: {
          page: page.value,
          pageSize: pageSize.value,
          keyword: keyword.value.trim() || undefined,
          status: statusFilter.value || undefined,
        },
      }),
      api.get<{ data: { items: CultureItem[] } }>('/admin/cultures', {
        params: { pageSize: 100 },
      }),
    ])
    const data = templateResponse.data.data
    templates.value = data.items
    total.value = data.total
    Object.assign(statusCounts, data.statusCounts)
    cultures.value = cultureResponse.data.data.items
  } catch (event) {
    error.value = (event as Error).message
  } finally {
    loading.value = false
  }
}

function resetForm() {
  Object.assign(form, {
    name: '',
    code: '',
    description: '',
    prompt_template: '请以{culture_element}和{campus_landmark}为主题，创作{style}风格文化海报。',
    preview_url: '',
    status: 'DRAFT',
    culture_item_id: null,
  })
  optionFields.value = [
    newOptionField('culture_element'),
    newOptionField('campus_landmark'),
    newOptionField('style'),
  ]
  editingId.value = undefined
}

function openCreator() {
  mode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

function openEditor(template: CreationTemplate) {
  mode.value = 'edit'
  editingId.value = template.id
  Object.assign(form, {
    name: template.name,
    code: template.code,
    description: template.description,
    prompt_template: template.prompt_template,
    preview_url: template.preview_url || '',
    status: template.status,
    culture_item_id: template.culture_item_id,
  })
  optionFields.value = Object.entries(template.options_schema || {}).map(
    ([key, values]) => newOptionField(key, values),
  )
  if (!optionFields.value.length) optionFields.value.push(newOptionField())
  dialogVisible.value = true
}

function addOptionField() {
  optionFields.value.push(newOptionField())
}

function removeOptionField(id: number) {
  optionFields.value = optionFields.value.filter(item => item.id !== id)
}

function addOptionValue(field: OptionField) {
  const value = field.draftValue.trim()
  if (!value) return
  if (field.values.includes(value)) {
    ElMessage.warning('候选值不能重复')
    return
  }
  field.values.push(value)
  field.draftValue = ''
}

function validateForm() {
  if (!form.name.trim() || !form.code.trim() || !form.description.trim()) {
    return '请完整填写模板名称、编码和描述'
  }
  if (!form.prompt_template.trim()) return '请填写 Prompt 模板'
  if (!optionFields.value.length) return '模板至少需要一个选项变量'

  const keys = optionFields.value.map(item => item.key.trim())
  const invalidKey = keys.find(key => !/^[A-Za-z_][A-Za-z0-9_]*$/.test(key))
  if (invalidKey !== undefined) return `选项变量名无效：${invalidKey || '空值'}`
  if (new Set(keys).size !== keys.length) return '选项变量名不能重复'
  const emptyValues = optionFields.value.find(item => !item.values.length)
  if (emptyValues) return `选项变量 ${emptyValues.key} 至少需要一个候选值`
  if (contractIssues.value.length) return contractIssues.value.join('；')
  return ''
}

async function saveTemplate() {
  const validationMessage = validateForm()
  if (validationMessage) {
    ElMessage.warning(validationMessage)
    return
  }
  const optionsSchema = Object.fromEntries(
    optionFields.value.map(item => [item.key.trim(), item.values]),
  )
  const payload = {
    name: form.name.trim(),
    description: form.description.trim(),
    prompt_template: form.prompt_template.trim(),
    options_schema: optionsSchema,
    preview_url: form.preview_url.trim() || null,
    status: form.status,
    culture_item_id: form.culture_item_id,
  }

  saving.value = true
  try {
    if (mode.value === 'create') {
      await api.post('/creations/templates', { ...payload, code: form.code.trim() })
      ElMessage.success('AI 模板已创建')
    } else {
      await api.put(`/creations/templates/${editingId.value}`, payload)
      ElMessage.success('AI 模板已更新')
    }
    dialogVisible.value = false
    await loadData()
  } catch (event) {
    ElMessage.error((event as Error).message)
  } finally {
    saving.value = false
  }
}

function applyFilters() {
  page.value = 1
  loadData()
}

function changePage(value: number) {
  page.value = value
  loadData()
}

onMounted(loadData)
</script>

<template>
  <section class="template-admin">
    <header>
      <div>
        <p>MEMBER 3 · AI TEMPLATE OPERATIONS</p>
        <h1 class="page-title">AI 模板管理</h1>
        <span>维护用户端共创模板、Prompt 约束、选项变量和发布状态。</span>
      </div>
      <div class="header-actions">
        <button type="button" @click="loadData">刷新数据</button>
        <button class="primary" type="button" @click="openCreator">新增模板</button>
      </div>
    </header>

    <el-alert v-if="error" :title="error" type="error" show-icon :closable="false" />

    <div class="template-metrics">
      <article><small>全部模板</small><strong>{{ overallTotal }}</strong></article>
      <article><small>已发布</small><strong>{{ statusCounts.PUBLISHED }}</strong></article>
      <article><small>草稿</small><strong>{{ statusCounts.DRAFT }}</strong></article>
      <article><small>已下线</small><strong>{{ statusCounts.OFFLINE }}</strong></article>
    </div>

    <div class="template-toolbar">
      <el-input
        v-model="keyword"
        clearable
        placeholder="搜索模板名称、编码或描述"
        @keyup.enter="applyFilters"
        @clear="applyFilters"
      />
      <el-select v-model="statusFilter" placeholder="全部状态" clearable @change="applyFilters">
        <el-option label="已发布" value="PUBLISHED" />
        <el-option label="草稿" value="DRAFT" />
        <el-option label="已下线" value="OFFLINE" />
      </el-select>
      <button type="button" @click="applyFilters">查询</button>
    </div>

    <el-table
      v-loading="loading"
      :data="templates"
      stripe
      class="template-table"
      empty-text="没有符合条件的 AI 模板"
    >
      <el-table-column label="模板" min-width="220">
        <template #default="{ row }">
          <div class="template-identity">
            <div><b>{{ row.name }}</b><small>{{ row.description }}</small></div>
            <code>{{ row.code }}</code>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="关联文化" min-width="145">
        <template #default="{ row }">
          {{ row.culture_item_id ? cultureMap.get(row.culture_item_id) || `文化条目 ${row.culture_item_id}` : '未关联' }}
        </template>
      </el-table-column>
      <el-table-column label="选项配置" width="120" align="center">
        <template #default="{ row }">
          <b>{{ optionSummary(row).variables }}</b> 个变量<br>
          <small>{{ optionSummary(row).values }} 个候选值</small>
        </template>
      </el-table-column>
      <el-table-column label="Prompt 摘要" min-width="230">
        <template #default="{ row }"><span class="prompt-preview">{{ row.prompt_template }}</span></template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-tag :type="statusTagType(row.status)">{{ statusLabel(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" width="170">
        <template #default="{ row }">{{ formatTime(row.updated_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="90" fixed="right">
        <template #default="{ row }"><el-button link type="primary" @click="openEditor(row)">编辑</el-button></template>
      </el-table-column>
    </el-table>

    <footer>
      <span>草稿和已下线模板不会出现在用户端。</span>
      <el-pagination
        background
        layout="prev, pager, next"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        @current-change="changePage"
      />
    </footer>

    <el-dialog
      v-model="dialogVisible"
      :title="mode === 'create' ? '新增 AI 模板' : '编辑 AI 模板'"
      width="min(860px, 95vw)"
      destroy-on-close
    >
      <el-form label-position="top" class="template-form">
        <div class="form-grid">
          <el-form-item label="模板名称" required>
            <el-input v-model="form.name" maxlength="120" />
          </el-form-item>
          <el-form-item label="唯一编码" required>
            <el-input v-model="form.code" :disabled="mode === 'edit'" maxlength="80" placeholder="kapok-poster" />
          </el-form-item>
          <el-form-item label="发布状态" required>
            <el-select v-model="form.status" style="width:100%">
              <el-option label="草稿" value="DRAFT" />
              <el-option label="已发布" value="PUBLISHED" />
              <el-option label="已下线" value="OFFLINE" />
            </el-select>
          </el-form-item>
          <el-form-item label="关联文化">
            <el-select v-model="form.culture_item_id" clearable filterable style="width:100%">
              <el-option v-for="culture in cultures" :key="culture.id" :label="culture.title" :value="culture.id" />
            </el-select>
          </el-form-item>
        </div>
        <el-form-item label="模板描述" required>
          <el-input v-model="form.description" type="textarea" :rows="2" maxlength="500" show-word-limit />
        </el-form-item>
        <el-form-item label="预览图 URL">
          <el-input v-model="form.preview_url" placeholder="https://… 或 /uploads/…" />
        </el-form-item>
        <el-form-item label="Prompt 模板" required>
          <el-input
            v-model="form.prompt_template"
            type="textarea"
            :rows="5"
            placeholder="使用 {variable_name} 引用下方选项变量"
          />
          <div class="placeholder-list">
            <span>已识别占位符</span>
            <el-tag v-for="name in promptPlaceholders" :key="name" size="small">{{ name }}</el-tag>
            <small v-if="!promptPlaceholders.length">尚未识别到占位符</small>
          </div>
          <p v-if="contractIssues.length" class="contract-error">{{ contractIssues.join('；') }}</p>
        </el-form-item>

        <div class="option-heading">
          <div><b>结构化选项</b><small>变量名必须与 Prompt 中的占位符一一对应。</small></div>
          <el-button @click="addOptionField">新增变量</el-button>
        </div>
        <div class="option-fields">
          <article v-for="field in optionFields" :key="field.id">
            <div class="option-field-head">
              <el-input v-model="field.key" placeholder="变量名，例如 style" />
              <el-button type="danger" plain @click="removeOptionField(field.id)">移除变量</el-button>
            </div>
            <div class="option-values">
              <el-tag
                v-for="value in field.values"
                :key="value"
                closable
                @close="field.values = field.values.filter(item => item !== value)"
              >{{ value }}</el-tag>
              <div class="value-adder">
                <el-input
                  v-model="field.draftValue"
                  placeholder="输入候选值"
                  @keyup.enter="addOptionValue(field)"
                />
                <el-button @click="addOptionValue(field)">添加</el-button>
              </div>
            </div>
          </article>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveTemplate">
          {{ mode === 'create' ? '创建模板' : '保存修改' }}
        </el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.template-admin{display:grid;gap:20px}.template-admin>header{display:flex;align-items:flex-end;justify-content:space-between;gap:24px}.template-admin>header p{margin:0 0 5px;color:#9e3138;font-size:10px;font-weight:900;letter-spacing:.14em}.template-admin>header h1{margin-bottom:4px}.template-admin>header span{color:#68746e}.header-actions{display:flex;gap:8px}.template-admin button{min-height:39px;padding:0 15px;border:1px solid #d6ddd8;border-radius:7px;background:#fff;cursor:pointer}.template-admin button.primary{color:#fff;background:#9e3138;border-color:#9e3138}.template-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.template-metrics article{padding:18px 20px;background:#fff;border:1px solid #dfe5e1;border-radius:10px}.template-metrics small{color:#6c7771}.template-metrics strong{display:block;margin-top:4px;color:#9e3138;font-size:29px}.template-toolbar{display:grid;grid-template-columns:minmax(260px,1fr) 180px auto;gap:10px;padding:14px;background:#fff;border:1px solid #e0e5e1;border-radius:9px}.template-table{border:1px solid #e0e5e1;border-radius:10px}.template-identity{display:grid;gap:7px}.template-identity>div{display:grid;gap:4px}.template-identity small{overflow:hidden;max-width:360px;color:#78827d;text-overflow:ellipsis;white-space:nowrap}.template-identity code{width:max-content;padding:3px 6px;color:#7f2931;background:#f7eceb;border-radius:4px}.prompt-preview{display:-webkit-box;overflow:hidden;color:#59655f;line-height:1.5;-webkit-box-orient:vertical;-webkit-line-clamp:2}.template-table small{color:#78827d}.template-admin>footer{display:flex;align-items:center;justify-content:space-between;gap:18px;color:#75807a;font-size:11px}.form-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:0 14px}.placeholder-list{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin-top:8px;color:#68736e;font-size:11px}.contract-error{margin:8px 0 0;color:#9e3138;font-size:12px}.option-heading{display:flex;align-items:center;justify-content:space-between;margin:10px 0}.option-heading>div{display:grid;gap:4px}.option-heading small{color:#75807a}.option-fields{display:grid;gap:10px}.option-fields article{padding:14px;background:#f7f9f7;border:1px solid #dfe5e1;border-radius:9px}.option-field-head{display:grid;grid-template-columns:1fr auto;gap:8px}.option-values{display:flex;flex-wrap:wrap;align-items:center;gap:7px;margin-top:10px}.value-adder{display:grid;grid-template-columns:minmax(150px,230px) auto;gap:6px}@media(max-width:900px){.template-metrics{grid-template-columns:repeat(2,1fr)}}@media(max-width:680px){.template-admin>header,.template-admin>footer{align-items:flex-start;flex-direction:column}.template-toolbar,.form-grid{grid-template-columns:1fr}.template-metrics{grid-template-columns:1fr 1fr}.header-actions{width:100%}.header-actions button{flex:1}.option-field-head,.value-adder{grid-template-columns:1fr}}
</style>
