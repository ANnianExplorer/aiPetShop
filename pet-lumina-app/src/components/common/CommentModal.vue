<script setup lang="ts">
import { ref } from 'vue'
import { useToast } from '@/composables/useToast'
import { commentApi } from '@/api/comment'
import EmojiPicker from './EmojiPicker.vue'

interface CommentItem {
  id: string
  author: string
  avatar: string
  content: string
  createdAt: string
  likes: number
  isLiked?: number
}

const props = defineProps<{
  visible: boolean
  comments: CommentItem[]
  postId?: string
}>()

const emit = defineEmits<{
  close: []
  submit: [content: string]
}>()

const { showToast } = useToast()
const commentText = ref('')
const showEmojiPicker = ref(false)
const commentInputRef = ref<HTMLInputElement | null>(null)

const handleSubmit = () => {
  if (commentText.value.trim()) {
    emit('submit', commentText.value)
    commentText.value = ''
  }
}

const handleEmojiSelect = (emoji: string) => {
  commentText.value += emoji
  commentInputRef.value?.focus()
}

const toggleEmojiPicker = () => {
  showEmojiPicker.value = !showEmojiPicker.value
}

const toggleLike = async (comment: CommentItem) => {
  try {
    const isLiked = await commentApi.toggleLike(comment.id) as any
    comment.isLiked = isLiked ? 1 : 0
    comment.likes += isLiked ? 1 : -1
  } catch {
    showToast('操作失败', 'error')
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="comment-modal">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-end justify-center">
        <div class="absolute inset-0 bg-black/30" @click="emit('close')"></div>

        <div class="relative w-full max-w-lg bg-surface-container-low rounded-t-3xl overflow-hidden animate-slide-up">
          <div class="p-4 pb-6">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-title-sm text-title-sm text-on-surface">评论 ({{ comments.length }})</h3>
              <button @click="emit('close')" class="p-2 rounded-full hover:bg-surface-container-high transition-colors">
                <span class="material-symbols-outlined text-on-surface-variant">close</span>
              </button>
            </div>

            <div class="space-y-md max-h-64 overflow-y-auto no-scrollbar mb-4">
              <div v-for="comment in comments" :key="comment.id" class="flex gap-sm">
                <img class="w-8 h-8 rounded-full object-cover flex-shrink-0" :src="comment.avatar" />
                <div class="flex-1">
                  <div class="bg-surface-container rounded-xl p-sm">
                    <p class="font-label-bold text-label-bold text-on-surface">{{ comment.author }}</p>
                    <p class="font-body-sm text-body-sm text-on-surface-variant mt-1">{{ comment.content }}</p>
                  </div>
                  <div class="flex items-center gap-md mt-1 px-2">
                    <span class="text-xs text-on-surface-variant">{{ comment.createdAt }}</span>
                    <button @click="toggleLike(comment)" class="text-xs flex items-center gap-1 transition-colors"
                      :class="comment.isLiked === 1 ? 'text-rose-500' : 'text-on-surface-variant hover:text-primary'">
                      <span class="material-symbols-outlined text-sm">{{ comment.isLiked === 1 ? 'favorite' : 'favorite_border' }}</span>
                      {{ comment.likes }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div class="flex items-center gap-sm">
              <div class="flex-1 flex items-center bg-surface-container rounded-full px-4 py-2">
                <input
                  ref="commentInputRef"
                  v-model="commentText"
                  @keyup.enter="handleSubmit"
                  placeholder="写下你的评论..."
                  class="flex-1 bg-transparent font-body-sm text-on-surface focus:outline-none"
                />
                <button @click="toggleEmojiPicker" class="ml-2 text-on-surface-variant hover:text-primary transition-colors active:scale-90">
                  <span class="material-symbols-outlined text-xl">mood</span>
                </button>
              </div>
              <button @click="handleSubmit" class="w-10 h-10 bg-primary text-on-primary rounded-full flex items-center justify-center active:scale-95 transition-transform" :class="{ 'opacity-50': !commentText.trim() }">
                <span class="material-symbols-outlined">send</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <EmojiPicker
    :visible="showEmojiPicker"
    @select="handleEmojiSelect"
    @close="showEmojiPicker = false"
  />
</template>

<style scoped>
@keyframes slide-up {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}

.animate-slide-up {
  animation: slide-up 0.3s ease-out;
}

.comment-modal-enter-active,
.comment-modal-leave-active {
  transition: opacity 0.3s ease;
}

.comment-modal-enter-from,
.comment-modal-leave-to {
  opacity: 0;
}
</style>
