<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import TrendingSlider from '@/components/community/TrendingSlider.vue'
import PostFeed from '@/components/community/PostFeed.vue'
import type { Post, Topic } from '@/types'
import { postApi } from '@/api/post'
import { topicApi } from '@/api/topic'

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
      p.user?.nickname?.toLowerCase().includes(query) ||
      p.tagList?.some(t => t.toLowerCase().includes(query))
    )
  }
  
  return result
})

const topics = ref<Topic[]>([])
const posts = ref<Post[]>([])

onMounted(async () => {
  try {
    const [topicRes, postRes] = await Promise.all([
      topicApi.listPage({ pageSize: 10 }),
      postApi.listPage({ pageSize: 10 })
    ])
    topics.value = (topicRes as any)?.records ?? []
    posts.value = (postRes as any)?.records ?? []
  } catch (e) {
    console.error('Failed to fetch community data:', e)
  }
})
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
