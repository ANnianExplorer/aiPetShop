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
      <span @click="goToCommunity" class="font-label-bold text-label-bold text-primary cursor-pointer active:opacity-50 transition-opacity">发现更多</span>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-lg">
      <div
        v-for="(post, index) in trends"
        :key="post.id"
        @click="goToPost(post.id)"
        class="group rounded-2xl overflow-hidden glass-card cursor-pointer ripple-card anim-float"
        :style="{ animationDelay: `${index * -1.2}s` }"
      >
        <div class="h-48 overflow-hidden relative">
          <img class="w-full h-full object-cover group-active:scale-110 transition-transform duration-500" :src="post.imageList[0]" />
          <!-- Shimmer overlay -->
          <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full animate-[shimmerSweep_5s_ease-in-out_infinite]" :style="{ animationDelay: `${index * -2}s` }"></div>
        </div>
        <div class="p-md relative z-10">
          <div class="flex items-center gap-2 mb-2">
            <div class="w-6 h-6 rounded-full bg-surface-variant overflow-hidden shadow-sm">
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
