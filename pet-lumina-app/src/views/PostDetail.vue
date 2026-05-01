<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import ShareModal from '@/components/common/ShareModal.vue'
import CommentModal from '@/components/common/CommentModal.vue'
import type { Post } from '@/types'

const route = useRoute()
const router = useRouter()
const { showToast } = useToast()

const postId = computed(() => route.params.id as string)

const mockPosts: Record<string, Post> = {
  p1: {
    id: 'p1',
    author: {
      id: 'u3',
      name: '林间猫影',
      avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop',
      location: '北京'
    },
    content: '今天的阳光太好了，家里的主子已经在阳台晒了一整个下午。看着它慵懒的样子，感觉所有的疲惫都被治愈了。大家平时都给主子喂什么零食？我家猫特别喜欢吃冻干鸡肉，但是不知道吃多了好不好。最近也在考虑给它换一种猫粮，有没有推荐的品牌？',
    images: [
      'https://images.unsplash.com/photo-1574158622682-e40e69881006?w=600&h=400&fit=crop',
      'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=600&h=400&fit=crop'
    ],
    tags: ['猫咪日常', '晒晒宠物'],
    createdAt: '2小时前',
    likes: 1200,
    comments: 86,
    category: '猫咪',
    isLiked: false,
    isBookmarked: false
  },
  p2: {
    id: 'p2',
    author: {
      id: 'u4',
      name: '德牧小伍',
      avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop',
      location: '上海'
    },
    content: '周末的飞盘训练，小伍表现得越来越稳了。这种高强度运动后的拉伸非常重要！今天训练了将近两个小时，小伍的接盘成功率已经达到了80%以上。分享一下我们的训练心得：首先要从近距离开始，慢慢增加距离；其次要注意狗狗的体力，适时休息；最后，训练结束后的奖励必不可少！',
    images: [
      'https://images.unsplash.com/photo-1552053831-71594a27632d?w=600&h=400&fit=crop'
    ],
    tags: ['训犬心得', '狗狗运动'],
    createdAt: '5小时前',
    likes: 954,
    comments: 42,
    category: '狗狗',
    isLiked: false,
    isBookmarked: false
  }
}

const post = computed(() => mockPosts[postId.value] || null)

const isLiked = ref(false)
const isBookmarked = ref(false)
const showShareModal = ref(false)
const showCommentModal = ref(false)
const likeAnimating = ref(false)
const bookmarkAnimating = ref(false)

