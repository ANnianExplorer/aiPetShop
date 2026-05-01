<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import TrendingSlider from '@/components/community/TrendingSlider.vue'
import PostFeed from '@/components/community/PostFeed.vue'
import type { Post, Topic } from '@/types'

const router = useRouter()
const userStore = useUserStore()
const { currentUser } = storeToRefs(userStore)

const goToNotifications = () => {
  router.push({ name: 'notifications' })
}

const goToNewTopic = () => {
  router.push({ name: 'newTopic' })
}

const categories = ['全部', '猫咪', '狗狗', '异宠', '医疗健康']
const activeCategory = ref('全部')
const searchQuery = ref('')

const filteredPosts = computed(() => {
  let result = posts.value
  
  if (activeCategory.value !== '全部') {
    result = result.filter(p => p.category === activeCategory.value)
  }
  
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.trim().toLowerCase()
    result = result.filter(p => 
      p.content.toLowerCase().includes(query) || 
      p.author.name.toLowerCase().includes(query) ||
      p.tags.some(t => t.toLowerCase().includes(query))
    )
  }
  
  return result
})

// Mock Data
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
  }
])

const posts = ref<Post[]>([
  {
    id: 'p1',
    author: {
      id: 'u3',
      name: '林间猫影',
      avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop',
      location: '北京'
    },
    content: '今天的阳光太好了，家里的主子已经在阳台晒了一整个下午。大家平时都给主子喂什么零食？',
    images: ['https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400&h=300&fit=crop'],
    tags: ['猫咪日常', '晒晒宠物'],
    createdAt: '2小时前',
    likes: 1200,
    comments: 86,
    category: '猫咪',
    isLiked: false,
    isBookmarked: false
  },
  {
    id: 'p2',
    author: {
      id: 'u4',
      name: '德牧小伍',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
      location: '上海'
    },
    content: '周末的飞盘训练，小伍表现得越来越稳了。这种高强度运动后的拉伸非常重要！',
    images: ['https://images.unsplash.com/photo-1552053831-71594a27632d?w=400&h=300&fit=crop'],
    tags: ['训犬心得', '狗狗运动'],
    createdAt: '5小时前',
    likes: 954,
    comments: 42,
    category: '狗狗',
    isLiked: false,
    isBookmarked: false
  },
  {
    id: 'p3',
    author: {
      id: 'u5',
      name: '兔兔爱好者',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop',
      location: '广州'
    },
    content: '我家小兔子今天学会了新技能，会自己用厕所了！分享一下训练心得。',
    images: ['https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?w=400&h=300&fit=crop'],
    tags: ['异宠', '训练'],
    createdAt: '8小时前',
    likes: 567,
    comments: 34,
    category: '异宠',
    isLiked: false,
    isBookmarked: false
  },
  {
    id: 'p4',
    author: {
      id: 'u6',
      name: '宠物营养师',
      avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop',
      location: '深圳'
    },
    content: '分享一份科学的宠物饮食搭配方案，帮助毛孩子们健康成长。',
    images: ['https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=400&h=300&fit=crop'],
    tags: ['健康', '饮食'],
    createdAt: '1天前',
    likes: 2341,
    comments: 156,
    category: '医疗健康',
    isLiked: false,
    isBookmarked: false
  }
])
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <div class="flex justify-between items-center py-md mb-md">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-primary-container overflow-hidden">
            <img :src="currentUser?.avatar" class="w-full h-full object-cover" />
          </div>
          <span class="text-xl font-bold tracking-tighter text-emerald-800 dark:text-emerald-100 font-['Plus_Jakarta_Sans']">PetLumina</span>
        </div>
        <div class="flex items-center gap-4">
          <button @click="goToNotifications" class="active:scale-95 transition-transform duration-200 hover:bg-emerald-50 p-2 rounded-full">
            <span class="material-symbols-outlined text-emerald-700">notifications</span>
          </button>
        </div>
      </div>

      <!-- Search Bar -->
      <div class="relative flex items-center bg-surface-container-low rounded-full px-4 py-3 shadow-sm group focus-within:ring-2 focus-within:ring-primary/20 transition-all">
        <span class="material-symbols-outlined text-outline mr-3">search</span>
        <input v-model="searchQuery" type="text" placeholder="搜索帖子、用户或话题..." class="bg-transparent border-none focus:ring-0 w-full text-body-md placeholder:text-outline-variant font-body-md outline-none" />
      </div>

      <TrendingSlider :topics="topics" />

      <!-- Category Filters -->
      <section class="flex gap-sm overflow-x-auto no-scrollbar">
        <button 
          v-for="cat in categories" 
          :key="cat"
          @click="activeCategory = cat"
          class="px-md py-sm rounded-full font-label-bold text-label-bold whitespace-nowrap transition-colors"
          :class="activeCategory === cat ? 'bg-primary text-white' : 'bg-surface-container-high text-on-surface-variant hover:bg-primary-fixed'"
        >
          {{ cat }}
        </button>
      </section>

      <PostFeed :posts="filteredPosts" />

      <div v-if="filteredPosts.length === 0" class="flex flex-col items-center justify-center py-20">
        <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">groups</span>
        <p class="mt-4 font-title-md text-on-surface-variant">暂无帖子</p>
      </div>
    </main>

    <!-- Floating Action Button -->
    <button @click="goToNewTopic" class="fixed bottom-24 right-6 w-14 h-14 bg-primary text-white rounded-full shadow-lg flex items-center justify-center active:scale-90 transition-transform z-40">
      <span class="material-symbols-outlined text-[32px]">add</span>
    </button>
  </div>
</template>
