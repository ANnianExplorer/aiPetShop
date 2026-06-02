<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { topicApi } from '@/api/topic'
import type { Topic, Post } from '@/types'

const router = useRouter()
const route = useRoute()
const { showToast } = useToast()

const topicId = computed(() => Number(route.params.id))

const topic = ref<Topic | null>(null)
const relatedPosts = ref<Post[]>([])
const isFollowing = ref(false)

onMounted(async () => {
  try {
    const topicData = await topicApi.getById(topicId.value) as any
    topic.value = topicData
    isFollowing.value = topicData?.isFollowed === 1

    const postsRes = await topicApi.listTopicPosts({ topicId: topicId.value, pageSize: 10 }) as any
    relatedPosts.value = postsRes?.records || []
  } catch (error) {
    console.error('Failed to fetch topic detail:', error)
  }
})

const goBack = () => {
  router.back()
}

const goToPostDetail = (postId: number) => {
  router.push({ name: 'postDetail', params: { id: postId } })
}

const toggleFollow = async () => {
  try {
    await topicApi.toggleFollow(topicId.value)
    isFollowing.value = !isFollowing.value
    if (topic.value) {
      topic.value.followerCount += isFollowing.value ? 1 : -1
    }
    showToast(isFollowing.value ? '已关注话题' : '已取消关注', 'success')
  } catch (error) {
    console.error('Failed to toggle follow:', error)
  }
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <div class="flex items-center justify-between py-md mb-md">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">话题详情</span>
        <button 
          @click="toggleFollow"
          class="active:scale-95 transition-transform px-4 py-2 rounded-full font-label-bold text-label-bold"
          :class="isFollowing ? 'bg-primary text-white' : 'bg-surface-container-high text-on-surface'"
        >
          {{ isFollowing ? '已关注' : '关注' }}
        </button>
      </div>

      <section v-if="topic" class="relative rounded-xl overflow-hidden">
        <img :src="topic.image" class="w-full h-48 object-cover" />
        <div class="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent"></div>
        <div class="absolute bottom-4 left-4 right-4">
          <span class="text-white px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider mb-2 inline-block bg-primary/90">
            {{ topic.category }}
          </span>
          <h1 class="text-white font-headline-sm text-headline-sm">{{ topic.title }}</h1>
        </div>
      </section>

      <section v-if="topic" class="bg-surface-container-low rounded-xl p-4">
        <p class="text-body-md text-on-surface leading-relaxed">{{ topic.description }}</p>
        <div class="flex gap-6 mt-4 pt-4 border-t border-outline-variant/20">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-sm">forum</span>
            <span class="text-label-bold text-on-surface-variant">{{ topic.postCount }} 篇帖子</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-sm">group</span>
            <span class="text-label-bold text-on-surface-variant">{{ topic.followerCount }} 人关注</span>
          </div>
        </div>
      </section>

      <section>
        <h2 class="font-title-sm text-title-sm text-on-surface mb-4">相关帖子</h2>
        <div class="space-y-4">
          <div 
            v-for="post in relatedPosts" 
            :key="post.id"
            @click="goToPostDetail(post.id)"
            class="bg-surface-container-low rounded-xl overflow-hidden shadow-sm cursor-pointer active:scale-95 transition-transform"
          >
            <div class="flex items-center gap-3 p-4 pb-2">
              <img :src="post.user?.avatar" class="w-8 h-8 rounded-full object-cover" />
              <div class="flex-1">
                <p class="font-label-bold text-label-bold text-on-surface">{{ post.user?.nickname }}</p>
                <p class="text-[10px] text-outline-variant">{{ post.createTime }}</p>
              </div>
            </div>
            <img v-if="post.imageList.length > 0" :src="post.imageList[0]" class="w-full h-40 object-cover" />
            <div class="p-4 pt-2">
              <p class="text-body-md text-on-surface leading-relaxed">{{ post.content }}</p>
              <div class="flex items-center gap-4 mt-3">
                <div class="flex items-center gap-1 text-outline-variant">
                  <span class="material-symbols-outlined text-sm">favorite</span>
                  <span class="text-xs">{{ post.likes }}</span>
                </div>
                <div class="flex items-center gap-1 text-outline-variant">
                  <span class="material-symbols-outlined text-sm">chat_bubble</span>
                  <span class="text-xs">{{ post.comments }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
