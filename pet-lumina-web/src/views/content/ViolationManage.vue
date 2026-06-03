<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const activeTab = ref('words')

// Sensitive words
const wordData = ref([
  { id: 1, word: '广告推销', category: 'spam', level: 'high', hitCount: 128, status: 'active', createTime: '2024-01-15' },
  { id: 2, word: '加微信', category: 'spam', level: 'high', hitCount: 96, status: 'active', createTime: '2024-01-15' },
  { id: 3, word: '免费领养', category: 'fraud', level: 'medium', hitCount: 64, status: 'active', createTime: '2024-02-03' },
  { id: 4, word: '低价转让', category: 'fraud', level: 'medium', hitCount: 45, status: 'active', createTime: '2024-02-10' },
  { id: 5, word: '虐待', category: 'violent', level: 'critical', hitCount: 12, status: 'active', createTime: '2024-03-01' },
  { id: 6, word: '毒杀', category: 'violent', level: 'critical', hitCount: 5, status: 'active', createTime: '2024-03-01' },
])

// Violation records
const violationData = ref([
  { id: 1, type: 'post', content: '加微信免费领养名贵品种猫...', author: '小明', reason: '疑似诈骗信息', status: 'pending', createTime: '2024-03-20 14:30' },
  { id: 2, type: 'comment', content: '这个价格太便宜了，加我QQ...', author: '匿名用户', reason: '广告引流', status: 'processed', createTime: '2024-03-19 09:15' },
  { id: 3, type: 'post', content: '低价转让纯种金毛，有意者联系...', author: '宠物贩子', reason: '疑似非法交易', status: 'pending', createTime: '2024-03-18 21:45' },
  { id: 4, type: 'comment', content: '虐待动物的都应该...', author: '愤怒市民', reason: '暴力言论', status: 'processed', createTime: '2024-03-17 16:20' },
])

const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

const wordSearch = ref('')
const categoryFilter = ref('')
const showAddWord = ref(false)
const newWord = ref({ word: '', category: 'spam', level: 'medium' })

async function fetchData() {
  loading.value = true
  try {
    // TODO: call API
    total.value = activeTab.value === 'words' ? wordData.value.length : violationData.value.length
  } catch (e) { console.error(e) } finally { loading.value = false }
}

onMounted(fetchData)

const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleReset = () => { wordSearch.value = ''; categoryFilter.value = ''; currentPage.value = 1; fetchData() }

const addWord = () => {
  if (!newWord.value.word) { ElMessage.warning('请输入敏感词'); return }
  wordData.value.unshift({
    id: Date.now(),
    word: newWord.value.word,
    category: newWord.value.category,
    level: newWord.value.level,
    hitCount: 0,
    status: 'active',
    createTime: new Date().toISOString().substring(0, 10),
  })
  showAddWord.value = false
  newWord.value = { word: '', category: 'spam', level: 'medium' }
  ElMessage.success('敏感词已添加')
}

const removeWord = async (word: any) => {
  try {
    await ElMessageBox.confirm(`确定删除敏感词「${word.word}」？`, '确认删除', { type: 'warning' })
    wordData.value = wordData.value.filter(w => w.id !== word.id)
    ElMessage.success('已删除')
  } catch {}
}

const handleViolation = async (record: any, action: string) => {
  try {
    await ElMessageBox.confirm(`确定${action === 'ignore' ? '忽略' : '处理'}此违规记录？`, '确认操作', { type: 'warning' })
    record.status = 'processed'
    ElMessage.success('操作成功')
  } catch {}
}

const levelLabel = (level: string) => ({ critical: '严重', high: '高', medium: '中', low: '低' }[level] || level)
const levelColor = (level: string) => ({ critical: 'badge-error', high: 'badge-warning', medium: 'badge-info', low: 'badge-info' }[level] || 'badge-info')
const categoryLabel = (cat: string) => ({ spam: '垃圾广告', fraud: '欺诈', violent: '暴力', other: '其他' }[cat] || cat)
const statusLabel = (s: string) => s === 'pending' ? '待处理' : '已处理'
</script>

