<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ShareModal from '@/components/common/ShareModal.vue'
import type { LogEntry } from '@/types'
import { logApi } from '@/api/log'

const route = useRoute()
const router = useRouter()

const logId = computed(() => Number(route.params.id))

const log = ref<LogEntry | null>(null)

onMounted(async () => {
  try {
    log.value = await logApi.getById(logId.value) as any
  } catch (e) {
    console.error('Failed to fetch log:', e)
    log.value = null
  }
})

const isLiked = ref(false)
const showShareModal = ref(false)

const toggleLike = () => {
  isLiked.value = !isLiked.value
}

const goBack = () => {
  router.back()
}

const openShare = () => {
  showShareModal.value = true
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, string> = {
    feeding: 'restaurant',
    walking: 'directions_walk',
    grooming: 'content_cut',
    medical: 'medical_services',
    other: 'event_note'
  }
  return icons[type] || 'event_note'
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    feeding: 'bg-primary-container text-primary',
    walking: 'bg-secondary-container text-secondary',
    grooming: 'bg-tertiary-container text-tertiary',
    medical: 'bg-error-container text-error',
    other: 'bg-surface-container-high text-on-surface'
  }
  return colors[type] || 'bg-surface-container-high text-on-surface'
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main v-if="log" class="pt-4">
      <div class="p-container-padding space-y-lg max-w-screen-xl mx-auto">
        <div class="flex items-center justify-between py-md mb-md">
          <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
            <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
          </button>
          <span class="font-title-sm text-on-surface">记录详情</span>
          <button @click="openShare" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
            <span class="material-symbols-outlined text-emerald-700">more_vert</span>
          </button>
        </div>
        <div class="flex items-center gap-sm">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center" :class="getTypeColor(log.type)">
            <span class="material-symbols-outlined text-2xl">{{ getTypeIcon(log.type) }}</span>
          </div>
          <div>
            <h2 class="font-headline-sm text-headline-sm text-on-surface">{{ log.title }}</h2>
            <p class="text-xs text-on-surface-variant">{{ log.createTime }}</p>
          </div>
        </div>

        <div v-if="log.imageList && log.imageList.length > 0" class="rounded-xl overflow-hidden">
          <img class="w-full h-auto object-cover" :src="log.imageList[0]" />
        </div>

        <p class="font-body-md text-body-md text-on-surface leading-relaxed">{{ log.content }}</p>

        <div class="flex gap-sm flex-wrap">
          <span v-for="tag in log.tagList" :key="tag" class="px-3 py-1 bg-primary-container text-primary rounded-full text-xs font-label-bold">
            #{{ tag }}
          </span>
        </div>

        <div class="flex items-center justify-between py-md border-t border-b border-surface-variant/30">
          <button @click="toggleLike" class="flex items-center gap-2 px-4 py-2 rounded-full transition-colors" :class="isLiked ? 'text-red-500' : 'text-on-surface-variant hover:bg-surface-container'">
            <span class="material-symbols-outlined">{{ isLiked ? 'favorite' : 'favorite_border' }}</span>
            <span class="font-label-bold">{{ isLiked ? 1 : 0 }}</span>
          </button>
          <button @click="openShare" class="flex items-center gap-2 px-4 py-2 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors">
            <span class="material-symbols-outlined">share</span>
            <span class="font-label-bold">分享</span>
          </button>
        </div>
      </div>
    </main>

    <div v-else class="pt-20 px-container-padding flex flex-col items-center justify-center min-h-[60vh]">
      <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">error_outline</span>
      <p class="mt-4 font-title-md text-on-surface-variant">记录不存在</p>
      <button @click="goBack" class="mt-4 px-6 py-2 bg-primary text-on-primary rounded-full font-label-bold">返回</button>
    </div>

    <Teleport to="body">
      <ShareModal 
        v-model:visible="showShareModal" 
        :post="log ? { title: log.title, image: (log.imageList && log.imageList[0]) || '', author: '我的宠物记录' } : null" 
      />
    </Teleport>
  </div>
</template>
