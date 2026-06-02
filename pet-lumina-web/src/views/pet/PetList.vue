<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { petApi } from '@/api/pet'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Pet } from '@/types'

const loading = ref(false)
const tableData = ref<Pet[]>([])
const searchText = ref('')
const typeFilter = ref('')
const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const params: any = { current: currentPage.value, pageSize: pageSize.value }
    if (searchText.value) params.searchText = searchText.value
    if (typeFilter.value) params.type = typeFilter.value
    const res = await petApi.listPage(params) as any
    tableData.value = res?.records || []
    total.value = res?.total || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleReset = () => { searchText.value = ''; typeFilter.value = ''; currentPage.value = 1; fetchData() }

const handleDelete = async (pet: Pet) => {
  try {
    await ElMessageBox.confirm(`确定要删除宠物「${pet.name}」吗？`, '确认删除', { type: 'warning' })
    await petApi.delete(pet.id)
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
          placeholder="名字/主人/品种"
          class="w-full bg-white/15 backdrop-blur-[10px] border border-white/30 rounded-full pl-11 pr-4 py-3 text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container/50 outline-none transition-all text-sm"
          @keyup.enter="handleSearch"
        />
      </div>
      <el-select v-model="typeFilter" placeholder="宠物类型" clearable style="width: 120px">
        <el-option label="狗" value="狗" />
        <el-option label="猫" value="猫" />
        <el-option label="其他" value="其他" />
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
        <el-table-column prop="id" label="ID" width="100" />
        <el-table-column prop="name" label="名字" width="120" />
        <el-table-column prop="type" label="类型" width="80" />
        <el-table-column prop="breed" label="品种" width="120" />
        <el-table-column label="主人" width="120">
          <template #default="{ row }">{{ row.user?.nickname || '-' }}</template>
        </el-table-column>
        <el-table-column prop="healthScore" label="健康分数" width="100" />
        <el-table-column prop="todaySteps" label="今日步数" width="100" />
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
