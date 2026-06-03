<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { petApi } from '@/api/pet'
import { userApi } from '@/api/user'
import { healthApi } from '@/api/health'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Pet } from '@/types'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const petData = ref<Pet | null>(null)
const ownerInfo = ref<any>(null)
const healthRecords = ref<any[]>([])

const petId = computed(() => route.params.id as string)

onMounted(async () => {
  loading.value = true
  try {
    const res = await petApi.getDetail(petId.value) as any
    petData.value = res
    if (res?.userId) {
      try { ownerInfo.value = await userApi.getDetail(res.userId) as any } catch {}
    }
    try {
      const hRes = await healthApi.listRecords({ petId: petId.value, pageSize: 5 }) as any
      healthRecords.value = hRes?.records || []
    } catch {}
  } catch (e) { console.error(e) } finally { loading.value = false }
})

const goBack = () => router.push('/pet')
const handleEdit = () => router.push(`/pet/edit/${petId.value}`)
const viewAllHealth = () => router.push({ path: '/health', query: { petId: petId.value } })

const handleDelete = async () => {
  if (!petData.value) return
  try {
    await ElMessageBox.confirm(`确定要删除宠物「${petData.value.name}」吗？`, '确认删除', { type: 'error' })
    await petApi.delete(petData.value.id)
    ElMessage.success('删除成功')
    router.push('/pet')
  } catch {}
}

const healthStatusClass = (score: number) => {
  if (score >= 80) return { bg: 'bg-emerald-500', text: '健康良好' }
  if (score >= 50) return { bg: 'bg-amber-500', text: '观察中' }
  return { bg: 'bg-red-500', text: '需关注' }
}
</script>

