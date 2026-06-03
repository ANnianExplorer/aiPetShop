<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { postApi } from '@/api/post'
import { commentApi } from '@/api/comment'
import ShareModal from '@/components/common/ShareModal.vue'
import CommentModal from '@/components/common/CommentModal.vue'
import type { Post, Comment } from '@/types'

const route = useRoute()
const router = useRouter()
const { showToast } = useToast()

const postId = computed(() => Number(route.params.id))

const post = ref<Post | null>(null)
const comments = ref<Comment[]>([])
const loading = ref(true)

const showShareModal = ref(false)
const showCommentModal = ref(false)
const likeAnimating = ref(false)
const bookmarkAnimating = ref(false)

const displayComments = computed(() =>
  comments.value.map(c => ({
    id: String(c.id),
    author: c.user?.nickname ?? '匿名用户',
    avatar: c.user?.avatar ?? '',
    content: c.content,
    createdAt: c.createTime,
    likes: c.likes
  }))
)

const fetchPost = async () => {
  try {
    const res = await postApi.getById(postId.value) as any
    post.value = res
  } catch (e) {
    console.error('Failed to fetch post:', e)
  }
}

const fetchComments = async () => {
  try {
    const res = await commentApi.listPage({ postId: postId.value, pageSize: 50 }) as any
    comments.value = res?.records || []
  } catch (e) {
    console.error('Failed to fetch comments:', e)
  }
}

onMounted(async () => {
  loading.value = true
  await Promise.all([fetchPost(), fetchComments()])
  loading.value = false
})

const toggleLike = async () => {
  if (!post.value) return
  likeAnimating.value = true
  try {
    await postApi.toggleLike(postId.value)
    const wasLiked = post.value.isLiked === 1
    post.value.isLiked = wasLiked ? 0 : 1
    post.value.likes += wasLiked ? -1 : 1
    showToast(wasLiked ? '已取消点赞' : '已点赞', 'success')
  } catch (e) {
    console.error('Failed to toggle like:', e)
  } finally {
    setTimeout(() => {
      likeAnimating.value = false
    }, 300)
  }
}

const toggleFavorite = async () => {
  if (!post.value) return
  bookmarkAnimating.value = true
  try {
    await postApi.toggleFavorite(postId.value)
    const wasFavorited = post.value.isFavorited === 1
    post.value.isFavorited = wasFavorited ? 0 : 1
    showToast(wasFavorited ? '已取消收藏' : '已收藏', 'success')
  } catch (e) {
    console.error('Failed to toggle favorite:', e)
  } finally {
    setTimeout(() => {
      bookmarkAnimating.value = false
    }, 300)
  }
}

const handleCommentSubmit = async (content: string) => {
  try {
    await commentApi.add({ postId: postId.value, content })
    await fetchComments()
    showToast('评论成功', 'success')
  } catch (e) {
    console.error('Failed to add comment:', e)
  }
}

const goBack = () => {
  router.back()
}

const goToUserProfile = (userId?: number) => {
  if (userId != null) {
    router.push({ name: 'userProfile', params: { id: String(userId) } })
  }
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
          <img @click="goToUserProfile(post.user?.id)" class="w-10 h-10 rounded-full border-2 border-primary object-cover cursor-pointer active:scale-95 transition-transform" :src="post.user?.avatar" />
          <div @click="goToUserProfile(post.user?.id)" class="cursor-pointer">
            <p class="font-label-bold text-label-bold text-on-surface">{{ post.user?.nickname }}</p>
            <p class="text-xs text-on-surface-variant">{{ post.createTime }}</p>
          </div>
        </div>

        <div v-if="post.imageList && post.imageList.length > 0" class="rounded-xl overflow-hidden">
          <img class="w-full h-auto object-cover" :src="post.imageList[0]" />
        </div>

        <p class="font-body-md text-body-md text-on-surface leading-relaxed">{{ post.content }}</p>

        <div class="flex gap-sm flex-wrap">
          <span v-for="tag in post.tagList" :key="tag" class="px-3 py-1 bg-primary-container text-primary rounded-full text-xs font-label-bold">
            #{{ tag }}
          </span>
        </div>

        <div class="flex items-center justify-between py-md border-t border-b border-surface-variant/30">
          <button @click="toggleLike" class="flex items-center gap-2 px-4 py-2 rounded-full transition-all active:scale-90" :class="[(post.isLiked === 1) ? 'text-rose-500' : 'text-on-surface-variant hover:bg-surface-container', likeAnimating ? 'scale-125' : '']">
            <span class="material-symbols-outlined transition-all" :class="[(post.isLiked === 1) ? 'fill-current text-rose-500' : '', likeAnimating ? 'scale-125' : '']">{{ (post.isLiked === 1) ? 'favorite' : 'favorite_border' }}</span>
            <span class="font-label-bold">{{ post.likes }}</span>
          </button>
          <button @click="openComment" class="flex items-center gap-2 px-4 py-2 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors active:scale-90">
            <span class="material-symbols-outlined">mode_comment</span>
            <span class="font-label-bold">{{ comments.length }}</span>
          </button>
          <button @click="toggleFavorite" class="flex items-center gap-2 px-4 py-2 rounded-full transition-all active:scale-90" :class="[(post.isFavorited === 1) ? 'text-amber-500' : 'text-on-surface-variant hover:bg-surface-container', bookmarkAnimating ? 'scale-125' : '']">
            <span class="material-symbols-outlined transition-all" :class="[(post.isFavorited === 1) ? 'fill-current text-amber-500' : '', bookmarkAnimating ? 'scale-125' : '']">{{ (post.isFavorited === 1) ? 'bookmark' : 'bookmark_border' }}</span>
          </button>
        </div>
      </div>
    </main>

    <!-- Loading -->
    <div v-else-if="loading" class="pt-20 flex flex-col items-center justify-center min-h-[60vh]">
      <div class="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
      <p class="mt-4 text-on-surface-variant text-sm">加载中...</p>
    </div>

    <!-- Not Found -->
    <div v-else class="pt-20 px-container-padding flex flex-col items-center justify-center min-h-[60vh]">
      <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">error_outline</span>
      <p class="mt-4 font-title-md text-on-surface-variant">帖子不存在</p>
      <button @click="goBack" class="mt-4 px-6 py-2 bg-primary text-on-primary rounded-full font-label-bold">返回</button>
    </div>

    <Teleport to="body">
      <ShareModal
        v-model:visible="showShareModal"
        :post="post ? { title: post.content.slice(0, 30) + '...', image: post.imageList[0] || '', author: post.user?.nickname ?? '' } : null"
      />
    </Teleport>

    <CommentModal
      :visible="showCommentModal"
      :comments="displayComments"
      @close="showCommentModal = false"
      @submit="handleCommentSubmit"
    />
  </div>
</template>
