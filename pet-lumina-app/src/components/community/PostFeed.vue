<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import ShareModal from '@/components/common/ShareModal.vue'
import type { Post } from '@/types'

const router = useRouter()
const { showToast } = useToast()

const props = defineProps<{
  posts: Post[]
}>()

const showShareModal = ref(false)
const currentSharePost = ref<{ title: string; image: string; author: string } | null>(null)

const navigateToPost = (postId: number) => {
  router.push({ name: 'postDetail', params: { id: postId } })
}

const toggleLike = (post: Post) => {
  const wasLiked = post.isLiked === 1
  post.isLiked = wasLiked ? 0 : 1
  post.likes += wasLiked ? -1 : 1
  showToast(wasLiked ? '已取消点赞' : '已点赞', 'success')
}

const toggleBookmark = (post: Post) => {
  post.isFavorited = post.isFavorited ? 0 : 1
  showToast(post.isFavorited === 1 ? '已收藏' : '已取消收藏', 'success')
}

const openComment = (post: Post) => {
  router.push({ name: 'postDetail', params: { id: post.id } })
}

const openShare = (post: Post) => {
  currentSharePost.value = {
    title: post.content.slice(0, 30) + (post.content.length > 30 ? '...' : ''),
    image: post.imageList[0] || '',
    author: post.user?.nickname || ''
  }
  showShareModal.value = true
}
</script>

<template>
  <section class="grid grid-cols-1 md:grid-cols-2 gap-lg pb-10">
    <article 
      v-for="post in posts" 
      :key="post.id"
      class="glass-card rounded-xl overflow-hidden shadow-sm border border-white/20 transition-transform active:scale-[0.98] bg-white/80 cursor-pointer"
    >
      <div @click="navigateToPost(post.id)" class="block">
        <div class="p-md flex items-center justify-between">
          <div class="flex items-center gap-sm">
            <img class="w-8 h-8 rounded-full border border-surface-variant object-cover" :src="post.user?.avatar" />
            <div>
              <p class="font-label-bold text-label-bold text-on-surface">{{ post.user?.nickname }}</p>
              <p class="text-[10px] text-outline">{{ post.createTime }} · 坐标 {{ post.user?.location || '未知' }}</p>
            </div>
          </div>
          <button @click.stop class="text-outline hover:text-primary transition-colors">
            <span class="material-symbols-outlined">more_horiz</span>
          </button>
        </div>

        <div class="aspect-[4/5] w-full overflow-hidden" v-if="post.imageList.length > 0">
          <img class="w-full h-full object-cover" :src="post.imageList[0]" />
        </div>

        <div class="p-md space-y-sm">
          <p class="font-body-md text-body-md text-on-surface-variant line-clamp-2">
            {{ post.content }}
          </p>
          <div class="flex gap-sm">
            <span 
              v-for="tag in post.tagList" 
              :key="tag"
              class="text-secondary font-label-bold text-[11px]"
            >
              #{{ tag }}
            </span>
          </div>
        </div>
      </div>

      <div class="flex items-center justify-between px-md pb-md pt-2 border-t border-surface-variant/30">
        <div class="flex items-center gap-md">
          <button @click.stop="toggleLike(post)" class="flex items-center gap-xs transition-colors active:scale-90" :class="post.isLiked === 1 ? 'text-rose-500' : 'text-outline hover:text-rose-500'">
            <span class="material-symbols-outlined text-[20px]" :class="post.isLiked === 1 ? 'fill-current' : ''">favorite</span>
            <span class="text-caption-sm font-label-bold">{{ post.likes }}</span>
          </button>
          <button @click.stop="openComment(post)" class="flex items-center gap-xs text-outline hover:text-emerald-600 transition-colors active:scale-90">
            <span class="material-symbols-outlined text-[20px]">mode_comment</span>
            <span class="text-caption-sm font-label-bold">{{ post.comments }}</span>
          </button>
        </div>
        <div class="flex items-center gap-3">
          <button @click.stop="toggleBookmark(post)" class="transition-colors active:scale-90" :class="post.isFavorited === 1 ? 'text-amber-500' : 'text-outline hover:text-amber-500'">
            <span class="material-symbols-outlined text-[20px]" :class="post.isFavorited === 1 ? 'fill-current' : ''">bookmark</span>
          </button>
          <button @click.stop="openShare(post)" class="text-outline hover:text-primary transition-colors active:scale-90">
            <span class="material-symbols-outlined text-[20px]">share</span>
          </button>
        </div>
      </div>
    </article>
  </section>

  <Teleport to="body">
    <ShareModal 
      v-model:visible="showShareModal" 
      :post="currentSharePost" 
    />
  </Teleport>
</template>
