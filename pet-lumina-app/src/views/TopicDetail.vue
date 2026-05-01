<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '@/composables/useToast'
import type { Post } from '@/types'

const router = useRouter()
const route = useRoute()
const { showToast } = useToast()

const topicId = route.params.id as string

const topic = ref({
  id: topicId,
  title: '冬季宠物保暖指南',
  image: 'https://images.unsplash.com/photo-1548199973-03cce0bbc87b?w=600&h=400&fit=crop',
  category: '指南',
  description: '冬天来了，如何让你的宠物温暖过冬？本话题汇集了各种实用的保暖技巧和经验分享。',
  postsCount: 128,
  followers: 2340
})

const relatedPosts = ref<Post[]>([
  {
    id: 'rp1',
    author: {
      id: 'u10',
      name: '暖冬宠物',
      avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop',
      location: '哈尔滨'
    },
    content: '分享我家猫咪的冬季保暖神器，电热毯+小窝，主子舒服得不想出门了！',
    images: ['https://images.unsplash.com/photo-1574158622682-e40e69881006?w=400&h=300&fit=crop'],
    tags: ['保暖', '猫咪'],
    createdAt: '1小时前',
    likes: 456,
    comments: 32,
    category: '猫咪'
  },
  {
    id: 'rp2',
    author: {
      id: 'u11',
      name: '狗狗护理师',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
      location: '北京'
    },
    content: '冬季遛狗注意事项：穿好衣服、注意脚掌保护、控制运动量。',
    images: ['https://images.unsplash.com/photo-1552053831-71594a27632d?w=400&h=300&fit=crop'],
    tags: ['保暖', '狗狗'],
    createdAt: '3小时前',
    likes: 789,
    comments: 56,
    category: '狗狗'
  },
  {
    id: 'rp3',
    author: {
      id: 'u12',
      name: '异宠达人',
      avatar: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop',
      location: '上海'
    },
    content: '仓鼠冬季保暖小贴士：加厚垫料、避免穿堂风、适当增加高热量食物。',
    images: ['https://images.unsplash.com/photo-1585110396000-c9ffd4e4b308?w=400&h=300&fit=crop'],
    tags: ['保暖', '异宠'],
    createdAt: '6小时前',
    likes: 234,
    comments: 18,
    category: '异宠'
  }
])

const isFollowing = ref(false)

const goBack = () => {
  router.back()
}

const goToPostDetail = (postId: string) => {
  router.push({ name: 'postDetail', params: { id: postId } })
}

const toggleFollow = () => {
  isFollowing.value = !isFollowing.value
  showToast(isFollowing.value ? '已关注话题' : '已取消关注', 'success')
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

      <section class="relative rounded-xl overflow-hidden">
        <img :src="topic.image" class="w-full h-48 object-cover" />
        <div class="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent"></div>
        <div class="absolute bottom-4 left-4 right-4">
          <span class="text-white px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider mb-2 inline-block bg-primary/90">
            {{ topic.category }}
          </span>
          <h1 class="text-white font-headline-sm text-headline-sm">{{ topic.title }}</h1>
        </div>
      </section>

      <section class="bg-surface-container-low rounded-xl p-4">
        <p class="text-body-md text-on-surface leading-relaxed">{{ topic.description }}</p>
        <div class="flex gap-6 mt-4 pt-4 border-t border-outline-variant/20">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-sm">forum</span>
            <span class="text-label-bold text-on-surface-variant">{{ topic.postsCount }} 篇帖子</span>
          </div>
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-sm">group</span>
            <span class="text-label-bold text-on-surface-variant">{{ topic.followers }} 人关注</span>
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
              <img :src="post.author.avatar" class="w-8 h-8 rounded-full object-cover" />
              <div class="flex-1">
                <p class="font-label-bold text-label-bold text-on-surface">{{ post.author.name }}</p>
                <p class="text-[10px] text-outline-variant">{{ post.createdAt }}</p>
              </div>
            </div>
            <img v-if="post.images.length > 0" :src="post.images[0]" class="w-full h-40 object-cover" />
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
