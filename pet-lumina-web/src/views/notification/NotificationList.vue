<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { notificationApi } from '@/api/notification'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
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

const typeConfig = (type: string) => {
  const map: Record<string, { icon: string; bg: string; color: string }> = {
    campaign: { icon: 'campaign', bg: 'bg-secondary-container/30', color: 'text-primary-container' },
    update: { icon: 'update', bg: 'bg-tertiary-container/30', color: 'text-tertiary' },
    draft: { icon: 'drafts', bg: 'bg-outline-variant/30', color: 'text-slate-400' },
    priority: { icon: 'priority_high', bg: 'bg-error-container/20', color: 'text-error' },
    new: { icon: 'new_releases', bg: 'bg-primary-container/20', color: 'text-primary-container' },
    reminder: { icon: 'notifications', bg: 'bg-secondary-container/30', color: 'text-primary-container' },
    social: { icon: 'group', bg: 'bg-primary-container/20', color: 'text-primary-container' },
    health: { icon: 'medication', bg: 'bg-tertiary-container/30', color: 'text-tertiary' },
    system: { icon: 'info', bg: 'bg-outline-variant/30', color: 'text-slate-400' },
  }
  return map[type] || map.system
}

const handleEdit = (item: Notification) => {
  ElMessage.info('编辑功能开发中')
}

const handleDelete = async (item: Notification) => {
  try {
    await ElMessageBox.confirm('确定要删除这条通知吗？', '确认删除', { type: 'warning' })
    await notificationApi.delete(item.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}
</script>

<template>
  <div v-loading="loading" class="max-w-screen-xl mx-auto">
    <!-- Header -->
    <div class="flex justify-between items-end mb-10 animate-float-up">
      <div>
        <h2 class="font-[Plus_Jakarta_Sans] text-[32px] font-bold text-on-surface mb-2">通知管理</h2>
        <p class="text-on-surface-variant max-w-2xl">发布全站公告、系统更新提示或向特定用户组发送私信，维持社区活力与合规。</p>
      </div>
      <button class="flex items-center gap-2 bg-primary-container text-on-primary-container px-8 py-3.5 rounded-xl font-bold shadow-[0_10px_20px_-5px_rgba(109,175,146,0.3)] btn-jelly text-sm">
        <span class="material-symbols-outlined">add_circle</span>
        <span>发布新通知</span>
      </button>
    </div>

    <!-- Notification Cards -->
    <div class="grid grid-cols-1 gap-5 mb-8">
      <div
        v-for="(item, index) in tableData"
        :key="item.id"
        class="glass-card p-6 rounded-3xl flex items-center justify-between group animate-float-up depth-1 hover:depth-2"
        :style="{ animationDelay: `${0.1 + index * 0.06}s` }"
      >
        <div class="flex items-start gap-5">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center" :class="typeConfig(item.type).bg">
            <span class="material-symbols-outlined text-3xl" :class="typeConfig(item.type).color">{{ typeConfig(item.type).icon }}</span>
          </div>
          <div>
            <h4 class="font-[Plus_Jakarta_Sans] font-semibold text-base text-on-surface mb-1">{{ item.title }}</h4>
            <div class="flex items-center gap-4">
              <span class="flex items-center gap-1.5 text-xs font-[Plus_Jakarta_Sans] text-slate-500">
                <span class="material-symbols-outlined text-sm">schedule</span>
                {{ item.createTime }}
              </span>
              <span
                class="px-2.5 py-0.5 rounded-full text-xs font-[Plus_Jakarta_Sans] font-semibold"
                :class="item.isRead === 1 ? 'bg-secondary-container text-on-secondary-container' : 'bg-surface-container-highest text-slate-600'"
              >
                {{ item.isRead === 1 ? '已发布' : '草稿箱' }}
              </span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button @click="handleEdit(item)" class="p-3 rounded-xl glass-card text-on-surface-variant hover:text-primary-container transition-colors">
            <span class="material-symbols-outlined">edit</span>
          </button>
          <button @click="handleDelete(item)" class="p-3 rounded-xl glass-card text-on-surface-variant hover:text-error transition-colors">
            <span class="material-symbols-outlined">delete</span>
          </button>
        </div>
      </div>

      <!-- Empty state -->
      <div v-if="!loading && tableData.length === 0" class="glass-panel rounded-3xl p-16 text-center">
        <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">notifications_off</span>
        <p class="text-on-surface-variant text-lg">暂无通知</p>
      </div>
    </div>

    <!-- Pagination -->
    <div class="flex justify-center mb-20 animate-float-up" style="animation-delay: 0.4s">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[5, 10, 20]"
        layout="total, sizes, prev, pager, next"
        @current-change="handleCurrentChange"
        @size-change="handleSizeChange"
      />
    </div>

    <!-- Floating Stats Overlay -->
    <div class="fixed bottom-8 right-8 z-40 animate-float-up" style="animation-delay: 0.6s">
      <div class="glass-panel-deep p-4 rounded-2xl flex items-center gap-6 shadow-2xl depth-3">
        <div class="text-center px-4 border-r border-white/20">
          <p class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold">总通知数</p>
          <p class="text-xl font-[Plus_Jakarta_Sans] font-bold text-primary-container animate-number-pop">{{ total.toLocaleString() }}</p>
        </div>
        <div class="text-center px-4 border-r border-white/20">
          <p class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold">本月新增</p>
          <p class="text-xl font-[Plus_Jakarta_Sans] font-bold text-primary-container animate-number-pop" style="animation-delay: 0.1s">42</p>
        </div>
        <div class="text-center px-4">
          <p class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold">触达率</p>
          <p class="text-xl font-[Plus_Jakarta_Sans] font-bold text-primary-container animate-number-pop" style="animation-delay: 0.2s">98.2%</p>
        </div>
      </div>
    </div>
  </div>
</template>
