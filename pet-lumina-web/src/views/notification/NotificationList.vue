<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { notificationApi } from '@/api/notification'
import { usePagination } from '@/composables/usePagination'
import type { Notification } from '@/types'

const loading = ref(false)
const tableData = ref<Notification[]>([])
const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const params = { current: currentPage.value, pageSize: pageSize.value }
    const res = await notificationApi.listPage(params) as any
    tableData.value = res?.records || []
    total.value = res?.total || 0
  } catch (e) { console.error(e) } finally { loading.value = false }
}

onMounted(fetchData)

const typeIcon = (type: string) => {
  const map: Record<string, string> = { reminder: 'notifications', social: 'group', health: 'medication', system: 'info' }
  return map[type] || 'info'
}
</script>

<template>
  <div class="space-y-5">
    <!-- Header -->
    <div class="glass-panel rounded-full px-6 py-4 flex items-center gap-3">
      <span class="material-symbols-outlined text-primary-container text-xl">notifications</span>
      <h2 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-sm">通知列表</h2>
    </div>

    <!-- Table -->
    <div class="glass-panel rounded-3xl p-6">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column label="类型" width="60">
          <template #default="{ row }">
            <span class="material-symbols-outlined text-primary-container text-lg">{{ typeIcon(row.type) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" width="150" />
        <el-table-column prop="content" label="内容" show-overflow-tooltip />
        <el-table-column prop="createTime" label="时间" width="160" />
        <el-table-column prop="isRead" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.isRead === 1 ? 'info' : 'warning'" size="small">
              {{ row.isRead === 1 ? '已读' : '未读' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end mt-6">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" @current-change="handleCurrentChange" @size-change="handleSizeChange" />
      </div>
    </div>
  </div>
</template>
