<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import type { Topic } from '@/types'

const router = useRouter()

const topics = ref<Topic[]>([
  {
    id: 'tp1',
    title: '冬季宠物保暖指南',
    image: 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=400&h=300&fit=crop',
    category: '指南'
  },
  {
    id: 'tp2',
    title: '春季宠物聚会报名中',
    image: 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&h=300&fit=crop',
    category: '社交'
  },
  {
    id: 'tp3',
    title: '新手养猫必备清单',
    image: 'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400&h=300&fit=crop',
    category: '指南'
  },
  {
    id: 'tp4',
    title: '宠物摄影大赛',
    image: 'https://images.unsplash.com/photo-1530281700549-e82e7bf110d6?w=400&h=300&fit=crop',
    category: '活动'
  },
  {
    id: 'tp5',
    title: '宠物健康饮食分享',
    image: 'https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=400&h=300&fit=crop',
    category: '健康'
  },
  {
    id: 'tp6',
    title: '训犬技巧交流',
    image: 'https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400&h=300&fit=crop',
    category: '训练'
  }
])

const goBack = () => {
  router.back()
}

const openTopic = (topic: Topic) => {
  router.push({ name: 'topicDetail', params: { id: topic.id } })
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <div class="flex items-center justify-between py-md mb-md">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">全部话题</span>
        <div class="w-10"></div>
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div 
          v-for="topic in topics" 
          :key="topic.id"
          @click="openTopic(topic)"
          class="rounded-xl relative overflow-hidden shadow-sm cursor-pointer hover:shadow-md transition-all active:scale-[0.98] h-36"
        >
          <img class="absolute inset-0 w-full h-full object-cover" :src="topic.image" />
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
          <div class="absolute bottom-3 left-3 right-3">
            <span 
              class="text-white px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider mb-1 inline-block"
              :class="topic.category === '指南' ? 'bg-primary/90' : 'bg-secondary/90'"
            >
              {{ topic.category }}
            </span>
            <h3 class="text-white font-label-bold text-label-bold">{{ topic.title }}</h3>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
