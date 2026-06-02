<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { Post } from '@/types'

const router = useRouter()

defineProps<{
  trends: Post[]
}>()

const goToCommunity = () => {
  router.push({ name: 'community' })
}

const goToPost = (postId: number) => {
  router.push({ name: 'postDetail', params: { id: postId } })
}
</script>

<template>
  <section class="pb-10">
    <div class="flex justify-between items-end mb-md">
      <h2 class="font-headline-md text-headline-md">社区动态</h2>
      <span @click="goToCommunity" class="font-label-bold text-label-bold text-primary cursor-pointer hover:opacity-80 transition-opacity">发现更多</span>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-lg">
      <div 
        v-for="post in trends" 
        :key="post.id"
        @click="goToPost(post.id)"
        class="group rounded-3xl overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow cursor-pointer active:scale-[0.98]"
      >
        <div class="h-48 overflow-hidden">
          <img class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" :src="post.imageList[0]" />
        </div>
        <div class="p-md">
          <div class="flex items-center gap-2 mb-2">
            <div class="w-6 h-6 rounded-full bg-surface-variant overflow-hidden">
              <img class="w-full h-full object-cover" :src="post.user?.avatar" />
            </div>
            <span class="font-label-bold text-caption-sm opacity-60">由 {{ post.user?.nickname }} 分享</span>
          </div>
          <h4 class="font-title-sm text-title-sm mb-1">{{ post.content.split('，')[0] }}</h4>
          <p class="font-body-md text-sm text-on-surface-variant line-clamp-2">{{ post.content }}</p>
        </div>
      </div>
    </div>
  </section>
</template>