<template>
  <div v-loading="loading" class="space-y-8">
    <!-- Header -->
    <div class="flex items-center justify-between animate-float-up">
      <div class="flex items-center gap-4">
        <button class="glass-panel rounded-full w-10 h-10 flex items-center justify-center btn-jelly" @click="goBack">
          <span class="material-symbols-outlined text-on-surface-variant">arrow_back</span>
        </button>
        <h1 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">宠物详情</h1>
      </div>
      <div class="flex items-center gap-3">
        <button @click="handleEdit" class="flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary text-white btn-jelly shadow-lg shadow-primary/20 text-sm font-bold">
          <span class="material-symbols-outlined text-lg">edit</span>编辑信息
        </button>
        <button @click="handleDelete" class="w-11 h-11 flex items-center justify-center rounded-full bg-error-container text-error btn-jelly">
          <span class="material-symbols-outlined">delete</span>
        </button>
      </div>
    </div>

    <template v-if="petData">
      <div class="grid grid-cols-12 gap-6">
        <!-- Left Column -->
        <div class="col-span-12 lg:col-span-8 space-y-6">
          <!-- Hero -->
          <div class="glass-panel-deep rounded-[32px] overflow-hidden depth-3 animate-float-up stagger-1 relative group">
            <div class="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent z-10" />
            <div class="h-[400px] relative overflow-hidden">
              <img v-if="petData.avatar" :src="petData.avatar" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700" />
              <div v-else class="w-full h-full bg-gradient-to-br from-primary-container/30 via-primary/10 to-secondary-container/20 flex items-center justify-center">
                <span class="material-symbols-outlined text-white/20" style="font-size: 200px">pets</span>
              </div>
              <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
              <div class="absolute bottom-8 left-10 z-20 text-white">
                <div class="flex items-center gap-4 mb-2">
                  <h1 class="font-[Plus_Jakarta_Sans] text-[40px] font-bold drop-shadow-lg">{{ petData.name }}</h1>
                  <span class="px-4 py-1 rounded-full text-xs font-bold uppercase tracking-widest shadow-lg"
                    :class="healthStatusClass(petData.healthScore || 100).bg">
                    {{ healthStatusClass(petData.healthScore || 100).text }}
                  </span>
                </div>
                <p class="text-white/90 text-lg">{{ petData.breed }} · {{ petData.age || '-' }} · {{ petData.type === 'dog' ? '狗狗' : petData.type === 'cat' ? '猫咪' : '其他' }}</p>
              </div>
            </div>
          </div>

          <!-- Bento Info Cards -->
          <div class="grid grid-cols-3 gap-4">
            <div class="glass-panel p-5 rounded-[24px] flex flex-col items-center text-center depth-1 animate-float-up stagger-2">
              <span class="material-symbols-outlined text-primary text-3xl mb-3 glow-icon">monitor_weight</span>
              <span class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold mb-1">今日步数</span>
              <span class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">{{ petData.todaySteps ?? 0 }}</span>
            </div>
            <div class="glass-panel p-5 rounded-[24px] flex flex-col items-center text-center depth-1 animate-float-up stagger-3">
              <span class="material-symbols-outlined text-primary text-3xl mb-3 glow-icon">restaurant</span>
              <span class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold mb-1">喂食进度</span>
              <span class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">{{ petData.feedingCount ?? 0 }}/{{ petData.feedingTotal ?? 0 }}</span>
            </div>
            <div class="glass-panel p-5 rounded-[24px] flex flex-col items-center text-center depth-1 animate-float-up stagger-4">
              <span class="material-symbols-outlined text-primary text-3xl mb-3 glow-icon">monitor_heart</span>
              <span class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold mb-1">健康评分</span>
              <span class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-primary">{{ petData.healthScore ?? '-' }}</span>
            </div>
          </div>

          <!-- Basic Info -->
          <div class="glass-panel rounded-[32px] p-8 depth-2 animate-float-up stagger-5">
            <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-lg mb-6 flex items-center gap-2">
              <span class="material-symbols-outlined text-primary">info</span>基本信息
            </h3>
            <div class="grid grid-cols-2 gap-4">
              <div class="p-4 rounded-2xl bg-white/20">
                <p class="text-xs text-slate-400 mb-1">类型</p>
                <p class="font-bold text-on-surface">{{ petData.type === 'dog' ? '狗狗' : petData.type === 'cat' ? '猫咪' : '其他' }}</p>
              </div>
              <div class="p-4 rounded-2xl bg-white/20">
                <p class="text-xs text-slate-400 mb-1">品种</p>
                <p class="font-bold text-on-surface">{{ petData.breed || '-' }}</p>
              </div>
              <div class="p-4 rounded-2xl bg-white/20">
                <p class="text-xs text-slate-400 mb-1">年龄</p>
                <p class="font-bold text-on-surface">{{ petData.age || '-' }}</p>
              </div>
              <div class="p-4 rounded-2xl bg-white/20">
                <p class="text-xs text-slate-400 mb-1">备注</p>
                <p class="font-bold text-on-surface">{{ petData.notes || '无' }}</p>
              </div>
            </div>
          </div>

          <!-- Health Records -->
          <div class="glass-panel rounded-[32px] p-8 depth-2 animate-float-up stagger-6">
            <div class="flex justify-between items-center mb-6">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-primary glow-icon">history</span>
                <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-lg">健康记录</h3>
              </div>
              <button @click="viewAllHealth" class="text-primary text-sm font-semibold hover:underline">查看全部</button>
            </div>
            <div v-if="healthRecords.length > 0" class="space-y-3">
              <div v-for="record in healthRecords" :key="record.id"
                class="flex items-center justify-between p-4 rounded-2xl bg-white/20 hover:bg-white/30 transition-all group/item">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 rounded-xl bg-secondary-container flex items-center justify-center text-primary group-hover/item:scale-110 transition-transform">
                    <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">monitor_heart</span>
                  </div>
                  <div>
                    <p class="font-bold text-on-surface text-sm">{{ record.date || '-' }}</p>
                    <p class="text-xs text-slate-500">心率 {{ record.heartRate ?? '-' }} · 步数 {{ record.steps ?? '-' }}</p>
                  </div>
                </div>
                <span class="px-4 py-1.5 rounded-full bg-primary/10 text-primary text-xs font-bold">{{ record.mood || '正常' }}</span>
              </div>
            </div>
            <div v-else class="text-center py-8 text-slate-400">
              <span class="material-symbols-outlined text-4xl mb-2">medical_services</span>
              <p class="text-sm">暂无健康记录</p>
            </div>
          </div>
        </div>

        <!-- Right Column -->
        <div class="col-span-12 lg:col-span-4 space-y-6">
          <!-- Owner Info -->
          <div class="glass-panel rounded-[32px] p-8 depth-2 animate-float-up stagger-2">
            <h4 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-6">主人信息</h4>
            <div class="flex flex-col items-center text-center">
              <div class="w-24 h-24 rounded-full border-4 border-white/60 mb-4 shadow-xl bg-gradient-to-br from-primary-container to-primary flex items-center justify-center text-white text-3xl font-bold font-[Plus_Jakarta_Sans]">
                {{ (ownerInfo?.nickname || petData.user?.nickname || '?').charAt(0) }}
              </div>
              <p class="font-[Plus_Jakarta_Sans] font-bold text-lg text-on-surface">{{ ownerInfo?.nickname || petData.user?.nickname || '-' }}</p>
              <p class="text-slate-500 mb-6">{{ ownerInfo?.phone || '-' }}</p>
              <div class="w-full space-y-3">
                <div class="flex items-center justify-between px-4 py-3 rounded-xl bg-white/20">
                  <span class="material-symbols-outlined text-primary text-sm">call</span>
                  <span class="text-sm font-medium">{{ ownerInfo?.phone || '-' }}</span>
                </div>
                <div class="flex items-center justify-between px-4 py-3 rounded-xl bg-white/20">
                  <span class="material-symbols-outlined text-primary text-sm">mail</span>
                  <span class="text-sm font-medium">{{ ownerInfo?.email || '-' }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="glass-panel rounded-[32px] p-8 depth-2 animate-float-up stagger-3">
            <h4 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-6">快捷操作</h4>
            <div class="space-y-3">
              <button @click="viewAllHealth" class="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/20 hover:bg-white/40 transition-all text-sm text-on-surface">
                <span class="material-symbols-outlined text-primary">monitor_heart</span>
                查看健康记录
              </button>
              <button @click="handleEdit" class="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-white/20 hover:bg-white/40 transition-all text-sm text-on-surface">
                <span class="material-symbols-outlined text-primary">edit</span>
                编辑宠物信息
              </button>
            </div>
          </div>

          <!-- Admin Notes -->
          <div class="glass-panel rounded-[32px] p-8 depth-2 animate-float-up stagger-4">
            <div class="flex items-center gap-2 mb-4">
              <span class="material-symbols-outlined text-primary text-sm">edit_note</span>
              <h4 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">管理员备注</h4>
            </div>
            <p class="text-sm text-on-surface-variant leading-relaxed italic">{{ petData.notes || '暂无备注' }}</p>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="flex flex-col items-center justify-center py-20">
      <span class="material-symbols-outlined text-6xl text-slate-300">pets</span>
      <p class="mt-4 text-on-surface-variant">未找到该宠物信息</p>
      <button @click="goBack" class="mt-4 px-6 py-2 bg-primary text-white rounded-full btn-jelly">返回列表</button>
    </div>
  </div>
</template>
