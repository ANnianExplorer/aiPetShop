<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'
import { postApi } from '@/api/post'
import ShareModal from '@/components/common/ShareModal.vue'
import type { Post } from '@/types'

const router = useRouter()
const { showToast } = useToast()
const { t } = useI18n()

const props = defineProps<{
  posts: Post[]
}>()

const showShareModal = ref(false)
const currentSharePost = ref<{ title: string; image: string; author: string } | null>(null)
const likingPosts = ref<Set<string>>(new Set())

const authorName = (post: Post) => post.user?.nickname || t('community.anonymousUser')

const excerptOf = (post: Post) => {
  const text = post.content.trim()
  return text.length > 40 ? `${text.slice(0, 40)}…` : text
}

const toggleLike = async (post: Post) => {
  if (likingPosts.value.has(post.id)) return
  likingPosts.value.add(post.id)
  try {
    const isLiked = await postApi.toggleLike(post.id)
    post.isLiked = isLiked ? 1 : 0
    post.likes += isLiked ? 1 : -1
    showToast(isLiked ? '点赞成功' : '已取消点赞', 'success')
  } catch {
    showToast('操作失败', 'error')
  } finally {
    likingPosts.value.delete(post.id)
  }
}

const toggleBookmark = async (post: Post) => {
  try {
    const isFavorited = await postApi.toggleFavorite(post.id)
    post.isFavorited = isFavorited ? 1 : 0
    showToast(isFavorited ? '收藏成功' : '已取消收藏', 'success')
  } catch {
    showToast('操作失败', 'error')
  }
}

const openComment = (post: Post) => {
  router.push({ name: 'postDetail', params: { id: post.id } })
}

const openShare = (post: Post) => {
  currentSharePost.value = {
    title: post.content.slice(0, 30) + (post.content.length > 30 ? '...' : ''),
    image: (post.imageList && post.imageList[0]) || '',
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
      class="glass-card rounded-xl overflow-hidden shadow-sm border border-white/20 dark:border-surface-variant/20 transition-transform active:scale-[0.98] bg-white/80 dark:bg-surface-container/80 cursor-pointer"
    >
      <RouterLink
        :to="{ name: 'postDetail', params: { id: post.id } }"
        class="block"
        :aria-label="t('a11y.postCard', { author: authorName(post), excerpt: excerptOf(post) })"
      >
        <div class="p-md flex items-center justify-between">
          <div class="flex items-center gap-sm">
            <img class="w-8 h-8 rounded-full border border-surface-variant object-cover" :src="post.user?.avatar" alt="" />
            <div>
              <p class="font-label-bold text-label-bold text-on-surface">{{ post.user?.nickname }}</p>
              <p class="text-[10px] text-outline">{{ post.createTime }} · 坐标 {{ post.user?.location || '未知' }}</p>
            </div>
          </div>
          <button type="button" @click.stop :aria-label="t('a11y.moreActions')" class="text-outline hover:text-primary transition-colors">
            <span class="material-symbols-outlined" aria-hidden="true">more_horiz</span>
          </button>
        </div>

        <div class="aspect-[4/5] w-full overflow-hidden" v-if="post.imageList && post.imageList.length > 0">
          <img class="w-full h-full object-cover" :src="post.imageList[0]" :alt="t('a11y.postImage', { author: authorName(post) })" />
        </div>

        <div class="p-md space-y-sm">
          <p class="font-body-md text-body-md text-on-surface-variant line-clamp-2">
            {{ post.content }}
          </p>
          <div class="flex gap-sm">
            <span 
              v-for="tag in (post.tagList || []).filter(t => !t.startsWith('topic:'))"
              :key="tag"
              class="text-secondary font-label-bold text-[11px]"
            >
              #{{ tag }}
            </span>
          </div>
        </div>
      </RouterLink>

      <div class="flex items-center justify-between px-md pb-md pt-2 border-t border-surface-variant/30">
        <div class="flex items-center gap-md">
          <button type="button" @click.stop="toggleLike(post)" :aria-label="post.isLiked === 1 ? t('a11y.unlikePost', { count: post.likes }) : t('a11y.likePost', { count: post.likes })" class="flex items-center gap-xs transition-colors active:scale-90" :class="post.isLiked === 1 ? 'text-rose-500' : 'text-outline hover:text-rose-500'">
            <span class="material-symbols-outlined text-[20px]" :class="post.isLiked === 1 ? 'fill-current' : ''" aria-hidden="true">favorite</span>
            <span class="text-caption-sm font-label-bold">{{ post.likes }}</span>
          </button>
          <button type="button" @click.stop="openComment(post)" :aria-label="t('a11y.commentPost', { count: post.comments })" class="flex items-center gap-xs text-outline hover:text-emerald-600 transition-colors active:scale-90">
            <span class="material-symbols-outlined text-[20px]" aria-hidden="true">mode_comment</span>
            <span class="text-caption-sm font-label-bold">{{ post.comments }}</span>
          </button>
        </div>
        <div class="flex items-center gap-3">
          <button type="button" @click.stop="toggleBookmark(post)" :aria-label="post.isFavorited === 1 ? t('a11y.unfavoritePost') : t('a11y.favoritePost')" class="transition-colors active:scale-90" :class="post.isFavorited === 1 ? 'text-amber-500' : 'text-outline hover:text-amber-500'">
            <span class="material-symbols-outlined text-[20px]" :class="post.isFavorited === 1 ? 'fill-current' : ''" aria-hidden="true">bookmark</span>
          </button>
          <button type="button" @click.stop="openShare(post)" :aria-label="t('a11y.sharePost')" class="text-outline hover:text-primary transition-colors active:scale-90">
            <span class="material-symbols-outlined text-[20px]" aria-hidden="true">share</span>
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
