<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import type { Post } from '@/types'

const route = useRoute()
const router = useRouter()
const { showToast } = useToast()

const userId = computed(() => route.params.id as string)

const mockUsers: Record<string, {
  id: string
  name: string
  avatar: string
  location: string
  bio: string
  postsCount: number
  followers: number
  following: number
  posts: Post[]
}> = {
  u3: {
    id: 'u3',
    name: '林间猫影',
    avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop',
    location: '北京',
    bio: '猫咪爱好者 | 分享猫咪日常 | 家有两只布偶猫',
    postsCount: 128,
    followers: 2340,
    following: 156,
    posts: [
      {
        id: 'p1',
        author: { id: 'u3', name: '林间猫影', avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop', location: '北京' },
        content: '今天的阳光太好了，家里的主子已经在阳台晒了一整个下午。看着它慵懒的样子，感觉所有的疲惫都被治愈了。',
        images: ['https://images.unsplash.com/photo-1574158622682-e40e69881006?w=600&h=400&fit=crop'],
        tags: ['猫咪日常', '晒晒宠物'],
        createdAt: '2小时前',
        likes: 1200,
        comments: 86,
        category: '猫咪'
      },
      {
        id: 'p10',
        author: { id: 'u3', name: '林间猫影', avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop', location: '北京' },
        content: '新买的猫爬架到了，两只主子抢着玩，太可爱了！',
        images: ['https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&h=400&fit=crop'],
        tags: ['猫咪', '好物分享'],
        createdAt: '1天前',
        likes: 856,
        comments: 42,
        category: '猫咪'
      }
    ]
  },
  u4: {
    id: 'u4',
    name: '德牧小伍',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
    location: '上海',
    bio: '德牧训练师 | 分享训犬心得 | 运动达人',
    postsCount: 86,
    followers: 1560,
    following: 230,
    posts: [
      {
        id: 'p2',
        author: { id: 'u4', name: '德牧小伍', avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop', location: '上海' },
        content: '周末的飞盘训练，小伍表现得越来越稳了。这种高强度运动后的拉伸非常重要！',
        images: ['https://images.unsplash.com/photo-1552053831-71594a27632d?w=600&h=400&fit=crop'],
        tags: ['训犬心得', '狗狗运动'],
        createdAt: '5小时前',
        likes: 954,
        comments: 42,
        category: '狗狗'
      }
    ]
  }
}

const user = computed(() => mockUsers[userId.value] || null)
const isFollowing = ref(false)

const goBack = () => {
  router.back()
}

const toggleFollow = () => {
  isFollowing.value = !isFollowing.value
  showToast(isFollowing.value ? '已关注' : '已取消关注', 'success')
}

const goToPostDetail = (postId: string) => {
  router.push({ name: 'postDetail', params: { id: postId } })
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main v-if="user" class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <div class="flex items-center justify-between py-md mb-md">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">用户主页</span>
        <div class="w-10"></div>
      </div>

      <section class="bg-surface-container-low rounded-xl p-6 text-center">
        <img :src="user.avatar" class="w-20 h-20 rounded-full object-cover mx-auto mb-4 border-4 border-primary" />
        <h1 class="font-headline-sm text-headline-sm text-on-surface">{{ user.name }}</h1>
        <p class="text-body-sm text-on-surface-variant mt-1">{{ user.location }}</p>
        <p class="text-body-md text-on-surface mt-3">{{ user.bio }}</p>

        <div class="flex justify-center gap-8 mt-6 pt-6 border-t border-outline-variant/20">
          <div class="text-center">
            <p class="font-title-md text-title-md text-on-surface">{{ user.postsCount }}</p>
            <p class="text-label-sm text-on-surface-variant">帖子</p>
          </div>
          <div class="text-center">
            <p class="font-title-md text-title-md text-on-surface">{{ user.followers }}</p>
            <p class="text-label-sm text-on-surface-variant">粉丝</p>
          </div>
          <div class="text-center">
            <p class="font-title-md text-title-md text-on-surface">{{ user.following }}</p>
            <p class="text-label-sm text-on-surface-variant">关注</p>
          </div>
        </div>

        <button 
          @click="toggleFollow"
          class="mt-6 w-full py-3 rounded-full font-title-sm text-title-sm transition-all active:scale-95"
          :class="isFollowing ? 'bg-surface-container-high text-on-surface' : 'bg-primary text-on-primary'"
        >
          {{ isFollowing ? '已关注' : '关注' }}
        </button>
      </section>

      <section>
        <h2 class="font-title-sm text-title-sm text-on-surface mb-4">TA 的帖子</h2>
        <div class="space-y-4">
          <div 
            v-for="post in user.posts" 
            :key="post.id"
            @click="goToPostDetail(post.id)"
            class="bg-surface-container-low rounded-xl overflow-hidden shadow-sm cursor-pointer active:scale-95 transition-transform"
          >
            <img v-if="post.images.length > 0" :src="post.images[0]" class="w-full h-40 object-cover" />
            <div class="p-4">
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

    <div v-else class="pt-20 px-container-padding flex flex-col items-center justify-center min-h-[60vh]">
      <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">error_outline</span>
      <p class="mt-4 font-title-md text-on-surface-variant">用户不存在</p>
      <button @click="goBack" class="mt-4 px-6 py-2 bg-primary text-on-primary rounded-full font-label-bold">返回</button>
    </div>
  </div>
</template>
