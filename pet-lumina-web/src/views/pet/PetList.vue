<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { petApi } from '@/api/pet'
import { usePagination } from '@/composables/usePagination'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Pet } from '@/types'

const router = useRouter()
const loading = ref(false)
const tableData = ref<Pet[]>([])
const searchText = ref('')
const typeFilter = ref('')
const healthFilter = ref('')
const { currentPage, pageSize, total, handleCurrentChange, handleSizeChange } = usePagination(fetchData)

async function fetchData() {
  loading.value = true
  try {
    const params: any = { current: currentPage.value, pageSize: pageSize.value }
    if (searchText.value) params.name = searchText.value
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
const handleReset = () => { searchText.value = ''; typeFilter.value = ''; healthFilter.value = ''; currentPage.value = 1; fetchData() }

const handleDelete = async (pet: Pet) => {
  try {
    await ElMessageBox.confirm(`确定要删除宠物「${pet.name}」吗？`, '确认删除', { type: 'warning' })
    await petApi.delete(pet.id)
    ElMessage.success('删除成功')
    fetchData()
  } catch {}
}

const viewDetail = (pet: Pet) => {
  router.push(`/pet/${pet.id}`)
}

const healthStatusClass = (score: number) => {
  if (score >= 80) return { bg: 'bg-emerald-500', text: '健康良好', class: 'badge-success' }
  if (score >= 50) return { bg: 'bg-amber-500', text: '观察中', class: 'badge-warning' }
  return { bg: 'bg-red-500', text: '治疗中', class: 'badge-error' }
}

const petImages = [
  'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1558618666-fcd25c85f82e?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1583511655857-d19b40a7a54e?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=400&h=300&fit=crop',
]

const getPetImage = (pet: Pet, index: number) => {
  return pet.avatar || petImages[index % petImages.length]
}
</script>

<template>
  <div v-loading="loading">
    <!-- Header -->
    <div class="flex justify-between items-end mb-8 animate-float-up">
      <div>
        <h2 class="font-[Plus_Jakarta_Sans] text-[32px] font-bold text-primary mb-2">宠物管理</h2>
        <p class="text-on-surface-variant">管理和监控所有登记在册的宠物理档案</p>
      </div>
      <button
        @click="router.push('/pet/add')"
        class="flex items-center gap-2 bg-primary-container text-on-primary-container px-6 py-3 rounded-xl font-bold shadow-lg btn-jelly text-sm"
      >
        <span class="material-symbols-outlined text-lg">add</span>
        添加宠物
      </button>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <div class="glass-panel rounded-2xl p-6 flex items-center justify-between depth-1 animate-float-up" style="animation-delay: 0.1s">
        <div>
          <p class="text-slate-500 text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-1">宠物总数</p>
          <h3 class="font-[Plus_Jakarta_Sans] text-[40px] font-bold text-primary">{{ total.toLocaleString() }}</h3>
        </div>
        <div class="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center text-emerald-600">
          <span class="material-symbols-outlined text-3xl">pets</span>
        </div>
      </div>
      <div class="glass-panel rounded-2xl p-6 flex items-center justify-between depth-1 animate-float-up" style="animation-delay: 0.15s">
        <div>
          <p class="text-slate-500 text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-1">本月新增</p>
          <div class="flex items-baseline gap-2">
            <h3 class="font-[Plus_Jakarta_Sans] text-[40px] font-bold text-primary">+84</h3>
            <span class="text-xs text-emerald-600 font-bold flex items-center gap-1">
              <span class="material-symbols-outlined text-base">trending_up</span> 12%
            </span>
          </div>
        </div>
        <div class="w-14 h-14 bg-emerald-100 rounded-2xl flex items-center justify-center text-emerald-600">
          <span class="material-symbols-outlined text-3xl">trending_up</span>
        </div>
      </div>
    </div>

    <!-- Filter Bar -->
    <div class="glass-panel rounded-2xl p-4 flex flex-wrap items-center gap-4 mb-8 animate-float-up" style="animation-delay: 0.2s">
      <div class="relative flex-1 min-w-[200px]">
        <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">search</span>
        <input
          v-model="searchText"
          type="text"
          placeholder="搜索宠物名、主人姓名..."
          class="w-full bg-white/50 border border-white/40 rounded-lg pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 outline-none transition-all"
          @keyup.enter="handleSearch"
        />
      </div>
      <el-select v-model="typeFilter" placeholder="所有品种" clearable style="width: 140px">
        <el-option label="狗" value="狗" />
        <el-option label="猫" value="猫" />
        <el-option label="其他" value="其他" />
      </el-select>
      <el-select v-model="healthFilter" placeholder="健康状态" clearable style="width: 130px">
        <el-option label="良好" value="good" />
        <el-option label="治疗中" value="treating" />
        <el-option label="观察中" value="observing" />
      </el-select>
      <button class="p-2.5 text-slate-400 hover:text-emerald-600 transition-colors" @click="handleSearch">
        <span class="material-symbols-outlined">filter_list</span>
      </button>
    </div>

    <!-- Pet Card Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
      <div
        v-for="(pet, index) in tableData"
        :key="pet.id"
        class="glass-panel rounded-2xl overflow-hidden group cursor-pointer depth-1 hover:depth-3 transition-all duration-400 animate-float-up"
        :style="{ animationDelay: `${0.25 + index * 0.06}s` }"
        @click="viewDetail(pet)"
      >
        <!-- Image -->
        <div class="relative h-48 overflow-hidden">
          <img
            :src="getPetImage(pet, index)"
            :alt="pet.name"
            class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          />
          <div class="absolute top-4 right-4 px-3 py-1 rounded-full text-xs font-bold text-white shadow-lg"
            :class="healthStatusClass(pet.healthScore || 100).bg">
            {{ healthStatusClass(pet.healthScore || 100).text }}
          </div>
        </div>
        <!-- Info -->
        <div class="p-6">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h4 class="font-[Plus_Jakarta_Sans] text-xl font-bold text-primary mb-1">{{ pet.name }}</h4>
              <p class="text-slate-500 text-sm">{{ pet.breed || pet.type }} · {{ pet.age || '-' }} 岁</p>
            </div>
            <button class="text-slate-400 hover:text-emerald-500 transition-colors" @click.stop>
              <span class="material-symbols-outlined">more_vert</span>
            </button>
          </div>
          <div class="flex items-center gap-3 pt-4 border-t border-white/20">
            <div class="w-8 h-8 rounded-full bg-primary-container/20 flex items-center justify-center">
              <span class="material-symbols-outlined text-primary-container text-sm">person</span>
            </div>
            <div>
              <p class="text-xs text-slate-400">所属主人</p>
              <p class="text-sm font-semibold text-slate-700">{{ pet.user?.nickname || '-' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Add New Placeholder Card -->
      <div
        class="border-2 border-dashed border-emerald-500/30 rounded-2xl flex flex-col items-center justify-center p-6 text-emerald-500 hover:bg-emerald-500/5 transition-all duration-300 cursor-pointer min-h-[350px] animate-float-up"
        :style="{ animationDelay: `${0.25 + tableData.length * 0.06}s` }"
        @click="router.push('/pet/add')"
      >
        <div class="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mb-4">
          <span class="material-symbols-outlined text-3xl">add</span>
        </div>
        <p class="font-semibold text-lg">点击添加新宠物</p>
        <p class="text-sm opacity-60">完善档案以获取更多服务</p>
      </div>
    </div>

    <!-- Pagination -->
    <div class="flex justify-center animate-float-up" style="animation-delay: 0.5s">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[6, 12, 24]"
        layout="total, sizes, prev, pager, next"
        @current-change="handleCurrentChange"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>