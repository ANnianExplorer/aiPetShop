<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import { violationApi } from '@/api/violation'

interface SensitiveWordRow {
  id: number | string
  word: string
  category?: string
  level?: string
  hitCount?: number
  status?: number
  createTime?: string
}

interface ViolationRecordRow {
  id: number | string
  targetType?: string
  contentSnapshot?: string
  authorId?: number | string
  reason?: string
  word?: string
  status?: number
  createTime?: string
}

const loading = ref(false)
const submitting = ref(false)
const activeTab = ref<'words' | 'violations'>('words')
const tabs = [
  { key: 'words', label: '敏感词库', icon: 'block' },
  { key: 'violations', label: '违规记录', icon: 'report' },
] as const

const wordData = ref<SensitiveWordRow[]>([])
const violationData = ref<ViolationRecordRow[]>([])

// 统计卡：全部走分页 total，避免把当前页 hitCount 求和造成误导
const wordTotal = ref(0)
const pendingTotal = ref(0)
const processedTotal = ref(0)
const recordTotal = computed(() => pendingTotal.value + processedTotal.value)

// 敏感词筛选
const wordSearch = ref('')
const categoryFilter = ref('')
const statusFilter = ref<any>('')

// 违规记录筛选
const recordStatusFilter = ref<any>('')
const recordTypeFilter = ref('')

const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

// 敏感词新增 / 编辑弹窗
const showWordDialog = ref(false)
const editingId = ref<number | string | null>(null)
const wordForm = reactive({ word: '', category: 'spam', level: 'medium', status: 1 })
const dialogTitle = computed(() => (editingId.value == null ? '添加敏感词' : '编辑敏感词'))

/** 统一错误提示；request.ts 已经弹过一次时用 grouping 合并，避免双份 toast */
function showError(e: unknown, fallback: string) {
  const message = e instanceof Error && e.message ? e.message : fallback
  ElMessage.error({ message, grouping: true })
}

async function fetchStats() {
  try {
    const [words, pending, processed] = (await Promise.all([
      violationApi.listWords({ current: 1, pageSize: 1 }),
      violationApi.listRecords({ current: 1, pageSize: 1, status: 0 }),
      violationApi.listRecords({ current: 1, pageSize: 1, status: 1 }),
    ])) as any[]
    wordTotal.value = Number(words?.total || 0)
    pendingTotal.value = Number(pending?.total || 0)
    processedTotal.value = Number(processed?.total || 0)
  } catch (e) {
    showError(e, '统计数据加载失败')
  }
}

