<script setup lang="ts">
import { ref } from 'vue'
import type { User } from '@/types'

const props = defineProps<{
  user: User
}>()

const emit = defineEmits<{
  updateAvatar: [avatar: string]
}>()

const avatarInput = ref<HTMLInputElement | null>(null)

const handleAvatarClick = () => {
  avatarInput.value?.click()
}

const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        emit('updateAvatar', e.target.result as string)
      }
    }
    reader.readAsDataURL(input.files[0])
  }
}
</script>

<template>
  <section class="mt-8 flex flex-col items-center text-center">
    <div class="relative group cursor-pointer" @click="handleAvatarClick">
      <div class="w-24 h-24 rounded-full border-4 border-white shadow-xl overflow-hidden">
        <img class="w-full h-full object-cover" :src="user.avatar" />
      </div>
      <div class="absolute bottom-0 right-0 bg-primary p-1.5 rounded-full text-white shadow-md">
        <span class="material-symbols-outlined text-[16px]">edit</span>
      </div>
    </div>
    <input 
      ref="avatarInput"
      type="file" 
      accept="image/*" 
      class="hidden" 
      @change="handleFileChange" 
    />
    <h1 class="mt-4 font-display-lg text-display-lg text-on-surface">{{ user.nickname }}</h1>
    <p class="mt-2 font-body-md text-caption-sm text-outline max-w-xs">热爱自然的摄影师，也是两只调皮猫咪的"全职管家"。致力于分享最有温度的养宠生活。</p>
    
    <!-- Stats Chips -->
    <div class="mt-6 flex justify-center gap-4">
      <div class="bg-surface-container-low px-4 py-2 rounded-full flex flex-col items-center min-w-[80px]">
        <span class="font-label-bold text-label-bold text-primary">128</span>
        <span class="text-[10px] font-medium text-outline">动态</span>
      </div>
      <div class="bg-surface-container-low px-4 py-2 rounded-full flex flex-col items-center min-w-[80px]">
        <span class="font-label-bold text-label-bold text-primary">1.2k</span>
        <span class="text-[10px] font-medium text-outline">关注者</span>
      </div>
      <div class="bg-surface-container-low px-4 py-2 rounded-full flex flex-col items-center min-w-[80px]">
        <span class="font-label-bold text-label-bold text-primary">856</span>
        <span class="text-[10px] font-medium text-outline">获赞</span>
      </div>
    </div>
  </section>
</template>
