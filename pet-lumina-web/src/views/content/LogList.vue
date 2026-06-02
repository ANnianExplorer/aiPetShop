<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logApi } from '@/api/log'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { LogEntry } from '@/types'

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

const typeLabel = (type: string) => {
  const map: Record<string, string> = { feeding: '喂养', walking: '散步', grooming: '美容', medical: '医疗', other: '其他' }
  return map[type] || type
}

const handleDelete = async (log: LogEntry) => {
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '确认删除', { type: 'warning' })
    await logApi.delete(log.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}
</script>

<template>
  <div class="space-y-5">
    <!-- Search Bar -->
    <div class="glass-panel rounded-full px-6 py-4 flex items-center gap-4 flex-wrap">
      <div class="relative flex-1 min-w-[200px]">
        <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg">search</span>
        <input
          v-model="searchText"
          type="text"
          placeholder="搜索标题"
          class="w-full bg-white/15 backdrop-blur-[10px] border border-white/30 rounded-full pl-11 pr-4 py-3 text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container/50 outline-none transition-all text-sm"
          @keyup.enter="handleSearch"
        />
      </div>
      <el-select v-model="typeFilter" placeholder="类型" clearable style="width: 120px">
        <el-option label="喂养" value="feeding" />
        <el-option label="散步" value="walking" />
        <el-option label="美容" value="grooming" />
        <el-option label="医疗" value="medical" />
        <el-option label="其他" value="other" />
      </el-select>
      <button class="bg-primary-container text-white rounded-2xl px-6 py-3 font-bold shadow-[0_10px_25px_-5px_rgba(109,175,146,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-200 text-sm" @click="handleSearch">
        搜索
      </button>
      <button class="glass-panel rounded-2xl px-6 py-3 text-on-surface-variant hover:bg-white/20 transition-all text-sm" @click="handleReset">
        重置
      </button>
    </div>

    <!-- Table -->
    <div class="glass-panel rounded-3xl p-6">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" show-overflow-tooltip />
        <el-table-column prop="type" label="类型" width="80">
          <template #default="{ row }">{{ typeLabel(row.type) }}</template>
        </el-table-column>
        <el-table-column label="作者" width="100">
          <template #default="{ row }">{{ row.user?.nickname || '-' }}</template>
        </el-table-column>
        <el-table-column prop="likes" label="点赞" width="70" />
        <el-table-column prop="createTime" label="时间" width="160" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end mt-6">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" @current-change="handleCurrentChange" @size-change="handleSizeChange" />
      </div>
    </div>
  </div>
</template>
