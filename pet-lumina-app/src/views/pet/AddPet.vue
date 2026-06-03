<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { useUserStore } from '@/stores/user'
import { fileApi } from '@/api/file'

const router = useRouter()
const { showToast } = useToast()
const userStore = useUserStore()
const submitting = ref(false)

const petName = ref('')
const petType = ref('')
const petBreed = ref('')
const petAge = ref('')
const petAvatar = ref('')
const petDescription = ref('')
const avatarUploading = ref(false)

const petTypes = [
  { id: 'dog', name: '狗狗', icon: 'pets' },
  { id: 'cat', name: '猫咪', icon: 'cat' },
  { id: 'other', name: '其他', icon: 'paw' }
]

const avatarInput = ref<HTMLInputElement | null>(null)

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
  // 先显示本地预览
  petAvatar.value = URL.createObjectURL(file)
  avatarUploading.value = true
  try {
    // 上传到 COS，拿到 URL
    const url = await fileApi.uploadImage(file, 'pet/image')
    petAvatar.value = url
    showToast('照片上传成功', 'success')
  } catch (e) {
    petAvatar.value = ''
    showToast('照片上传失败', 'error')
  } finally {
    avatarUploading.value = false
    input.value = ''
  }
}

const selectPetType = (type: string) => {
  petType.value = type
}

const goBack = () => {
  router.back()
}

const handleSubmit = async () => {
  if (!petName.value || !petType.value || !petBreed.value) {
    showToast('请填写完整信息', 'error')
    return
  }
  submitting.value = true
  try {
    await userStore.addPet({
      name: petName.value,
      type: petType.value,
      breed: petBreed.value,
      age: petAge.value || undefined,
      notes: petDescription.value || undefined,
      avatar: petAvatar.value || undefined,
    })
    showToast('宠物添加成功', 'success')
    setTimeout(() => {
      router.back()
    }, 800)
  } catch (e) {
    showToast('添加失败，请重试', 'error')
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex items-center justify-between py-md mb-lg animate-float-up">
        <button @click="goBack" class="icon-btn p-2 rounded-full">
          <span class="material-symbols-outlined text-primary">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">添加宠物</span>
        <div class="w-10"></div>
      </div>

      <!-- Avatar Upload -->
      <section class="mb-lg flex flex-col items-center animate-float-up stagger-1">
        <input
          ref="avatarInput"
          type="file"
          accept="image/jpeg,image/png,image/gif,image/webp"
          class="hidden"
          @change="handleFileChange"
        />
        <div class="relative group cursor-pointer" @click="handleAvatarClick">
          <div class="w-32 h-32 rounded-full border-4 border-white shadow-xl overflow-hidden bg-surface-container flex items-center justify-center">
            <img v-if="petAvatar" class="w-full h-full object-cover" :src="petAvatar" />
            <span v-else class="material-symbols-outlined text-6xl text-on-surface-variant">add_a_photo</span>
          </div>
          <div class="absolute bottom-0 right-0 bg-primary p-1.5 rounded-full text-white shadow-md">
            <span class="material-symbols-outlined text-[16px]">{{ avatarUploading ? 'hourglass_top' : 'edit' }}</span>
          </div>
        </div>
        <p class="mt-2 text-sm text-tertiary">{{ avatarUploading ? '上传中...' : '点击上传宠物照片' }}</p>
      </section>

      <!-- Form -->
      <section class="space-y-4 mb-lg animate-float-up stagger-2">
        <!-- Pet Type -->
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">宠物类型</label>
          <div class="grid grid-cols-3 gap-3">
            <button
              v-for="type in petTypes"
              :key="type.id"
              @click="selectPetType(type.id)"
              class="flex flex-col items-center gap-2 p-3 rounded-xl transition-all btn-jelly"
              :class="petType === type.id ? 'bg-primary text-on-primary shadow-md' : 'glass-card text-on-surface-variant'"
            >
              <span class="material-symbols-outlined text-2xl">{{ type.icon }}</span>
              <span class="text-xs font-label-bold">{{ type.name }}</span>
            </button>
          </div>
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">宠物名称</label>
          <input v-model="petName" placeholder="例如：豆豆"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">品种</label>
          <input v-model="petBreed" placeholder="例如：金毛寻回犬"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">年龄</label>
          <input v-model="petAge" placeholder="例如：2岁"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">备注说明</label>
          <textarea v-model="petDescription" placeholder="添加备注信息..." rows="3"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none"></textarea>
        </div>
      </section>

      <button
        @click="handleSubmit"
        :disabled="submitting || avatarUploading"
        class="w-full py-3.5 bg-primary text-on-primary rounded-xl font-label-bold text-label-bold btn-jelly shadow-md disabled:opacity-50 animate-float-up stagger-3"
      >
        {{ submitting ? '保存中...' : '保存' }}
      </button>
    </main>
  </div>
</template>
