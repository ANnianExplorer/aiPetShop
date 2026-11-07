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
    const url = await userApi.updateAvatar(file)
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
    <p v-if="user.bio" class="mt-2 font-body-md text-caption-sm text-outline max-w-xs">{{ user.bio }}</p>
    <p v-else class="mt-2 font-body-md text-caption-sm text-outline max-w-xs">还没有填写个人简介</p>
  </section>
</template>
