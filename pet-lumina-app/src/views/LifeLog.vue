<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import LogCard from '@/components/lifelog/LogCard.vue'
import type { LogEntry } from '@/types'

const router = useRouter()
const userStore = useUserStore()
const { currentUser, currentPet } = storeToRefs(userStore)

const goToNotifications = () => {
  router.push({ name: 'notifications' })
}

const categories = ['全部', '日常', '健康', '户外']
const activeCategory = ref('全部')
const searchQuery = ref('')

const filteredLogs = computed(() => {
  let result = logs.value
  
  if (activeCategory.value !== '全部') {
    result = result.filter(l => l.tags.some(t => t.includes(activeCategory.value)))
  }
  
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.trim().toLowerCase()
    result = result.filter(l => 
      l.title.toLowerCase().includes(query) || 
      l.description.toLowerCase().includes(query) ||
      l.tags.some(t => t.toLowerCase().includes(query))
    )
  }
  
  return result
})

const goToNewTopic = () => {
  router.push({ name: 'newTopic' })
}

const logs = ref<LogEntry[]>([
  {
    id: 'l1',
    petId: 'pet1',
    type: 'feeding',
    title: '午后阳光下的惬意时光',
    description: '今天天气特别好，小宝贝在阳台上晒了一整个下午的太阳。看着它慵懒的样子，感觉所有的疲惫都被治愈了。',
    images: ['https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400&h=300&fit=crop'],
    tags: ['猫咪', '日常'],
    createdAt: '2小时前'
  },
  {
    id: 'l2',
    petId: 'pet1',
    type: 'walking',
    title: '今天在草地上跑疯了！',
    description: '周末带小伍去了附近的公园，它跑得特别开心，还和其他狗狗玩了一会儿。运动量完全达标！',
    images: ['https://images.unsplash.com/photo-1552053831-71594a27632d?w=400&h=300&fit=crop'],
    tags: ['狗狗', '户外'],
    createdAt: '昨天 16:20'
  },
  {
    id: 'l3',
    petId: 'pet1',
    type: 'medical',
    title: '年度体检报告：非常健康',
    description: '今天带小宝贝去做了年度体检，结果显示一切正常。体重、牙齿、毛发状态都很好。继续保持！',
    images: ['https://images.unsplash.com/photo-1628009368231-7bb7cfcb0def?w=400&h=300&fit=crop'],
    tags: ['体检', '健康'],
    createdAt: '3天前'
  },
  {
    id: 'l4',
    petId: 'pet1',
    type: 'walking',
    title: '今日份城市漫步',
    description: '傍晚时分带着小宝贝在小区附近散步，秋天的风景真美。它特别喜欢闻路边的花草。',
    images: ['https://images.unsplash.com/photo-1601758228041-f3b2795255f1?w=400&h=300&fit=crop'],
    tags: ['散步', '户外'],
    createdAt: '5天前'
  }
])
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex justify-between items-center py-md mb-md">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-primary-fixed overflow-hidden border border-primary/10">
            <img :src="currentPet?.avatar" class="w-full h-full object-cover" />
          </div>
          <h1 class="text-xl font-bold tracking-tighter text-emerald-800 dark:text-emerald-100 font-['Plus_Jakarta_Sans']">PetLumina</h1>
        </div>
        <div class="flex gap-4">
          <button @click="goToNotifications" class="material-symbols-outlined text-emerald-700 dark:text-emerald-400 active:scale-95 transition-transform duration-200">notifications</button>
        </div>
      </div>
      <!-- Search Bar Section -->
      <div class="mt-4 mb-6">
        <div class="relative flex items-center bg-surface-container-low rounded-full px-4 py-3 shadow-sm group focus-within:ring-2 focus-within:ring-primary/20 transition-all">
          <span class="material-symbols-outlined text-outline mr-3">search</span>
          <input v-model="searchQuery" type="text" placeholder="搜索记录、好友或动态..." class="bg-transparent border-none focus:ring-0 w-full text-body-md placeholder:text-outline-variant font-body-md outline-none" />
        </div>
      </div>

      <!-- Category Tabs -->
      <div class="flex gap-3 overflow-x-auto pb-4 no-scrollbar">
        <button 
          v-for="cat in categories" 
          :key="cat"
          @click="activeCategory = cat"
          class="px-6 py-2 rounded-full font-label-bold whitespace-nowrap shadow-sm transition-colors"
          :class="activeCategory === cat ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-on-surface-variant hover:bg-emerald-50'"
        >
          {{ cat }}
        </button>
      </div>

      <!-- Masonry Grid Layout -->
      <div class="columns-2 gap-card-gutter mt-2">
        <LogCard 
          v-for="log in filteredLogs" 
          :key="log.id" 
          :log="log" 
        />
      </div>

      <div v-if="filteredLogs.length === 0" class="flex flex-col items-center justify-center py-20">
        <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">edit_note</span>
        <p class="mt-4 font-title-md text-on-surface-variant">暂无记录</p>
      </div>
    </main>

    <!-- Floating Action Button -->
    <button @click="goToNewTopic" class="fixed bottom-24 right-6 w-14 h-14 bg-primary text-on-primary rounded-full flex items-center justify-center shadow-xl z-40 active:scale-90 transition-all">
      <span class="material-symbols-outlined text-3xl">add</span>
    </button>
  </div>
</template>
