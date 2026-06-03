<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { postApi } from '@/api/post'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Post } from '@/types'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const tableData = ref<Post[]>([])
const searchText = ref('')
const categoryFilter = ref('')
const authorFilter = ref('')
const statusTab = ref('all')
const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const params: any = { current: currentPage.value, pageSize: pageSize.value }
    if (searchText.value) params.searchText = searchText.value
    if (categoryFilter.value) params.category = categoryFilter.value
    if (authorFilter.value) params.authorName = authorFilter.value
    const res = await postApi.listPage(params) as any
    tableData.value = res?.records || []
    total.value = res?.total || 0
  } catch (e) { console.error(e) } finally { loading.value = false }
}

onMounted(() => {
  if (route.query.author) {
    authorFilter.value = route.query.author as string
  }
  fetchData()
})
const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleReset = () => { searchText.value = ''; categoryFilter.value = ''; authorFilter.value = ''; statusTab.value = 'all'; currentPage.value = 1; fetchData() }

const filterByAuthor = (authorName: string) => {
  authorFilter.value = authorName
  currentPage.value = 1
  fetchData()
}

const clearAuthorFilter = () => {
  authorFilter.value = ''
  currentPage.value = 1
  fetchData()
}

const handleDelete = async (post: Post) => {
  try {
    await ElMessageBox.confirm('确定要删除这篇帖子吗？', '确认删除', { type: 'warning' })
    await postApi.delete(post.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const viewDetail = (post: Post) => {
  router.push(`/post/${post.id}`)
}

const statusTabs = [
  { key: 'all', label: '全部状态' },
  { key: 'pending', label: '待审核' },
  { key: 'published', label: '已发布' },
  { key: 'hidden', label: '已隐藏' },
]
</script>

<template>
  <div v-loading="loading">
    <!-- Header -->
    <div class="flex justify-between items-end mb-8 animate-float-up">
      <div>
        <h2 class="font-[Plus_Jakarta_Sans] text-[32px] font-bold text-primary mb-2">帖子管理</h2>
        <p class="text-on-surface-variant">审核、管理社区帖子内容</p>
      </div>
      <button class="flex items-center gap-2 bg-primary-container text-on-primary-container px-6 py-3 rounded-xl font-bold shadow-lg btn-jelly text-sm">
        <span class="material-symbols-outlined text-lg">post_add</span>
        快速审核
      </button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <div class="glass-panel rounded-2xl p-6 flex items-center justify-between depth-1 animate-float-up" style="animation-delay: 0.1s">
        <div>
          <p class="text-slate-500 text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-1">今日新帖</p>
          <div class="flex items-baseline gap-2">
            <h3 class="font-[Plus_Jakarta_Sans] text-[40px] font-bold text-primary">128</h3>
            <span class="text-xs text-emerald-600 font-bold flex items-center gap-1">
              <span class="material-symbols-outlined text-base">trending_up</span> +12%
            </span>
          </div>
        </div>
        <div class="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center text-emerald-600">
          <span class="material-symbols-outlined text-3xl">article</span>
        </div>
      </div>
      <div class="glass-panel rounded-2xl p-6 flex items-center justify-between depth-1 animate-float-up" style="animation-delay: 0.15s">
        <div>
          <p class="text-slate-500 text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-1">待审核</p>
          <h3 class="font-[Plus_Jakarta_Sans] text-[40px] font-bold text-amber-500">14</h3>
        </div>
        <div class="w-14 h-14 bg-amber-100 rounded-2xl flex items-center justify-center text-amber-600">
          <span class="material-symbols-outlined text-3xl">pending_actions</span>
        </div>
      </div>
    </div>

    <!-- Author Filter Banner -->
    <div v-if="authorFilter" class="glass-panel rounded-2xl p-4 flex items-center justify-between mb-4 animate-float-up border-l-4 border-primary-container">
      <div class="flex items-center gap-3">
        <span class="material-symbols-outlined text-primary-container">person_search</span>
        <span class="text-sm font-medium">正在查看作者「<strong class="text-primary">{{ authorFilter }}</strong>」的所有帖子</span>
      </div>
      <button @click="clearAuthorFilter" class="flex items-center gap-1 text-sm text-slate-500 hover:text-error transition-colors">
        <span class="material-symbols-outlined text-lg">close</span>清除筛选
      </button>
    </div>

    <!-- Search Bar -->
    <div class="glass-panel rounded-2xl p-4 flex flex-wrap items-center gap-4 mb-6 animate-float-up" style="animation-delay: 0.2s">
      <div class="relative flex-1 min-w-[200px]">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">search</span>
        <input v-model="searchText" type="text" placeholder="搜索帖子内容..."
          class="w-full bg-white/50 border border-white/40 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
          @keyup.enter="handleSearch" />
      </div>
      <el-select v-model="categoryFilter" placeholder="类别" clearable style="width: 120px">
        <el-option label="猫咪" value="猫咪" />
        <el-option label="狗狗" value="狗狗" />
        <el-option label="异宠" value="异宠" />
      </el-select>
      <button class="p-2.5 text-slate-400 hover:text-emerald-600 transition-colors" @click="handleSearch">
        <span class="material-symbols-outlined">filter_list</span>
      </button>
    </div>

    <!-- Status Tabs -->
    <div class="flex gap-2 mb-6 animate-float-up" style="animation-delay: 0.25s">
      <button v-for="tab in statusTabs" :key="tab.key"
        @click="statusTab = tab.key"
        class="px-5 py-2 rounded-full text-sm font-[Plus_Jakarta_Sans] font-semibold transition-all duration-300"
        :class="statusTab === tab.key
          ? 'bg-primary-container text-white shadow-lg shadow-primary-container/30'
          : 'glass-panel text-on-surface-variant hover:bg-white/40'"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Table -->
    <div class="glass-panel rounded-3xl overflow-hidden depth-2 animate-float-up" style="animation-delay: 0.3s">
      <el-table :data="tableData" stripe>
        <el-table-column label="帖子内容" min-width="250">
          <template #default="{ row }">
            <div class="flex items-center gap-3">
              <div class="w-12 h-12 rounded-xl bg-primary-container/15 flex items-center justify-center flex-shrink-0">
                <span class="material-symbols-outlined text-primary-container">article</span>
              </div>
              <div class="min-w-0">
                <p class="font-semibold text-sm text-on-surface truncate">{{ row.content?.substring(0, 30) || '无标题' }}...</p>
                <p class="text-xs text-on-surface-variant truncate">{{ row.category || '-' }}</p>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="作者" width="120">
          <template #default="{ row }">
            <div class="flex items-center gap-2 cursor-pointer group/author" @click="row.user?.nickname && filterByAuthor(row.user.nickname)">
              <div class="w-7 h-7 rounded-full bg-primary-container/20 flex items-center justify-center">
                <span class="material-symbols-outlined text-primary-container text-sm">person</span>
              </div>
              <span class="text-sm group-hover/author:text-primary group-hover/author:underline transition-colors">{{ row.user?.nickname || '-' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="likes" label="点赞" width="80" />
        <el-table-column prop="createTime" label="发布时间" width="160" />
        <el-table-column label="状态" width="100">
          <template #default>
            <span class="px-3 py-1 rounded-full text-xs font-bold badge-success">已发布</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <div class="flex items-center gap-1">
              <button @click="viewDetail(row)" class="p-2 rounded-lg hover:bg-emerald-50 text-slate-400 hover:text-primary-container transition-all">
                <span class="material-symbols-outlined text-lg">visibility</span>
              </button>
              <button @click="handleDelete(row)" class="p-2 rounded-lg hover:bg-red-50 text-slate-400 hover:text-error transition-all">
                <span class="material-symbols-outlined text-lg">delete</span>
              </button>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end p-6">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next" @current-change="handleCurrentChange" @size-change="handleSizeChange" />
      </div>
    </div>

    <!-- FAB -->
    <button class="fab animate-scale-in" style="animation-delay: 0.5s">
      <span class="material-symbols-outlined text-[28px]">post_add</span>
    </button>
  </div>
</template>
