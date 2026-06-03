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
      <!-- Header -->
      <div class="flex justify-between items-center py-md mb-md animate-float-up">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-primary-container overflow-hidden shadow-md">
            <img :src="currentUser?.avatar" class="w-full h-full object-cover" />
          </div>
          <span class="text-xl font-bold tracking-tighter text-primary font-['Plus_Jakarta_Sans']">PetLumina</span>
        </div>
        <div class="flex items-center gap-4">
          <button @click="goToNotifications" class="icon-btn p-2 rounded-full">
            <span class="material-symbols-outlined text-primary">notifications</span>
          </button>
        </div>
      </div>

      <!-- Search Bar -->
      <div class="relative flex items-center glass-panel rounded-full px-4 py-3 depth-1 group focus-within:ring-2 focus-within:ring-primary/20 transition-all animate-float-up stagger-1">
        <span class="material-symbols-outlined text-outline mr-3">search</span>
        <input v-model="searchQuery" type="text" placeholder="搜索帖子、用户或话题..." class="bg-transparent border-none focus:ring-0 w-full text-body-md placeholder:text-outline-variant font-body-md outline-none" />
      </div>

      <div class="animate-float-up stagger-2">
        <TrendingSlider :topics="topics" />
      </div>

      <!-- Category Filters -->
      <section class="flex gap-sm overflow-x-auto no-scrollbar animate-float-up stagger-3">
        <button
          v-for="cat in categories"
          :key="cat"
          @click="activeCategory = cat"
          class="px-md py-sm rounded-full font-label-bold text-label-bold whitespace-nowrap transition-all duration-300 btn-jelly"
          :class="activeCategory === cat
            ? 'bg-primary text-white shadow-lg shadow-primary/20'
            : 'glass-panel text-on-surface-variant hover:bg-white/50'"
        >
          {{ cat }}
        </button>
      </section>

      <div class="animate-float-up stagger-4">
        <PostFeed :posts="filteredPosts" />
      </div>

      <div v-if="filteredPosts.length === 0" class="flex flex-col items-center justify-center py-20 animate-fade-in">
        <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">groups</span>
        <p class="mt-4 font-title-md text-on-surface-variant">暂无帖子</p>
      </div>
    </main>

    <!-- Floating Action Button -->
    <button
      @click="goToNewTopic"
      class="fixed bottom-24 right-6 w-14 h-14 bg-primary text-white rounded-full shadow-[0_8px_24px_rgba(75,100,85,0.3)] flex items-center justify-center z-40 btn-jelly animate-scale-in"
      style="animation-delay: 0.5s"
    >
      <span class="material-symbols-outlined text-[32px]">add</span>
    </button>
  </div>
</template>
