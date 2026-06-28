<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { logApi } from '@/api/log'
import { formatDate } from '@/utils/format'
import type { LogEntry } from '@/types'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const record = ref<LogEntry | null>(null)

const typeConfig: Record<string, { label: string; icon: string; bg: string; color: string }> = {
  feeding: { label: '饮食记录', icon: 'restaurant', bg: 'bg-orange-50', color: 'text-orange-600' },
  walking: { label: '运动记录', icon: 'directions_run', bg: 'bg-blue-50', color: 'text-blue-600' },
  grooming: { label: '美容记录', icon: 'content_cut', bg: 'bg-pink-50', color: 'text-pink-600' },
  medical: { label: '医疗记录', icon: 'medical_services', bg: 'bg-red-50', color: 'text-red-600' },
  daily: { label: '日常记录', icon: 'event_note', bg: 'bg-green-50', color: 'text-green-600' },
  other: { label: '其他', icon: 'note', bg: 'bg-gray-50', color: 'text-gray-600' },
}

const getType = (type: string) => typeConfig[type] || typeConfig.other

onMounted(async () => {
  loading.value = true
  try {
    const id = route.params.id as string
    record.value = await logApi.getById(id) as any
  } catch (e) {
    console.error(e)
    ElMessage.error('加载记录详情失败')
  } finally {
    loading.value = false
  }
})

const handleDelete = async () => {
  if (!record.value) return
  try {
    await ElMessageBox.confirm('确定要删除这条记录吗？', '确认删除', { type: 'warning' })
    await logApi.delete(record.value.id)
    ElMessage.success('删除成功')
    router.push('/log')
  } catch {}
}
</script>

<template>
  <div v-loading="loading" class="space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-6 animate-float-up">
      <button
        class="flex items-center justify-center w-10 h-10 rounded-full glass-panel text-primary transition-all duration-300 active:scale-95"
        @click="router.push('/log')"
      >
        <span class="material-symbols-outlined">arrow_back</span>
      </button>
      <div>
        <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">记录详情</h2>
        <p class="text-xs text-slate-500 font-[Plus_Jakarta_Sans]">Record ID: #{{ record?.id }}</p>
      </div>
    </div>

    <!-- Breadcrumbs -->
    <div class="flex items-center gap-2 text-sm text-slate-500 animate-float-up" style="animation-delay: 0.05s">
      <span>宠物动态</span>
      <span class="material-symbols-outlined text-xs">chevron_right</span>
      <span>生活记录</span>
      <span class="material-symbols-outlined text-xs">chevron_right</span>
      <span class="text-primary font-bold">{{ record?.title }}</span>
    </div>

    <!-- Content -->
    <div v-if="record" class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Left: Article -->
      <div class="lg:col-span-8 space-y-6">
        <article class="glass-panel-deep rounded-[32px] p-8 depth-2 animate-float-up stagger-1">
          <!-- Title & Meta -->
          <div class="flex justify-between items-start mb-8">
            <div>
              <h1 class="font-[Plus_Jakarta_Sans] text-3xl font-bold text-on-surface mb-3">{{ record.title }}</h1>
              <div class="flex items-center gap-4">
                <div class="flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full border border-primary/20">
                  <span class="material-symbols-outlined text-sm">schedule</span>
                  <span class="text-xs font-bold">{{ formatDate(record.createTime) }}</span>
                </div>
                <span class="px-3 py-1 rounded-full text-xs font-bold" :class="[getType(record.type).bg, getType(record.type).color]">
                  <span class="material-symbols-outlined text-[14px] align-middle mr-1">{{ getType(record.type).icon }}</span>
                  {{ getType(record.type).label }}
                </span>
              </div>
            </div>
            <div class="flex gap-2">
              <button class="p-2 rounded-xl glass-panel text-slate-500 hover:text-error transition-colors" @click="handleDelete">
                <span class="material-symbols-outlined">delete</span>
              </button>
            </div>
          </div>

          <!-- Images -->
          <div v-if="record.imageList && record.imageList.length > 0" class="mb-8">
            <div class="grid grid-cols-2 gap-4">
              <div v-for="(img, i) in record.imageList" :key="i" class="rounded-2xl overflow-hidden aspect-[4/3]">
                <img :src="img" class="w-full h-full object-cover transition-transform duration-700 hover:scale-105" />
              </div>
            </div>
          </div>

          <!-- Content -->
          <div class="mb-10">
            <p class="text-base text-on-surface/80 leading-relaxed whitespace-pre-wrap">{{ record.content }}</p>
          </div>

          <!-- Tags -->
          <div v-if="record.tagList && record.tagList.length > 0" class="border-t border-white/20 pt-8">
            <h3 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-4 flex items-center gap-2">
              <span class="material-symbols-outlined text-lg">sell</span>
              分类标签
            </h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="tag in record.tagList" :key="tag" class="px-4 py-2 glass-panel rounded-xl text-primary font-bold text-sm"># {{ tag }}</span>
            </div>
          </div>
        </article>
      </div>

      <!-- Right: Sidebar -->
      <div class="lg:col-span-4 space-y-6">
        <!-- Author Info -->
        <div v-if="record.user" class="glass-panel-deep rounded-[32px] p-6 text-center depth-2 animate-float-up stagger-2">
          <div class="relative w-20 h-20 mx-auto mb-4">
            <img v-if="record.user.avatar" :src="record.user.avatar" class="w-full h-full rounded-full object-cover" />
            <div v-else class="w-full h-full rounded-full bg-gradient-to-br from-primary-container to-primary flex items-center justify-center text-white text-2xl font-bold">
              {{ record.user.nickname?.charAt(0) || '?' }}
            </div>
          </div>
          <h3 class="font-bold text-on-surface mb-1">{{ record.user.nickname }}</h3>
          <p class="text-xs text-slate-500">{{ record.user.phone }}</p>
        </div>

        <!-- Stats -->
        <div class="glass-panel-deep rounded-[32px] p-6 depth-2 animate-float-up stagger-3">
          <h3 class="text-xs text-slate-500 font-semibold uppercase tracking-widest mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-lg">analytics</span>
            记录统计
          </h3>
          <div class="space-y-4">
            <div class="flex items-center justify-between p-4 rounded-2xl bg-white/10">
              <span class="text-sm font-bold">点赞数</span>
              <span class="font-bold text-primary">{{ record.likes }}</span>
            </div>
            <div class="flex items-center justify-between p-4 rounded-2xl bg-white/10">
              <span class="text-sm font-bold">图片数</span>
              <span class="font-bold text-primary">{{ record.imageList?.length || 0 }}</span>
            </div>
            <div class="flex items-center justify-between p-4 rounded-2xl bg-white/10">
              <span class="text-sm font-bold">标签数</span>
              <span class="font-bold text-primary">{{ record.tagList?.length || 0 }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!loading && !record" class="flex flex-col items-center py-20">
      <span class="material-symbols-outlined text-6xl text-slate-300 mb-4">error_outline</span>
      <p class="text-slate-500 text-lg">记录不存在</p>
      <button class="mt-4 px-6 py-2 bg-primary text-white rounded-full" @click="router.push('/log')">返回列表</button>
    </div>
  </div>
</template>
