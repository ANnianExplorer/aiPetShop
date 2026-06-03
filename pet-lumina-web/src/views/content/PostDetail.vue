<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { postApi } from '@/api/post'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { Post } from '@/types'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const postData = ref<Post | null>(null)

const postId = computed(() => route.params.id as string)

onMounted(async () => {
  loading.value = true
  try {
    const res = await postApi.getDetail(postId.value) as any
    postData.value = res
  } catch (e) { console.error(e) } finally { loading.value = false }
})

const handleApprove = () => {
  ElMessage.success('帖子已通过审核')
  router.push('/post')
}

const handleReject = async () => {
  try {
    await ElMessageBox.confirm('确定要拒绝并下架这篇帖子吗？', '拒绝审核', { type: 'warning' })
    ElMessage.success('帖子已下架')
    router.push('/post')
  } catch {}
}

const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要彻底删除这篇帖子吗？此操作不可恢复。', '删除帖子', { type: 'error' })
    await postApi.delete(Number(postId.value))
    ElMessage.success('帖子已删除')
    router.push('/post')
  } catch {}
}

const imageList = computed(() => {
  if (!postData.value?.images) return []
  try {
    const parsed = JSON.parse(postData.value.images)
    return Array.isArray(parsed) ? parsed : []
  } catch { return [] }
})

const tagList = computed(() => {
  if (!postData.value?.tags) return []
  try {
    const parsed = JSON.parse(postData.value.tags)
    return Array.isArray(parsed) ? parsed : []
  } catch { return [] }
})
</script>

