<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { LogEntry } from '@/types'

const route = useRoute()
const router = useRouter()

const logId = computed(() => route.params.id as string)

const mockLogs: Record<string, LogEntry> = {
  l1: {
    id: 'l1',
    petId: 'pet1',
    type: 'feeding',
    title: '今日喂食记录',
    description: '今天早上给小宝贝喂了200g幼犬粮，它吃得特别香。最近换了新的狗粮品牌，看起来适口性不错。中午又补充了一些湿粮，增加了水分摄入。',
    images: ['https://lh3.googleusercontent.com/aida-public/AB6AXuDrw2xQOCoPKtUH1OHjgSnmNFxCJnMRutQeJB4FzpZBVWDruxoWbpx-NfVJ1MSUFrd3sSi1rqMIrGXI0UPTfuyeWpg5j4Zf0D1URIsRXrEvPwZoWmHOqL2-IXbaJIP8KPu7dGtRYbb8512i_dK7sK28zVE2MaxkulF6GWyAXS9iM7lvKq8X8YzFtjdkFodZLMArgxBqVTjyriECa4S4RpzE-9mjcN3uQY68gNuJTAiTxVYdCFQv3XxKLzKQmCtRMPyd70tx3kOEZNX5'],
    createdAt: '2024-01-15 08:30',
    tags: ['喂食', '日常']
  },
  l2: {
    id: 'l2',
    petId: 'pet1',
    type: 'walking',
    title: '下午散步',
    description: '今天天气特别好，带着小伍去了公园散步。走了大概30分钟，它跑得特别开心，还和其他狗狗玩了一会儿。运动量达标！',
    images: ['https://lh3.googleusercontent.com/aida-public/AB6AXuBs-mer2w5mG_5FfxDENusNGC1qE4M9pLnE1DMn-I8VFbdU68rNVdewLa5uCedWh2Kmk7Y9XiN6_mzO_Bn2ryN-ZaXrAvmzUZC5AjL6nU2FWQR0if3nkG8JDPd-brQeg5Rp6HfoRO4c-HuNTGXVk5WxAHVIkWnPG3Y7yLv8hSYY8tqi4yRlAZdyKA09Iwsh3rBxMQQFA1qznWKGZ5cv7vbNtKW6Uv5yck06C0enOAoCc_FtQUPMGp8zwbvlhhOCaMa5eOTVJ7gS0qU9'],
    createdAt: '2024-01-15 15:00',
    tags: ['散步', '运动']
  },
  l3: {
    id: 'l3',
    petId: 'pet1',
    type: 'grooming',
    title: '洗澡美容',
    description: '今天给小宝贝洗了个澡，用了新的沐浴露，味道特别好闻。洗完之后毛发特别蓬松柔软，还修剪了指甲和耳朵周围的毛。',
    images: ['https://lh3.googleusercontent.com/aida-public/AB6AXuAPI7qGNIc36vLuccVKeqdqWOF1dpR1EvY7fgbyC-6_8fwQc5zuQJfGx8SLl_cQ7VndnqYjrmOSRC2_AUjsbzQzHrvxP6c26hNheHVGLKaCpoNUJmvVBzFmEiV2kB8HQVPYvip2bA04u0f6VkobU_HxVBTuKJeyB2n54Y6ACaV0hbDTjgXzwsxYdil0nCaAJx1kLjtkF5IJkRTGb627QFGi86L4Ftt25Dbd5zz-Jb1ecDPEZoOx3oqpZ0c-xqJ4vUXeKuflvMRtuC4m'],
    createdAt: '2024-01-14 10:00',
    tags: ['美容', '清洁']
  }
}

const log = computed(() => mockLogs[logId.value] || null)

const isLiked = ref(false)

const toggleLike = () => {
  isLiked.value = !isLiked.value
}

const goBack = () => {
  router.back()
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
          <button class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
            <span class="material-symbols-outlined text-emerald-700">more_vert</span>
          </button>
        </div>
        <div class="flex items-center gap-sm">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center" :class="getTypeColor(log.type)">
            <span class="material-symbols-outlined text-2xl">{{ getTypeIcon(log.type) }}</span>
          </div>
          <div>
            <h2 class="font-headline-sm text-headline-sm text-on-surface">{{ log.title }}</h2>
            <p class="text-xs text-on-surface-variant">{{ log.createdAt }}</p>
          </div>
        </div>

        <div v-if="log.images.length > 0" class="rounded-xl overflow-hidden">
          <img class="w-full h-auto object-cover" :src="log.images[0]" />
        </div>

        <p class="font-body-md text-body-md text-on-surface leading-relaxed">{{ log.description }}</p>

        <div class="flex gap-sm flex-wrap">
          <span v-for="tag in log.tags" :key="tag" class="px-3 py-1 bg-primary-container text-primary rounded-full text-xs font-label-bold">
            #{{ tag }}
          </span>
        </div>

        <div class="flex items-center justify-between py-md border-t border-b border-surface-variant/30">
          <button @click="toggleLike" class="flex items-center gap-2 px-4 py-2 rounded-full transition-colors" :class="isLiked ? 'text-red-500' : 'text-on-surface-variant hover:bg-surface-container'">
            <span class="material-symbols-outlined">{{ isLiked ? 'favorite' : 'favorite_border' }}</span>
            <span class="font-label-bold">{{ isLiked ? 1 : 0 }}</span>
          </button>
          <button class="flex items-center gap-2 px-4 py-2 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors">
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
  </div>
</template>
