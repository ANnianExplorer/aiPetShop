<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { topicApi } from '@/api/topic'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Topic } from '@/types'

const loading = ref(false)
const tableData = ref<Topic[]>([])
const searchText = ref('')
const categoryFilter = ref('')
const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

const showDialog = ref(false)
const isEdit = ref(false)
const form = reactive({ id: 0, title: '', description: '', image: '', category: '' })

async function fetchData() {
  loading.value = true
  try {
    const params: any = { current: currentPage.value, pageSize: pageSize.value }
    if (searchText.value) params.searchText = searchText.value
    if (categoryFilter.value) params.category = categoryFilter.value
    const res = await topicApi.listPage(params) as any
    tableData.value = res?.records || []
    total.value = res?.total || 0
  } catch (e) { console.error(e) } finally { loading.value = false }
}

onMounted(fetchData)
const handleSearch = () => { currentPage.value = 1; fetchData() }
const handleReset = () => { searchText.value = ''; categoryFilter.value = ''; currentPage.value = 1; fetchData() }

const handleAdd = () => {
  isEdit.value = false
  Object.assign(form, { id: 0, title: '', description: '', image: '', category: '' })
  showDialog.value = true
}

const handleEdit = (topic: Topic) => {
  isEdit.value = true
  Object.assign(form, { id: topic.id, title: topic.title, description: topic.description, image: topic.image, category: topic.category })
  showDialog.value = true
}

const handleSubmit = async () => {
  try {
    if (isEdit.value) {
      await topicApi.edit(form)
      ElMessage.success('编辑成功')
    } else {
      await topicApi.add(form)
      ElMessage.success('创建成功')
    }
    showDialog.value = false
    fetchData()
  } catch (e) { console.error(e) }
}

const handleDelete = async (topic: Topic) => {
  try {
    await ElMessageBox.confirm(`确定要删除话题「${topic.title}」吗？`, '确认删除', { type: 'warning' })
    await topicApi.delete(topic.id)
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
          placeholder="搜索话题"
          class="w-full bg-white/15 backdrop-blur-[10px] border border-white/30 rounded-full pl-11 pr-4 py-3 text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container/50 outline-none transition-all text-sm"
          @keyup.enter="handleSearch"
        />
      </div>
      <el-select v-model="categoryFilter" placeholder="类别" clearable style="width: 120px">
        <el-option label="综合" value="综合" />
        <el-option label="健康" value="健康" />
        <el-option label="日常" value="日常" />
      </el-select>
      <button class="bg-primary-container text-white rounded-2xl px-6 py-3 font-bold shadow-[0_10px_25px_-5px_rgba(109,175,146,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-200 text-sm" @click="handleSearch">
        搜索
      </button>
      <button class="glass-panel rounded-2xl px-6 py-3 text-on-surface-variant hover:bg-white/20 transition-all text-sm" @click="handleReset">
        重置
      </button>
      <button class="bg-emerald-500 text-white rounded-2xl px-6 py-3 font-bold shadow-[0_10px_25px_-5px_rgba(16,185,129,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-200 text-sm flex items-center gap-1" @click="handleAdd">
        <span class="material-symbols-outlined text-lg">add</span>
        新建话题
      </button>
    </div>

    <!-- Table -->
    <div class="glass-panel rounded-3xl p-6">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="图片" width="80">
          <template #default="{ row }">
            <el-image v-if="row.image" :src="row.image" style="width:50px;height:50px;border-radius:6px" fit="cover" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="话题" show-overflow-tooltip />
        <el-table-column prop="category" label="类别" width="100" />
        <el-table-column prop="postCount" label="帖子数" width="80" />
        <el-table-column prop="followerCount" label="关注数" width="80" />
        <el-table-column label="操作" width="140" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" link size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="flex justify-end mt-6">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :total="total" :page-sizes="[10,20,50]" layout="total, sizes, prev, pager, next, jumper" @current-change="handleCurrentChange" @size-change="handleSizeChange" />
      </div>
    </div>

    <!-- Add/Edit Dialog -->
    <el-dialog v-model="showDialog" :title="isEdit ? '编辑话题' : '新建话题'" width="500px" class="glass-dialog">
      <div class="space-y-5 py-2">
        <div>
          <label class="font-[Plus_Jakarta_Sans] text-xs font-semibold text-on-surface-variant mb-2 block uppercase tracking-wider">标题 <span class="text-error">*</span></label>
          <input
            v-model="form.title"
            type="text"
            placeholder="请输入话题标题"
            class="w-full px-4 py-3 rounded-xl bg-white/15 backdrop-blur-[10px] border border-white/30 text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container/50 outline-none transition-all text-sm"
          />
        </div>
        <div>
          <label class="font-[Plus_Jakarta_Sans] text-xs font-semibold text-on-surface-variant mb-2 block uppercase tracking-wider">描述</label>
          <textarea
            v-model="form.description"
            rows="3"
            placeholder="请输入话题描述"
            class="w-full px-4 py-3 rounded-xl bg-white/15 backdrop-blur-[10px] border border-white/30 text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container/50 outline-none transition-all text-sm resize-none"
          />
        </div>
        <div>
          <label class="font-[Plus_Jakarta_Sans] text-xs font-semibold text-on-surface-variant mb-2 block uppercase tracking-wider">图片</label>
          <input
            v-model="form.image"
            type="text"
            placeholder="图片URL"
            class="w-full px-4 py-3 rounded-xl bg-white/15 backdrop-blur-[10px] border border-white/30 text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container/50 outline-none transition-all text-sm"
          />
        </div>
        <div>
          <label class="font-[Plus_Jakarta_Sans] text-xs font-semibold text-on-surface-variant mb-2 block uppercase tracking-wider">类别</label>
          <el-select v-model="form.category" placeholder="选择类别" style="width: 100%">
            <el-option label="综合" value="综合" />
            <el-option label="健康" value="健康" />
            <el-option label="日常" value="日常" />
          </el-select>
        </div>
      </div>
      <template #footer>
        <div class="flex justify-end gap-3">
          <button class="glass-panel rounded-2xl px-6 py-3 text-on-surface-variant hover:bg-white/20 transition-all text-sm" @click="showDialog = false">取消</button>
          <button class="bg-primary-container text-white rounded-2xl px-6 py-3 font-bold shadow-[0_10px_25px_-5px_rgba(109,175,146,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-200 text-sm" @click="handleSubmit">确定</button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>
