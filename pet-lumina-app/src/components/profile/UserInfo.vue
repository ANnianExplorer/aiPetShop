<script setup lang="ts">
import { ref } from 'vue'
import type { User } from '@/types'
import { useToast } from '@/composables/useToast'
import { userApi } from '@/api/user'

const props = defineProps<{
  user: User
}>()

const emit = defineEmits<{
  updateAvatar: [avatar: string]
}>()

const { showToast } = useToast()
const avatarInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)

const handleAvatarClick = () => {
  avatarInput.value?.click()
}

const handleFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) {
    showToast('图片大小不能超过5MB', 'error')
    input.value = ''
    return
  }

  uploading.value = true
  try {
    // 调用后端 /user/update/avatar，同时上传 COS + 更新数据库
    const url = await userApi.updateAvatar(file) as unknown as string
    emit('updateAvatar', url)
    showToast('头像更新成功', 'success')
  } catch (e) {
    showToast('头像上传失败', 'error')
  } finally {
    uploading.value = false
    input.value = ''
  }
}
</script>

<template>
  <section class="mt-8 flex flex-col items-center text-center">
    <div class="relative group cursor-pointer" @click="handleAvatarClick">
      <div class="w-24 h-24 rounded-full border-4 border-white dark:border-surface-container shadow-xl overflow-hidden">
        <img class="w-full h-full object-cover" :src="user.avatar" />
      </div>
      <div class="absolute bottom-0 right-0 bg-primary p-1.5 rounded-full text-white shadow-md transition-transform group-active:scale-90">
        <span class="material-symbols-outlined text-[16px]">{{ uploading ? 'hourglass_top' : 'edit' }}</span>
      </div>
    </div>
    <input
      ref="avatarInput"
      type="file"
      accept="image/jpeg,image/png,image/gif,image/webp"
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
