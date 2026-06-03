<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { userApi } from '@/api/user'
import { usePagination } from '@/composables/usePagination'
import UserDetail from './UserDetail.vue'
import type { User } from '@/types'

const router = useRouter()

const loading = ref(false)
const tableData = ref<User[]>([])
const searchText = ref('')
const roleFilter = ref('')
const statusFilter = ref<number | ''>('')
const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

const showDrawer = ref(false)
const selectedUserId = ref<number>(0)

async function fetchData() {
  loading.value = true
  try {
    const params: any = {
      current: currentPage.value,
      pageSize: pageSize.value,
    }
    if (searchText.value) params.nickname = searchText.value
    if (roleFilter.value) params.role = roleFilter.value
    if (statusFilter.value !== '') params.status = statusFilter.value
    const res = await userApi.listPage(params) as any
    tableData.value = res?.records || []
    total.value = res?.total || 0
  } catch (e) {
    console.error('Failed to fetch users:', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)

const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

const handleReset = () => {
  searchText.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  fetchData()
}

const viewDetail = (user: User) => {
  selectedUserId.value = user.id
  showDrawer.value = true
}

const handleStatusChange = async (user: User) => {
  try {
    await userApi.updateStatus({ id: user.id, status: user.status === 1 ? 0 : 1 })
    fetchData()
  } catch (e) {
    console.error('Failed to update status:', e)
  }
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
          placeholder="姓名/邮箱/手机号"
          class="w-full bg-white/15 backdrop-blur-[10px] border border-white/30 rounded-full pl-11 pr-4 py-3 text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container/50 outline-none transition-all text-sm"
          @keyup.enter="handleSearch"
        />
      </div>
      <el-select v-model="roleFilter" placeholder="角色" clearable style="width: 120px">
        <el-option label="用户" value="user" />
        <el-option label="管理员" value="admin" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 120px">
        <el-option label="正常" :value="1" />
        <el-option label="禁用" :value="0" />
      </el-select>
      <button class="bg-primary-container text-white rounded-2xl px-6 py-3 font-bold shadow-[0_10px_25px_-5px_rgba(109,175,146,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-200 text-sm" @click="handleSearch">
        搜索
      </button>
      <button class="glass-panel rounded-2xl px-6 py-3 text-on-surface-variant hover:bg-white/20 transition-all text-sm" @click="handleReset">
        重置
      </button>
    </div>

    <!-- Action Bar -->
    <div class="flex justify-between items-center">
      <h3 class="font-[Plus_Jakarta_Sans] text-lg font-bold text-on-surface">用户列表</h3>
      <button
        class="btn-jelly flex items-center gap-2 px-5 py-2.5 bg-primary-container text-white rounded-2xl font-bold text-sm shadow-[0_8px_20px_-4px_rgba(109,175,146,0.4)]"
        @click="router.push('/user/add')"
      >
        <span class="material-symbols-outlined text-lg">person_add</span>
        新增用户
      </button>
    </div>

    <!-- Table -->
    <div class="glass-panel rounded-3xl p-6">
      <el-table :data="tableData" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="100" />
        <el-table-column prop="nickname" label="姓名" width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="role" label="角色" width="80">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
              {{ row.role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'" size="small">
              {{ row.status === 1 ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewDetail(row)">详情</el-button>
            <el-button :type="row.status === 1 ? 'danger' : 'success'" link size="small" @click="handleStatusChange(row)">
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="flex justify-end mt-6">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handleCurrentChange"
          @size-change="handleSizeChange"
        />
      </div>
    </div>

    <UserDetail v-model:visible="showDrawer" :user-id="selectedUserId" />
  </div>
</template>
