<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { notificationApi } from '@/api/notification'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Notification } from '@/types'

const loading = ref(false)
const tableData = ref<Notification[]>([])
const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

// Dialog state
const showDialog = ref(false)
const isEditing = ref(false)
const editId = ref<number | null>(null)
const form = ref({
  title: '',
  content: '',
  type: 'system',
})

const notificationTypes = [
  { value: 'system', label: '系统通知' },
  { value: 'update', label: '更新公告' },
  { value: 'campaign', label: '活动通知' },
  { value: 'priority', label: '紧急通知' },
  { value: 'social', label: '社交通知' },
  { value: 'health', label: '健康提醒' },
]

async function fetchData() {
  loading.value = true
  try {
    const params = { current: currentPage.value, pageSize: pageSize.value }
    const res = await notificationApi.listPage(params) as any
    const records = res?.records || []
    console.log('[Notification] fetchData raw records:', records.map((r: any) => ({ id: r.id, title: r.title, status: r.status, statusType: typeof r.status })))
    tableData.value = records
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

const isPublished = (item: Notification) => {
  const s = item.status
  return s == null || s === 1
}

const openCreate = () => {
  isEditing.value = false
  editId.value = null
  form.value = { title: '', content: '', type: 'system' }
  showDialog.value = true
}

const openEdit = (item: Notification) => {
  isEditing.value = true
  editId.value = item.id
  form.value = { title: item.title || '', content: item.content || '', type: item.type || 'system' }
  showDialog.value = true
}

const handleSubmit = async () => {
  if (!form.value.title) { ElMessage.warning('请输入通知标题'); return }
  if (!form.value.content) { ElMessage.warning('请输入通知内容'); return }
  try {
    if (isEditing.value && editId.value) {
      await notificationApi.update({ id: editId.value, ...form.value })
      ElMessage.success('通知已更新')
    } else {
      await notificationApi.create(form.value)
      ElMessage.success('通知已发布')
    }
    showDialog.value = false
    fetchData()
  } catch { ElMessage.error('操作失败') }
}

const handleDelete = async (item: Notification) => {
  try {
    await ElMessageBox.confirm('确定要删除这条通知吗？', '确认删除', { type: 'warning' })
    await notificationApi.delete(item.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const handleToggleStatus = async (item: Notification) => {
  const currentStatus = item.status == null ? 1 : Number(item.status)
  const newStatus = currentStatus === 1 ? 0 : 1
  const label = newStatus === 1 ? '发布' : '取消发布'
  try {
    await ElMessageBox.confirm(`确定要${label}这条通知吗？`, '确认操作', { type: 'warning' })
  } catch { return }
  try {
    await notificationApi.toggleStatus(item.id, newStatus)
    // 直接更新本地数据，确保 Vue 响应式触发
    item.status = newStatus
    ElMessage.success(`已${label}`)
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  }
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
      <button @click="openCreate" class="flex items-center gap-2 bg-primary-container text-on-primary-container px-8 py-3.5 rounded-xl font-bold shadow-[0_10px_20px_-5px_rgba(109,175,146,0.3)] btn-jelly text-sm">
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
            <p class="text-sm text-on-surface-variant mb-2 line-clamp-1">{{ item.content }}</p>
            <div class="flex items-center gap-4">
              <span class="flex items-center gap-1.5 text-xs font-[Plus_Jakarta_Sans] text-slate-500">
                <span class="material-symbols-outlined text-sm">schedule</span>
                {{ item.createTime }}
              </span>
              <span class="px-2.5 py-0.5 rounded-full text-xs font-[Plus_Jakarta_Sans] font-semibold" :class="typeConfig(item.type).bg + ' ' + typeConfig(item.type).color">
                {{ notificationTypes.find(t => t.value === item.type)?.label || item.type }}
              </span>
              <span class="px-2.5 py-0.5 rounded-full text-xs font-[Plus_Jakarta_Sans] font-bold"
                :class="isPublished(item) ? 'badge-success' : 'badge-warning'">
                {{ isPublished(item) ? '已发布' : '草稿' }}
              </span>
            </div>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button @click="handleToggleStatus(item)"
            class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all btn-jelly"
            :class="isPublished(item) ? 'bg-amber-100 text-amber-700 hover:bg-amber-200' : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'">
            <span class="material-symbols-outlined text-base">{{ isPublished(item) ? 'toggle_off' : 'toggle_on' }}</span>
            {{ isPublished(item) ? '取消发布' : '发布' }}
          </button>
          <button @click="openEdit(item)" class="p-2.5 rounded-xl glass-card text-on-surface-variant hover:text-primary-container transition-colors" title="编辑">
            <span class="material-symbols-outlined">edit</span>
          </button>
          <button @click="handleDelete(item)" class="p-2.5 rounded-xl glass-card text-on-surface-variant hover:text-error transition-colors" title="删除">
            <span class="material-symbols-outlined">delete</span>
          </button>
        </div>
      </div>

      <div v-if="!loading && tableData.length === 0" class="glass-panel rounded-3xl p-16 text-center">
        <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">notifications_off</span>
        <p class="text-on-surface-variant text-lg">暂无通知</p>
      </div>
    </div>

    <!-- Pagination -->
    <div class="flex justify-center mb-20 animate-float-up" style="animation-delay: 0.4s">
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[5, 10, 20]" layout="total, sizes, prev, pager, next" @current-change="handleCurrentChange" @size-change="handleSizeChange" />
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog v-model="showDialog" :title="isEditing ? '编辑通知' : '发布新通知'" width="560px" :close-on-click-modal="false">
      <div class="space-y-5">
        <div class="space-y-2">
          <label class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant uppercase tracking-widest">通知标题</label>
          <input v-model="form.title" class="glass-input w-full rounded-xl px-4 py-3 text-sm" placeholder="输入通知标题..." />
        </div>
        <div class="space-y-2">
          <label class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant uppercase tracking-widest">通知类型</label>
          <el-select v-model="form.type" style="width: 100%">
            <el-option v-for="t in notificationTypes" :key="t.value" :label="t.label" :value="t.value" />
          </el-select>
        </div>
        <div class="space-y-2">
          <label class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant uppercase tracking-widest">通知内容</label>
          <textarea v-model="form.content" class="glass-input w-full rounded-xl px-4 py-3 text-sm resize-none" rows="5" placeholder="输入通知内容..." />
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button @click="showDialog = false" class="px-6 py-2.5 rounded-xl text-sm text-on-surface-variant hover:bg-white/30 transition-all">取消</button>
          <button @click="handleSubmit" class="px-8 py-2.5 rounded-xl bg-primary text-white text-sm font-bold btn-jelly shadow-lg">
            {{ isEditing ? '保存修改' : '确认发布' }}
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>
