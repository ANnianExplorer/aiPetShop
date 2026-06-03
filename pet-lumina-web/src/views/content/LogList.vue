<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { logApi } from '@/api/log'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { LogEntry } from '@/types'

const router = useRouter()
const loading = ref(false)
const tableData = ref<LogEntry[]>([])
const searchText = ref('')
const typeFilter = ref('')
const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const params: any = { current: currentPage.value, pageSize: pageSize.value }
    if (searchText.value) params.searchText = searchText.value
    if (typeFilter.value) params.type = typeFilter.value
    const res = await logApi.listPage(params) as any
    tableData.value = res?.records || []
    total.value = res?.total || 0
  } catch (e) { console.error(e) } finally { loading.value = false }
}

onMounted(fetchData)
const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleReset = () => { searchText.value = ''; typeFilter.value = ''; currentPage.value = 1; fetchData() }

const typeConfig = (type: string) => {
  const map: Record<string, { label: string; icon: string; bg: string; color: string }> = {
    feeding: { label: '饮食记录', icon: 'restaurant', bg: 'bg-orange-50', color: 'text-orange-600' },
    walking: { label: '运动记录', icon: 'directions_run', bg: 'bg-blue-50', color: 'text-blue-600' },
    grooming: { label: '美容记录', icon: 'content_cut', bg: 'bg-pink-50', color: 'text-pink-600' },
    medical: { label: '医疗记录', icon: 'medical_services', bg: 'bg-red-50', color: 'text-red-600' },
    other: { label: '其他', icon: 'note', bg: 'bg-gray-50', color: 'text-gray-600' },
  }
  return map[type] || map.other
}

const handleDelete = async (log: LogEntry) => {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '确认删除', { type: 'warning' })
    await logApi.delete(log.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const viewDetail = (log: LogEntry) => {
  router.push(`/log/${log.id}`)
}
</script>

<template>
  <div v-loading="loading">
    <!-- Header -->
    <div class="flex flex-col md:flex-row justify-between items-end gap-6 mb-8 animate-float-up">
      <div>
        <h2 class="font-[Plus_Jakarta_Sans] text-[32px] font-bold text-primary tracking-tight">生活记录管理</h2>
        <p class="text-on-surface-variant mt-2">追踪与分析每一位毛孩子的成长瞬间与健康状态。</p>
      </div>
      <div class="flex items-center gap-4">
        <div class="glass-panel rounded-2xl px-6 py-4 flex items-center gap-4 depth-1">
          <div class="w-12 h-12 rounded-full bg-primary-fixed flex items-center justify-center">
            <span class="material-symbols-outlined text-primary glow-icon">description</span>
          </div>
          <div>
            <p class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold">记录总数</p>
            <p class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-primary">{{ total.toLocaleString() }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="glass-panel rounded-2xl p-4 flex flex-wrap items-center gap-4 mb-8 animate-float-up" style="animation-delay: 0.1s">
      <div class="relative flex-1 min-w-[200px]">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">search</span>
        <input v-model="searchText" type="text" placeholder="搜索标题..."
          class="w-full bg-white/50 border border-white/40 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
          @keyup.enter="handleSearch" />
      </div>
      <el-select v-model="typeFilter" placeholder="类型" clearable style="width: 130px">
        <el-option label="喂养" value="feeding" />
        <el-option label="散步" value="walking" />
        <el-option label="美容" value="grooming" />
        <el-option label="医疗" value="medical" />
      </el-select>
      <button class="bg-primary-container text-white rounded-2xl px-6 py-2.5 font-bold shadow-lg btn-jelly text-sm" @click="handleSearch">搜索</button>
      <button class="glass-panel rounded-2xl px-6 py-2.5 text-on-surface-variant hover:bg-white/20 transition-all text-sm" @click="handleReset">重置</button>
    </div>

    <!-- Record Cards -->
    <div class="space-y-5 mb-8">
      <div
        v-for="(log, index) in tableData"
        :key="log.id"
        class="glass-panel-heavy rounded-[32px] p-6 flex flex-col md:flex-row gap-6 depth-1 hover:depth-2 transition-all duration-400 animate-float-up cursor-pointer group"
        :style="{ animationDelay: `${0.15 + index * 0.06}s` }"
        @click="viewDetail(log)"
      >
        <!-- Date Badge -->
        <div class="md:w-40 shrink-0">
          <div class="p-4 bg-white/30 rounded-2xl border border-white/30 text-center">
            <p class="text-xs text-primary font-bold uppercase tracking-widest font-[Plus_Jakarta_Sans]">{{ log.createTime?.split(' ')[0] || '-' }}</p>
            <p class="font-[Plus_Jakarta_Sans] text-2xl font-bold mt-1 text-on-surface">{{ log.type ? typeConfig(log.type).label : '记录' }}</p>
          </div>
        </div>

        <!-- Content -->
        <div class="flex-1 space-y-3">
          <div class="flex justify-between items-start">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-full bg-primary-container/20 flex items-center justify-center">
                <span class="material-symbols-outlined text-primary-container">pets</span>
              </div>
              <div>
                <h4 class="font-[Plus_Jakarta_Sans] font-semibold text-base text-on-surface">{{ log.title || '生活记录' }}</h4>
                <span class="px-3 py-1 rounded-full text-xs font-bold mt-1 inline-flex items-center gap-1"
                  :class="[typeConfig(log.type || 'other').bg, typeConfig(log.type || 'other').color]">
                  <span class="material-symbols-outlined text-[14px]">{{ typeConfig(log.type || 'other').icon }}</span>
                  {{ typeConfig(log.type || 'other').label }}
                </span>
              </div>
            </div>
            <button class="p-2 rounded-xl bg-primary/5 text-primary hover:bg-primary hover:text-white transition-all opacity-0 group-hover:opacity-100" @click.stop>
              <span class="material-symbols-outlined">more_horiz</span>
            </button>
          </div>
          <p class="text-sm text-on-surface-variant leading-relaxed line-clamp-2">{{ log.content || '暂无描述' }}</p>
          <div class="pt-2 flex justify-end">
            <button class="flex items-center gap-2 px-5 py-2 bg-primary text-white rounded-full text-xs font-bold shadow-lg shadow-primary/20 btn-jelly" @click.stop="viewDetail(log)">
              查看详情
              <span class="material-symbols-outlined text-sm">arrow_forward</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-if="!loading && tableData.length === 0" class="glass-panel rounded-3xl p-16 text-center">
        <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">description</span>
        <p class="text-on-surface-variant text-lg">暂无记录</p>
      </div>
    </div>

    <!-- Pagination -->
    <div class="flex justify-center animate-float-up" style="animation-delay: 0.4s">
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[5,10,20]" layout="total, sizes, prev, pager, next" @current-change="handleCurrentChange" @size-change="handleSizeChange" />
    </div>

    <!-- FAB -->
    <button class="fab animate-scale-in" style="animation-delay: 0.6s">
      <span class="material-symbols-outlined text-[28px]">add</span>
    </button>
  </div>
</template>
