<script setup lang="ts">
import { ref } from 'vue'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()

const props = defineProps<{
  visible: boolean
  post: {
    title: string
    image: string
    author: string
  } | null
}>()

const emit = defineEmits<{
  close: []
}>()

const shareToWechat = () => {
  showToast('已分享到微信', 'success')
  emit('close')
}

const shareToQQ = () => {
  showToast('已分享到QQ', 'success')
  emit('close')
}

const shareToWeibo = () => {
  showToast('已分享到微博', 'success')
  emit('close')
}

const copyLink = () => {
  showToast('链接已复制', 'success')
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="fixed inset-0 z-50 flex items-end justify-center">
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="emit('close')"></div>
        
        <div class="relative w-full max-w-lg bg-surface-container-low rounded-t-3xl overflow-hidden animate-slide-up">
          <div class="p-6 pb-4">
            <div class="flex justify-between items-center mb-4">
              <h3 class="font-title-sm text-title-sm text-on-surface">分享到</h3>
              <button @click="emit('close')" class="p-2 rounded-full hover:bg-surface-container-high transition-colors">
                <span class="material-symbols-outlined text-on-surface-variant">close</span>
              </button>
            </div>

            <div v-if="post" class="flex items-center gap-3 p-3 bg-surface-container rounded-xl mb-6">
              <img :src="post.image" class="w-16 h-16 rounded-lg object-cover flex-shrink-0" />
              <div class="flex-1 min-w-0">
                <p class="font-label-bold text-label-bold text-on-surface truncate">{{ post.title }}</p>
                <p class="text-xs text-outline-variant mt-1">by {{ post.author }}</p>
              </div>
            </div>

            <div class="grid grid-cols-4 gap-4">
              <button @click="shareToWechat" class="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-surface-container-high transition-colors active:scale-95">
                <div class="w-12 h-12 rounded-full bg-[#07C160] flex items-center justify-center">
                  <svg class="w-7 h-7 text-white" viewBox="0 0 1024 1024" fill="currentColor">
                    <path d="M690.1 377.4c5.9 0 11.8 0.2 17.6 0.5-25.3-122.6-148.7-216.4-294.9-216.4-162.6 0-294.9 117.3-294.9 261.7 0 83.3 44.1 159.3 118 216.4l-29.5 88.7 103.1-51.6c36.8 7.3 66.3 14.7 103.1 14.7 9.3 0 18.4-0.4 27.5-1.1-5.8-19.6-9.1-40.1-9.1-61.4 0.1-138.7 118.1-251.5 259.1-251.5zM476.4 252.6c22.1 0 36.8 14.7 36.8 36.8 0 22.1-14.7 36.8-36.8 36.8-22.1 0-44.2-14.7-44.2-36.8 0-22.1 22.1-36.8 44.2-36.8zM254.7 326.2c-22.1 0-44.2-14.7-44.2-36.8 0-22.1 22.1-36.8 44.2-36.8 22.1 0 36.8 14.7 36.8 36.8 0 22.1-14.7 36.8-36.8 36.8zM906.1 628.8c0-122.6-118-222.1-235.9-222.1-132.8 0-235.9 99.5-235.9 222.1 0 122.8 103.1 222.1 235.9 222.1 29.5 0 59-7.3 88.5-14.7l81.2 44.2-22.1-73.8C876.7 762.4 906.1 699.6 906.1 628.8zM611.3 592c-14.7 0-29.5-14.7-29.5-29.5 0-14.7 14.7-29.5 29.5-29.5 22.1 0 36.8 14.7 36.8 29.5 0 14.8-14.7 29.5-36.8 29.5zM788.7 592c-14.7 0-29.5-14.7-29.5-29.5 0-14.7 14.7-29.5 29.5-29.5 22.1 0 36.8 14.7 36.8 29.5 0 14.8-14.7 29.5-36.8 29.5z"/>
                  </svg>
                </div>
                <span class="text-xs text-on-surface-variant">微信</span>
              </button>
              
              <button @click="shareToQQ" class="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-surface-container-high transition-colors active:scale-95">
                <div class="w-12 h-12 rounded-full bg-[#12B7F5] flex items-center justify-center">
                  <svg class="w-7 h-7 text-white" viewBox="0 0 1024 1024" fill="currentColor">
                    <path d="M824.8 613.2c-16-51.4-34.4-94.6-62.7-165.3C766.5 262.2 689.3 112 511.5 112 331.7 112 256.2 265.2 261 447.9c-28.4 70.8-46.7 113.7-62.7 165.3-34 109.5-23 154.8-14.6 155.8 18 2.2 70.1-82.4 70.1-82.4 0 49 25.2 112.9 79.8 159-26.4 8.1-85.7 29.9-71.6 53.8 11.4 19.3 196.2 12.3 249.5 6.3 53.3 6 238.1 13 249.5-6.3 14.1-23.8-45.2-45.7-71.6-53.8 54.6-46.2 79.8-110.1 79.8-159 0 0 52.1 84.6 70.1 82.4 8.5-1.1 19.5-46.4-14.5-155.8z"/>
                  </svg>
                </div>
                <span class="text-xs text-on-surface-variant">QQ</span>
              </button>
              
              <button @click="shareToWeibo" class="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-surface-container-high transition-colors active:scale-95">
                <div class="w-12 h-12 rounded-full bg-[#E6162D] flex items-center justify-center">
                  <span class="material-symbols-outlined text-white text-2xl">public</span>
                </div>
                <span class="text-xs text-on-surface-variant">微博</span>
              </button>
              
              <button @click="copyLink" class="flex flex-col items-center gap-2 p-3 rounded-xl hover:bg-surface-container-high transition-colors active:scale-95">
                <div class="w-12 h-12 rounded-full bg-surface-container-high flex items-center justify-center">
                  <span class="material-symbols-outlined text-on-surface-variant text-2xl">link</span>
                </div>
                <span class="text-xs text-on-surface-variant">复制链接</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
@keyframes slide-up {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.animate-slide-up {
  animation: slide-up 0.3s ease-out;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