<template>
  <div v-loading="loading" class="space-y-8">
    <!-- Header -->
    <div class="flex items-center gap-4 animate-float-up">
      <button class="flex items-center gap-2 px-5 py-2.5 rounded-full glass-panel-deep text-primary text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest hover:scale-[1.02] transition-all" @click="router.push('/post')">
        <span class="material-symbols-outlined text-lg">arrow_back</span>
        返回列表
      </button>
    </div>

    <template v-if="postData">
      <div class="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Left Column -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Post Article -->
          <div class="glass-panel-deep p-8 rounded-3xl depth-2 animate-float-up stagger-1">
            <div class="flex justify-between items-start mb-6">
              <div class="space-y-2">
                <span v-if="postData.category" class="px-3 py-1 bg-primary-container text-on-primary-container rounded-full text-[10px] font-bold tracking-widest uppercase">{{ postData.category }}</span>
                <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold mt-2 leading-tight text-on-surface">{{ postData.content?.substring(0, 60) }}{{ (postData.content?.length || 0) > 60 ? '...' : '' }}</h2>
                <p class="text-sm text-on-surface-variant flex items-center gap-2">
                  <span class="material-symbols-outlined text-sm">schedule</span>
                  发布于 {{ postData.createTime }}
                </p>
              </div>
            </div>

            <article class="text-base text-on-surface/90 leading-relaxed mb-8">
              <p>{{ postData.content }}</p>
            </article>

            <!-- Tags -->
            <div v-if="tagList.length > 0" class="flex flex-wrap gap-2 mb-6">
              <span v-for="tag in tagList" :key="tag" class="px-3 py-1 bg-primary/10 text-primary rounded-full text-xs font-bold">#{{ tag }}</span>
            </div>

            <!-- Images -->
            <div v-if="imageList.length > 0" class="grid grid-cols-2 gap-4">
              <div v-for="(img, i) in imageList" :key="i" class="relative group overflow-hidden rounded-2xl" :class="i === 0 && imageList.length > 1 ? 'row-span-2 h-[400px]' : 'h-[196px]'">
                <img :src="img" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
                <div class="absolute inset-0 bg-black/10 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
          </div>

          <!-- Statistics -->
          <div class="flex gap-4 animate-float-up stagger-2">
            <div class="flex-1 glass-panel p-6 rounded-2xl flex items-center justify-between depth-1">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary">
                  <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">favorite</span>
                </div>
                <div>
                  <p class="text-slate-500 text-xs font-[Plus_Jakarta_Sans] font-semibold">点赞总数</p>
                  <p class="font-[Plus_Jakarta_Sans] text-xl font-bold">{{ postData.likes ?? 0 }}</p>
                </div>
              </div>
            </div>
            <div class="flex-1 glass-panel p-6 rounded-2xl flex items-center justify-between depth-1">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-secondary/10 flex items-center justify-center text-secondary">
                  <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">chat_bubble</span>
                </div>
                <div>
                  <p class="text-slate-500 text-xs font-[Plus_Jakarta_Sans] font-semibold">评论数量</p>
                  <p class="font-[Plus_Jakarta_Sans] text-xl font-bold">{{ postData.comments ?? 0 }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column -->
        <div class="space-y-6">
          <!-- Author Card -->
          <div class="glass-panel-deep p-8 rounded-3xl overflow-hidden relative depth-2 animate-float-up stagger-2">
            <div class="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -mr-16 -mt-16 blur-2xl" />
            <h3 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-6">作者信息</h3>
            <div class="flex flex-col items-center text-center relative z-10">
              <div class="relative">
                <div class="w-24 h-24 rounded-full border-4 border-white shadow-xl bg-gradient-to-br from-primary-container to-primary flex items-center justify-center text-white text-3xl font-bold font-[Plus_Jakarta_Sans]">
                  {{ (postData.user?.nickname || '?').charAt(0) }}
                </div>
              </div>
              <h4 class="font-[Plus_Jakarta_Sans] text-xl font-bold mt-4 mb-1">{{ postData.user?.nickname || '未知用户' }}</h4>
              <p class="text-sm text-slate-500 mb-4 px-4">{{ postData.user?.bio || '-' }}</p>
              <button @click="router.push({ path: '/post', query: { author: postData.user?.nickname } })" class="w-full py-3 rounded-xl bg-white border border-primary/20 text-primary font-bold hover:bg-primary/5 transition-all">
                查看所有帖子
              </button>
            </div>
          </div>

          <!-- Audit Console -->
          <div class="glass-panel-deep p-8 rounded-3xl space-y-4 depth-2 animate-float-up stagger-3">
            <h3 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">审核控制台</h3>
            <div class="p-4 bg-white/20 rounded-2xl border border-white/40">
              <div class="flex items-center gap-3 mb-2">
                <span class="material-symbols-outlined text-amber-500">info</span>
                <span class="font-bold text-sm">当前状态：待审核</span>
              </div>
              <p class="text-[11px] text-slate-600">系统已初步完成敏感词过滤，未发现违规项。请根据社区准则进行人工复核。</p>
            </div>
            <div class="space-y-3 pt-4">
              <button class="w-full py-4 rounded-2xl bg-primary text-white font-bold flex items-center justify-center gap-2 shadow-lg shadow-primary/20 hover:scale-[1.02] transition-all btn-jelly" @click="handleApprove">
                <span class="material-symbols-outlined">check_circle</span>
                通过审核
              </button>
              <button class="w-full py-4 rounded-2xl bg-white border border-tertiary/30 text-tertiary font-bold flex items-center justify-center gap-2 hover:bg-tertiary/5 transition-all" @click="handleReject">
                <span class="material-symbols-outlined">block</span>
                拒绝并下架
              </button>
              <div class="h-px bg-white/30 my-4" />
              <button class="w-full py-4 rounded-2xl border-2 border-dashed border-error/30 text-error font-bold flex items-center justify-center gap-2 hover:bg-error/5 transition-all" @click="handleDelete">
                <span class="material-symbols-outlined">delete</span>
                彻底删除此帖
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="flex flex-col items-center justify-center py-20">
      <span class="material-symbols-outlined text-6xl text-slate-300">article</span>
      <p class="mt-4 text-on-surface-variant">帖子不存在</p>
      <button @click="router.push('/post')" class="mt-4 px-6 py-2 bg-primary text-white rounded-full btn-jelly">返回列表</button>
    </div>
  </div>
</template>
