<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import PageHeader from '@/components/common/PageHeader.vue'
import { getAdminUsage, listAdminSessions, type AdminSessionItem, type AdminUsage } from '@/api/agent'

const router = useRouter()

const loading = ref(false)
const rows = ref<AdminSessionItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const filters = ref({ userId: '', keyword: '' })
const usage = ref<AdminUsage | null>(null)

async function load() {
  loading.value = true
  try {
    const data = await listAdminSessions({
      page: page.value,
      page_size: pageSize.value,
      user_id: filters.value.userId.trim() || undefined,
      q: filters.value.keyword.trim() || undefined,
    })
    rows.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error((error as Error).message)
    rows.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

async function loadUsage() {
  try {
    usage.value = await getAdminUsage(7)
  } catch {
    // 用量只是辅助信息，失败不打断主列表
    usage.value = null
  }
}

function search() {
  page.value = 1
  load()
}

function reset() {
  filters.value = { userId: '', keyword: '' }
  search()
}

function openDetail(row: AdminSessionItem) {
  router.push(`/agent/sessions/${row.id}`)
}

onMounted(() => {
  load()
  loadUsage()
})
</script>

<template>
  <div class="space-y-8">
    <PageHeader
      title="会话工作台"
      subtitle="每一轮对话都可回溯：谁问的、调了哪些工具、引用了哪条记录、花了多少 token"
      icon="forum"
    />

    <div v-if="usage" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="glass-panel rounded-2xl p-5">
        <p class="text-xs text-on-surface-variant mb-1">近 {{ usage.days }} 天对话数</p>
        <p class="text-2xl font-bold text-primary">{{ usage.runs }}</p>
      </div>
      <div class="glass-panel rounded-2xl p-5">
        <p class="text-xs text-on-surface-variant mb-1">活跃用户</p>
        <p class="text-2xl font-bold text-primary">{{ usage.users }}</p>
      </div>
      <div class="glass-panel rounded-2xl p-5">
        <p class="text-xs text-on-surface-variant mb-1">消耗 token</p>
        <p class="text-2xl font-bold text-primary">{{ usage.total_tokens.toLocaleString() }}</p>
      </div>
      <div class="glass-panel rounded-2xl p-5">
        <p class="text-xs text-on-surface-variant mb-1">平均延迟</p>
        <p class="text-2xl font-bold text-primary">{{ usage.avg_latency_ms }} ms</p>
      </div>
    </div>

    <div class="glass-panel rounded-2xl p-6">
      <div class="flex flex-wrap items-end gap-4 mb-6">
        <div>
          <label class="block text-xs text-on-surface-variant mb-1">用户 ID</label>
          <el-input v-model="filters.userId" placeholder="精确匹配，如 1001" clearable style="width: 180px" />
        </div>
        <div>
          <label class="block text-xs text-on-surface-variant mb-1">会话标题</label>
          <el-input
            v-model="filters.keyword"
            placeholder="标题关键词"
            clearable
            style="width: 220px"
            @keyup.enter="search"
          />
        </div>
        <el-button type="primary" :loading="loading" @click="search">查询</el-button>
        <el-button @click="reset">重置</el-button>
        <span class="ml-auto text-xs text-on-surface-variant">共 {{ total }} 个会话</span>
      </div>

      <el-table :data="rows" v-loading="loading" row-key="id" @row-click="openDetail">
        <el-table-column prop="id" label="会话 ID" width="220" show-overflow-tooltip />
        <el-table-column prop="user_id" label="用户 ID" width="120" />
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column prop="channel" label="通道" width="100" />
        <el-table-column prop="message_count" label="消息数" width="100" />
        <el-table-column prop="create_time" label="创建时间" width="200" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button link type="primary" @click.stop="openDetail(row)">查看</el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="还没有对话；去 App 里问 Lumina 一句就有一条" />
        </template>
      </el-table>

      <div class="flex justify-end mt-4">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @current-change="load"
          @size-change="search"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.el-table) {
  background: transparent;
}

:deep(.el-table tr) {
  cursor: pointer;
}
</style>