<template>
  <div v-loading="loading" class="space-y-6">
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
          <h3 class="font-[Plus_Jakarta_Sans] text-2xl font-bold">{{ wordData.length }}</h3>
        </div>
      </div>
      <div class="glass-panel rounded-2xl p-5 flex items-center gap-4 depth-1">
        <div class="w-12 h-12 rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500">
          <span class="material-symbols-outlined text-2xl">pending_actions</span>
        </div>
        <div>
          <p class="text-xs text-slate-500 font-semibold uppercase tracking-widest">待处理</p>
          <h3 class="font-[Plus_Jakarta_Sans] text-2xl font-bold">{{ violationData.filter(v => v.status === 'pending').length }}</h3>
        </div>
      </div>
      <div class="glass-panel rounded-2xl p-5 flex items-center gap-4 depth-1">
        <div class="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary">
          <span class="material-symbols-outlined text-2xl">check_circle</span>
        </div>
        <div>
          <p class="text-xs text-slate-500 font-semibold uppercase tracking-widest">已处理</p>
          <h3 class="font-[Plus_Jakarta_Sans] text-2xl font-bold">{{ violationData.filter(v => v.status === 'processed').length }}</h3>
        </div>
      </div>
      <div class="glass-panel rounded-2xl p-5 flex items-center gap-4 depth-1">
        <div class="w-12 h-12 rounded-2xl bg-tertiary/10 flex items-center justify-center text-tertiary">
          <span class="material-symbols-outlined text-2xl">shield</span>
        </div>
        <div>
          <p class="text-xs text-slate-500 font-semibold uppercase tracking-widest">拦截命中</p>
          <h3 class="font-[Plus_Jakarta_Sans] text-2xl font-bold">{{ wordData.reduce((s, w) => s + w.hitCount, 0) }}</h3>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="flex gap-2 animate-float-up" style="animation-delay: 0.1s">
      <button
        v-for="tab in [{ key: 'words', label: '敏感词库', icon: 'block' }, { key: 'violations', label: '违规记录', icon: 'report' }]"
        :key="tab.key"
        @click="activeTab = tab.key; fetchData()"
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
        </el-select>
        <button class="bg-primary-container text-white rounded-2xl px-6 py-2.5 font-bold shadow-lg btn-jelly text-sm" @click="handleSearch">搜索</button>
        <button class="glass-panel rounded-2xl px-6 py-2.5 text-on-surface-variant hover:bg-white/20 transition-all text-sm" @click="handleReset">重置</button>
        <button class="bg-primary text-white rounded-2xl px-6 py-2.5 font-bold shadow-lg btn-jelly text-sm flex items-center gap-2" @click="showAddWord = true">
          <span class="material-symbols-outlined text-lg">add</span>添加敏感词
        </button>
      </div>

      <!-- Words Table -->
      <div class="glass-panel rounded-3xl overflow-hidden depth-2">
        <el-table :data="wordData" stripe>
          <el-table-column prop="word" label="敏感词" width="160" />
          <el-table-column label="分类" width="100">
            <template #default="{ row }">
              <span class="text-sm">{{ categoryLabel(row.category) }}</span>
            </template>
          </el-table-column>
          <el-table-column label="风险等级" width="100">
            <template #default="{ row }">
              <span :class="levelColor(row.level)" class="px-3 py-1 rounded-full text-[11px] font-bold">{{ levelLabel(row.level) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="hitCount" label="命中次数" width="100" />
          <el-table-column label="状态" width="80">
            <template #default="{ row }">
              <span :class="row.status === 'active' ? 'badge-success' : 'badge-info'" class="px-3 py-1 rounded-full text-[11px] font-bold">
                {{ row.status === 'active' ? '启用' : '禁用' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="添加时间" width="120" />
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <button @click="removeWord(row)" class="p-2 rounded-lg hover:bg-red-50 text-slate-400 hover:text-error transition-all">
                <span class="material-symbols-outlined text-lg">delete</span>
              </button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- Violations Tab -->
    <div v-if="activeTab === 'violations'" class="space-y-4 animate-float-up" style="animation-delay: 0.15s">
      <div class="glass-panel rounded-3xl overflow-hidden depth-2">
        <el-table :data="violationData" stripe>
          <el-table-column label="类型" width="80">
            <template #default="{ row }">
              <span class="flex items-center gap-1 text-sm">
                <span class="material-symbols-outlined text-base" :class="row.type === 'post' ? 'text-primary' : 'text-tertiary'">
                  {{ row.type === 'post' ? 'article' : 'chat_bubble' }}
                </span>
                {{ row.type === 'post' ? '帖子' : '评论' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="违规内容" min-width="250">
            <template #default="{ row }">
              <p class="text-sm truncate">{{ row.content }}</p>
            </template>
          </el-table-column>
          <el-table-column prop="author" label="发布者" width="100" />
          <el-table-column prop="reason" label="违规原因" width="140" />
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <span :class="row.status === 'pending' ? 'badge-warning' : 'badge-success'" class="px-3 py-1 rounded-full text-[11px] font-bold">
                {{ statusLabel(row.status) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="createTime" label="发现时间" width="160" />
          <el-table-column label="操作" width="160" fixed="right">
            <template #default="{ row }">
              <div v-if="row.status === 'pending'" class="flex items-center gap-1">
                <button @click="handleViolation(row, 'process')" class="px-3 py-1.5 rounded-lg bg-primary text-white text-xs font-bold hover:scale-105 transition-all btn-jelly">
                  处理
                </button>
                <button @click="handleViolation(row, 'ignore')" class="px-3 py-1.5 rounded-lg glass-panel text-xs font-bold text-on-surface-variant hover:bg-white/40 transition-all">
                  忽略
                </button>
              </div>
              <span v-else class="text-xs text-slate-400">已处理</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="flex justify-end">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next" @current-change="handleCurrentChange" @size-change="handleSizeChange" />
      </div>
    </div>

    <!-- Add Word Dialog -->
    <el-dialog v-model="showAddWord" title="添加敏感词" width="480px" :close-on-click-modal="false">
      <div class="space-y-5">
        <div class="space-y-2">
          <label class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant uppercase tracking-widest">敏感词</label>
          <input v-model="newWord.word" class="glass-input w-full rounded-xl px-4 py-3 text-sm" placeholder="输入敏感词..." />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="space-y-2">
            <label class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant uppercase tracking-widest">分类</label>
            <el-select v-model="newWord.category" style="width: 100%">
              <el-option label="垃圾广告" value="spam" />
              <el-option label="欺诈" value="fraud" />
              <el-option label="暴力" value="violent" />
              <el-option label="其他" value="other" />
            </el-select>
          </div>
          <div class="space-y-2">
            <label class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant uppercase tracking-widest">风险等级</label>
            <el-select v-model="newWord.level" style="width: 100%">
              <el-option label="严重" value="critical" />
              <el-option label="高" value="high" />
              <el-option label="中" value="medium" />
              <el-option label="低" value="low" />
            </el-select>
          </div>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button @click="showAddWord = false" class="px-6 py-2.5 rounded-xl text-sm text-on-surface-variant hover:bg-white/30 transition-all">取消</button>
          <button @click="addWord" class="px-8 py-2.5 rounded-xl bg-primary text-white text-sm font-bold btn-jelly shadow-lg">确认添加</button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>
