<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { healthApi } from '@/api/health'
import { usePagination } from '@/composables/usePagination'
import HealthDetail from './HealthDetail.vue'
import type { HealthRecord } from '@/types'

const route = useRoute()
const loading = ref(false)
const tableData = ref<HealthRecord[]>([])
const searchText = ref('')
const moodFilter = ref('')
const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

const showDrawer = ref(false)
const selectedRecordId = ref<number>(0)

async function fetchData() {
  loading.value = true
  try {
    const params: any = { current: currentPage.value, pageSize: pageSize.value }
    if (moodFilter.value) params.mood = moodFilter.value
    if (searchText.value) params.petId = searchText.value
    else if (route.query.petId) params.petId = route.query.petId
    const res = await healthApi.listRecords(params) as any
    tableData.value = res?.records || []
    total.value = res?.total || 0
  } catch (e) { console.error(e) } finally { loading.value = false }
}

onMounted(() => {
  if (route.query.petId) {
    searchText.value = route.query.petId as string
  }
  fetchData()
})
const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleReset = () => { searchText.value = ''; moodFilter.value = ''; currentPage.value = 1; fetchData() }

const viewDetail = (record: HealthRecord) => {
  selectedRecordId.value = record.id
  showDrawer.value = true
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
          placeholder="搜索宠物ID"
          class="w-full bg-white/15 backdrop-blur-[10px] border border-white/30 rounded-full pl-11 pr-4 py-3 text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container/50 outline-none transition-all text-sm"
          @keyup.enter="handleSearch"
        />
      </div>
      <el-select v-model="moodFilter" placeholder="心情" clearable style="width: 120px">
        <el-option label="开心" value="开心" />
        <el-option label="平静" value="平静" />
        <el-option label="疲惫" value="疲惫" />
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
        <el-table-column prop="petId" label="宠物ID" width="80" />
        <el-table-column prop="date" label="日期" width="120" />
        <el-table-column prop="heartRate" label="心率" width="70" />
        <el-table-column prop="sleepHours" label="睡眠(h)" width="80" />
        <el-table-column prop="steps" label="步数" width="80" />
        <el-table-column prop="calories" label="消耗" width="70" />
        <el-table-column prop="weight" label="体重" width="70" />
        <el-table-column prop="mood" label="心情" width="70" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end mt-6">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" @current-change="handleCurrentChange" @size-change="handleSizeChange" />
      </div>
    </div>

    <HealthDetail v-model:visible="showDrawer" :record-id="selectedRecordId" />
  </div>
</template>