const comments = ref([
  { id: 'c1', author: '爱猫人士', avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=100&h=100&fit=crop', content: '太可爱了！我家猫也特别喜欢晒太阳', createdAt: '1小时前', likes: 12 },
  { id: 'c2', author: '宠物营养师', avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop', content: '冻干鸡肉是很好的零食，但要注意控制量哦', createdAt: '30分钟前', likes: 8 }
])

const toggleLike = () => {
  likeAnimating.value = true
  isLiked.value = !isLiked.value
  showToast(isLiked.value ? '已点赞' : '已取消点赞', 'success')
  setTimeout(() => {
    likeAnimating.value = false
  }, 300)
}

const toggleBookmark = () => {
  bookmarkAnimating.value = true
  isBookmarked.value = !isBookmarked.value
  showToast(isBookmarked.value ? '已收藏' : '已取消收藏', 'success')
  setTimeout(() => {
    bookmarkAnimating.value = false
  }, 300)
}

const handleCommentSubmit = (content: string) => {
  comments.value.unshift({
    id: `c${Date.now()}`,
    author: '我',
    avatar: 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=100&h=100&fit=crop',
    content,
    createdAt: '刚刚',
    likes: 0
  })
}

const goBack = () => {
  router.back()
}

const goToUserProfile = (userId: string) => {
  router.push({ name: 'userProfile', params: { id: userId } })
}

const openShare = () => {
  showShareModal.value = true
}

const openComment = () => {
  showCommentModal.value = true
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main v-if="post" class="pt-4">
      <div class="p-container-padding space-y-lg max-w-screen-xl mx-auto">
        <div class="flex items-center justify-between py-md mb-md">
          <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
            <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
          </button>
          <span class="font-title-sm text-on-surface">帖子详情</span>
          <button @click="openShare" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
            <span class="material-symbols-outlined text-emerald-700">share</span>
          </button>
        </div>

        <div class="flex items-center gap-sm">
          <img @click="goToUserProfile(post.author.id)" class="w-10 h-10 rounded-full border-2 border-primary object-cover cursor-pointer active:scale-95 transition-transform" :src="post.author.avatar" />
          <div @click="goToUserProfile(post.author.id)" class="cursor-pointer">
            <p class="font-label-bold text-label-bold text-on-surface">{{ post.author.name }}</p>
            <p class="text-xs text-on-surface-variant">{{ post.createdAt }} · {{ post.author.location }}</p>
          </div>
        </div>

        <div v-if="post.images.length > 0" class="rounded-xl overflow-hidden">
          <img class="w-full h-auto object-cover" :src="post.images[0]" />
        </div>

        <p class="font-body-md text-body-md text-on-surface leading-relaxed">{{ post.content }}</p>

        <div class="flex gap-sm flex-wrap">
          <span v-for="tag in post.tags" :key="tag" class="px-3 py-1 bg-primary-container text-primary rounded-full text-xs font-label-bold">
            #{{ tag }}
          </span>
        </div>

        <div class="flex items-center justify-between py-md border-t border-b border-surface-variant/30">
          <button @click="toggleLike" class="flex items-center gap-2 px-4 py-2 rounded-full transition-all active:scale-90" :class="[isLiked ? 'text-rose-500' : 'text-on-surface-variant hover:bg-surface-container', likeAnimating ? 'scale-125' : '']">
            <span class="material-symbols-outlined transition-all" :class="[isLiked ? 'fill-current text-rose-500' : '', likeAnimating ? 'scale-125' : '']">{{ isLiked ? 'favorite' : 'favorite_border' }}</span>
            <span class="font-label-bold">{{ post.likes + (isLiked ? 1 : 0) }}</span>
          </button>
          <button @click="openComment" class="flex items-center gap-2 px-4 py-2 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors active:scale-90">
            <span class="material-symbols-outlined">mode_comment</span>
            <span class="font-label-bold">{{ comments.length }}</span>
          </button>
          <button @click="toggleBookmark" class="flex items-center gap-2 px-4 py-2 rounded-full transition-all active:scale-90" :class="[isBookmarked ? 'text-amber-500' : 'text-on-surface-variant hover:bg-surface-container', bookmarkAnimating ? 'scale-125' : '']">
            <span class="material-symbols-outlined transition-all" :class="[isBookmarked ? 'fill-current text-amber-500' : '', bookmarkAnimating ? 'scale-125' : '']">{{ isBookmarked ? 'bookmark' : 'bookmark_border' }}</span>
          </button>
        </div>
      </div>
    </main>

    <div v-else class="pt-20 px-container-padding flex flex-col items-center justify-center min-h-[60vh]">
      <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">error_outline</span>
      <p class="mt-4 font-title-md text-on-surface-variant">帖子不存在</p>
      <button @click="goBack" class="mt-4 px-6 py-2 bg-primary text-on-primary rounded-full font-label-bold">返回</button>
    </div>

    <ShareModal 
      :visible="showShareModal" 
      :post="post ? { title: post.content.slice(0, 30) + '...', image: post.images[0] || '', author: post.author.name } : null" 
      @close="showShareModal = false" 
    />

    <CommentModal 
      :visible="showCommentModal" 
      :comments="comments" 
      @close="showCommentModal = false" 
      @submit="handleCommentSubmit" 
    />
  </div>
</template>