async function fetchData() {
  loading.value = true
  try {
    if (activeTab.value === 'words') {
      const params: Record<string, any> = { current: currentPage.value, pageSize: pageSize.value }
      if (wordSearch.value.trim()) params.word = wordSearch.value.trim()
      if (categoryFilter.value) params.category = categoryFilter.value
      if (statusFilter.value !== '' && statusFilter.value != null) params.status = statusFilter.value

      const res = (await violationApi.listWords(params)) as any
      wordData.value = res?.records || []
      total.value = Number(res?.total || 0)
    } else {
      const params: Record<string, any> = { current: currentPage.value, pageSize: pageSize.value }
      if (recordStatusFilter.value !== '' && recordStatusFilter.value != null) {
        params.status = recordStatusFilter.value
      }
      if (recordTypeFilter.value) params.targetType = recordTypeFilter.value

      const res = (await violationApi.listRecords(params)) as any
      violationData.value = res?.records || []
      total.value = Number(res?.total || 0)
    }
  } catch (e) {
    showError(e, activeTab.value === 'words' ? '敏感词加载失败' : '违规记录加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
  fetchStats()
})

function switchTab(tab: 'words' | 'violations') {
  if (activeTab.value === tab) return
  activeTab.value = tab
  currentPage.value = 1
  total.value = 0
  fetchData()
}

const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

const handleReset = () => {
  wordSearch.value = ''
  categoryFilter.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  fetchData()
}

const handleRecordSearch = () => {
  currentPage.value = 1
  fetchData()
}

const handleRecordReset = () => {
  recordStatusFilter.value = ''
  recordTypeFilter.value = ''
  currentPage.value = 1
  fetchData()
}

function openAddWord() {
  editingId.value = null
  Object.assign(wordForm, { word: '', category: 'spam', level: 'medium', status: 1 })
  showWordDialog.value = true
}

function openEditWord(row: SensitiveWordRow) {
  editingId.value = row.id
  Object.assign(wordForm, {
    word: row.word,
    category: row.category || 'other',
    level: row.level || 'medium',
    status: Number(row.status ?? 1),
  })
  showWordDialog.value = true
}

async function submitWord() {
  const word = wordForm.word.trim()
  if (!word) {
    ElMessage.warning('请输入敏感词')
    return
  }
  submitting.value = true
  try {
    if (editingId.value == null) {
      await violationApi.addWord({ word, category: wordForm.category, level: wordForm.level })
      ElMessage.success('敏感词已添加')
    } else {
      await violationApi.updateWord({
        id: editingId.value,
        word,
        category: wordForm.category,
        level: wordForm.level,
        status: wordForm.status,
      })
      ElMessage.success('敏感词已更新')
    }
    showWordDialog.value = false
    await Promise.all([fetchData(), fetchStats()])
  } catch (e) {
    showError(e, '敏感词保存失败')
  } finally {
    submitting.value = false
  }
}

async function removeWord(row: SensitiveWordRow) {
  try {
    await ElMessageBox.confirm(`确定删除敏感词「${row.word}」？`, '确认删除', { type: 'warning' })
  } catch {
    return
  }
  try {
    await violationApi.deleteWord(row.id)
    ElMessage.success('已删除')
    await Promise.all([fetchData(), fetchStats()])
  } catch (e) {
    showError(e, '删除失败')
  }
}

async function markHandled(row: ViolationRecordRow) {
  if (Number(row.status) === 1) return
  try {
    await ElMessageBox.confirm('确定将这条违规记录标记为已处理？', '确认处理', { type: 'warning' })
  } catch {
    return
  }
  try {
    await violationApi.handleRecord(row.id)
    ElMessage.success('已标记为已处理')
    await Promise.all([fetchData(), fetchStats()])
  } catch (e) {
    showError(e, '处理失败')
  }
}

const levelLabel = (level?: string) =>
  ({ critical: '严重', high: '高', medium: '中', low: '低' }[level || ''] || level || '-')
const levelColor = (level?: string) =>
  ({ critical: 'badge-error', high: 'badge-warning', medium: 'badge-info', low: 'badge-info' }[level || ''] ||
    'badge-info')
const categoryLabel = (cat?: string) =>
  ({ spam: '垃圾广告', fraud: '欺诈', violent: '暴力', other: '其他' }[cat || ''] || cat || '-')
const targetLabel = (type?: string) => (type === 'post' ? '帖子' : type === 'comment' ? '评论' : type || '-')
const statusLabel = (s?: number) => (Number(s) === 1 ? '已处理' : '待处理')
</script>

<template>
  <div v-loading="loading" class="space-y-6 max-w-screen-xl mx-auto">
    <!-- Header -->
    <div class="flex justify-between items-end animate-float-up">
      <div>
        <h2 class="font-[Plus_Jakarta_Sans] text-[32px] font-bold text-primary mb-2">违规管理</h2>
        <p class="text-on-surface-variant">管理敏感词库与违规内容审核</p>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 animate-float-up" style="animation-delay: 0.05s">
      <div class="glass-panel rounded-2xl p-5 flex items-center gap-4 depth-1">
        <div class="w-12 h-12 rounded-2xl bg-error/10 flex items-center justify-center text-error">
          <span class="material-symbols-outlined text-2xl">warning</span>
        </div>
        <div>
          <p class="text-xs text-slate-500 font-semibold uppercase tracking-widest">敏感词总数</p>
          <h3 class="font-[Plus_Jakarta_Sans] text-2xl font-bold">{{ wordTotal }}</h3>
        </div>
      </div>
      <div class="glass-panel rounded-2xl p-5 flex items-center gap-4 depth-1">
        <div class="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500">
          <span class="material-symbols-outlined text-2xl">pending_actions</span>
        </div>
        <div>
          <p class="text-xs text-slate-500 font-semibold uppercase tracking-widest">待处理</p>
          <h3 class="font-[Plus_Jakarta_Sans] text-2xl font-bold">{{ pendingTotal }}</h3>
        </div>
      </div>
      <div class="glass-panel rounded-2xl p-5 flex items-center gap-4 depth-1">
        <div class="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
          <span class="material-symbols-outlined text-2xl">check_circle</span>
        </div>
        <div>
          <p class="text-xs text-slate-500 font-semibold uppercase tracking-widest">已处理</p>
          <h3 class="font-[Plus_Jakarta_Sans] text-2xl font-bold">{{ processedTotal }}</h3>
        </div>
      </div>
      <div class="glass-panel rounded-2xl p-5 flex items-center gap-4 depth-1">
        <div class="w-12 h-12 rounded-2xl bg-tertiary/10 flex items-center justify-center text-tertiary">
          <span class="material-symbols-outlined text-2xl">shield</span>
        </div>
        <div>
          <p class="text-xs text-slate-500 font-semibold uppercase tracking-widest">违规记录总数</p>
          <h3 class="font-[Plus_Jakarta_Sans] text-2xl font-bold">{{ recordTotal }}</h3>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-2 animate-float-up" style="animation-delay: 0.1s">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="switchTab(tab.key)"
        class="flex items-center gap-2 px-6 py-2.5 rounded-full text-sm font-[Plus_Jakarta_Sans] font-semibold transition-all duration-300"
        :class="activeTab === tab.key
          ? 'bg-primary-container text-white shadow-lg shadow-primary-container/30'
          : 'glass-panel text-on-surface-variant hover:bg-white/40'"
      >
        <span class="material-symbols-outlined text-lg">{{ tab.icon }}</span>
        {{ tab.label }}
      </button>
    </div>

    <!-- Sensitive Words Tab -->
    <div v-if="activeTab === 'words'" class="space-y-4 animate-float-up" style="animation-delay: 0.15s">
      <!-- Search + Add -->
      <div class="glass-panel rounded-2xl p-4 flex flex-wrap items-center gap-4">
        <div class="relative flex-1 min-w-[200px]">
          <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">search</span>
          <input v-model="wordSearch" type="text" placeholder="搜索敏感词..." @keyup.enter="handleSearch"
            class="w-full bg-white/50 border border-white/40 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all" />
        </div>
        <el-select v-model="categoryFilter" placeholder="分类" clearable style="width: 120px">
          <el-option label="垃圾广告" value="spam" />
          <el-option label="欺诈" value="fraud" />
          <el-option label="暴力" value="violent" />
          <el-option label="其他" value="other" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 110px">
          <el-option label="启用" :value="1" />
          <el-option label="禁用" :value="0" />
        </el-select>
        <button class="bg-primary-container text-white rounded-2xl px-6 py-2.5 font-bold shadow-lg btn-jelly text-sm" @click="handleSearch">搜索</button>
        <button class="glass-panel rounded-2xl px-6 py-2.5 text-on-surface-variant hover:bg-white/20 transition-all text-sm" @click="handleReset">重置</button>
        <button class="bg-primary text-white rounded-2xl px-6 py-2.5 font-bold shadow-lg btn-jelly text-sm flex items-center gap-2" @click="openAddWord">
          <span class="material-symbols-outlined text-lg">add</span>添加敏感词
        </button>
      </div>

      <!-- Words Table -->
      <div class="glass-panel rounded-3xl overflow-hidden depth-2">
        <el-table :data="wordData" stripe style="width: 100%">
          <el-table-column prop="word" label="敏感词" min-width="160" />
          <el-table-column label="分类" width="120">
            <template #default="{ row }">
              <span class="text-sm">{{ categoryLabel(row.category) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="风险等级" width="120">
            <template #default="{ row }">
              <span :class="levelColor(row.level)" class="px-3 py-1 rounded-full text-[11px] font-bold">{{ levelLabel(row.level) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="hitCount" label="命中次数" min-width="100" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <span :class="Number(row.status) === 1 ? 'badge-success' : 'badge-info'" class="px-3 py-1 rounded-full text-[11px] font-bold">
                {{ Number(row.status) === 1 ? '启用' : '禁用' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="添加时间" min-width="160" />
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <div class="flex items-center gap-1">
                <button @click="openEditWord(row)" class="p-2 rounded-lg hover:bg-primary/10 text-slate-400 hover:text-primary transition-all">
                  <span class="material-symbols-outlined text-lg">edit</span>
                </button>
                <button @click="removeWord(row)" class="p-2 rounded-lg hover:bg-red-50 text-slate-400 hover:text-error transition-all">
                  <span class="material-symbols-outlined text-lg">delete</span>
                </button>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="flex justify-end">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" @current-change="handleCurrentChange" @size-change="handleSizeChange" />
      </div>
    </div>

    <!-- Violations Tab -->
    <div v-if="activeTab === 'violations'" class="space-y-4 animate-float-up" style="animation-delay: 0.15s">
      <div class="glass-panel rounded-2xl p-4 flex flex-wrap items-center gap-4">
        <el-select v-model="recordStatusFilter" placeholder="状态" clearable style="width: 120px">
          <el-option label="待处理" :value="0" />
          <el-option label="已处理" :value="1" />
        </el-select>
        <el-select v-model="recordTypeFilter" placeholder="类型" clearable style="width: 120px">
          <el-option label="帖子" value="post" />
          <el-option label="评论" value="comment" />
        </el-select>
        <button class="bg-primary-container text-white rounded-2xl px-6 py-2.5 font-bold shadow-lg btn-jelly text-sm" @click="handleRecordSearch">搜索</button>
        <button class="glass-panel rounded-2xl px-6 py-2.5 text-on-surface-variant hover:bg-white/20 transition-all text-sm" @click="handleRecordReset">重置</button>
      </div>

      <div class="glass-panel rounded-3xl overflow-hidden depth-2">
        <el-table :data="violationData" stripe style="width: 100%">
          <el-table-column label="类型" width="80">
            <template #default="{ row }">
              <span class="flex items-center gap-1 text-sm">
                <span class="material-symbols-outlined text-base" :class="row.targetType === 'post' ? 'text-primary' : 'text-tertiary'">
                  {{ row.targetType === 'post' ? 'article' : 'chat_bubble' }}
                </span>
                {{ targetLabel(row.targetType) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="违规内容" min-width="250" show-overflow-tooltip>
            <template #default="{ row }">
              <p class="text-sm truncate">{{ row.contentSnapshot }}</p>
            </template>
          </el-table-column>
          <el-table-column label="发布者" width="110">
            <template #default="{ row }">
              <span class="text-xs text-slate-500">#{{ row.authorId }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="word" label="命中词" width="110" />
          <el-table-column prop="reason" label="违规原因" width="150" show-overflow-tooltip />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <span :class="Number(row.status) === 1 ? 'badge-success' : 'badge-warning'" class="px-3 py-1 rounded-full text-[11px] font-bold">
                {{ statusLabel(row.status) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="发现时间" width="160" />
          <el-table-column label="操作" width="130" fixed="right">
            <template #default="{ row }">
              <button v-if="Number(row.status) !== 1" @click="markHandled(row)" class="px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-bold hover:scale-105 transition-all btn-jelly">
                标记已处理
              </button>
              <span v-else class="text-xs text-slate-400">已处理</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="flex justify-end">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" @current-change="handleCurrentChange" @size-change="handleSizeChange" />
      </div>
    </div>

    <!-- Word Dialog -->
    <el-dialog v-model="showWordDialog" :title="dialogTitle" width="480px" :close-on-click-modal="false">
      <div class="space-y-5">
        <div class="space-y-2">
          <label class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant uppercase tracking-widest">敏感词</label>
          <input v-model="wordForm.word" class="glass-input w-full rounded-xl px-4 py-3 text-sm" placeholder="输入敏感词..." />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <label class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant uppercase tracking-widest">分类</label>
            <el-select v-model="wordForm.category" style="width: 100%">
              <el-option label="垃圾广告" value="spam" />
              <el-option label="欺诈" value="fraud" />
              <el-option label="暴力" value="violent" />
              <el-option label="其他" value="other" />
            </el-select>
          </div>
          <div class="space-y-2">
            <label class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant uppercase tracking-widest">风险等级</label>
            <el-select v-model="wordForm.level" style="width: 100%">
              <el-option label="严重" value="critical" />
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </div>
        </div>
        <div v-if="editingId != null" class="space-y-2">
          <label class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant uppercase tracking-widest">状态</label>
          <el-select v-model="wordForm.status" style="width: 100%">
            <el-option label="启用" :value="1" />
            <el-option label="禁用" :value="0" />
          </el-select>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button @click="showWordDialog = false" class="px-6 py-2.5 rounded-xl text-sm text-on-surface-variant hover:bg-white/30 transition-all">取消</button>
          <button @click="submitWord" :disabled="submitting" class="px-8 py-2.5 rounded-xl bg-primary text-white text-sm font-bold btn-jelly shadow-lg disabled:opacity-50">
            {{ editingId == null ? '确认添加' : '保存修改' }}
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>
