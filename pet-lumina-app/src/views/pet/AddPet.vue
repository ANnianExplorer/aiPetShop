<script setup lang="ts">
import { ref, computed } from 'vue'
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
const petNotes = ref('')
const avatarUploading = ref(false)

const petTypes = [
  { id: 'dog', name: '狗狗', icon: 'pets' },
  { id: 'cat', name: '猫咪', icon: 'cat' },
  { id: 'other', name: '其他', icon: 'paw' }
]

const typeLabel = computed(() => petTypes.find(t => t.id === petType.value)?.name || '未选择')

const avatarInput = ref<HTMLInputElement | null>(null)
const handleAvatarClick = () => { avatarInput.value?.click() }

const handleFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { showToast('图片大小不能超过5MB', 'error'); input.value = ''; return }
  petAvatar.value = URL.createObjectURL(file)
  avatarUploading.value = true
  try {
    petAvatar.value = await fileApi.uploadImage(file, 'pet/image')
    showToast('照片上传成功', 'success')
  } catch { petAvatar.value = ''; showToast('照片上传失败', 'error') } finally { avatarUploading.value = false; input.value = '' }
}

const selectPetType = (type: string) => { petType.value = type }
const goBack = () => router.back()

const handleSubmit = async () => {
  if (!petName.value || !petType.value || !petBreed.value) { showToast('请填写完整信息', 'error'); return }
  submitting.value = true
  try {
    await userStore.addPet({
      name: petName.value, type: petType.value, breed: petBreed.value,
      age: petAge.value || undefined, notes: petNotes.value || undefined, avatar: petAvatar.value || undefined,
    })
    showToast('宠物添加成功', 'success')
    setTimeout(() => router.back(), 800)
  } catch { showToast('添加失败，请重试', 'error') } finally { submitting.value = false }
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between py-md mb-lg animate-float-up">
        <button @click="goBack" class="icon-btn p-2 rounded-full">
          <span class="material-symbols-outlined text-primary">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">添加宠物</span>
        <div class="w-10"></div>
      </div>

      <!-- Preview Card -->
      <div class="glass-card rounded-2xl overflow-hidden mb-lg animate-float-up stagger-1">
        <div class="h-36 relative overflow-hidden">
          <img v-if="petAvatar" :src="petAvatar" class="w-full h-full object-cover" />
          <div v-else class="w-full h-full bg-gradient-to-br from-primary-container/30 to-primary/10 flex items-center justify-center">
            <span class="material-symbols-outlined text-white/30" style="font-size: 60px">pets</span>
          </div>
          <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
          <div class="absolute bottom-3 left-4 text-white">
            <h3 class="font-display-lg text-lg drop-shadow-lg">{{ petName || '宠物名称' }}</h3>
            <p class="text-white/80 text-xs">{{ petBreed || '品种' }} · {{ typeLabel }}</p>
          </div>
        </div>
      </div>

      <!-- Avatar Upload -->
      <section class="mb-lg flex flex-col items-center animate-float-up stagger-2">
        <input ref="avatarInput" type="file" accept="image/jpeg,image/png,image/gif,image/webp" class="hidden" @change="handleFileChange" />
        <div class="relative group cursor-pointer" @click="handleAvatarClick">
          <div class="w-28 h-28 rounded-full border-4 border-white shadow-xl overflow-hidden bg-surface-container flex items-center justify-center">
            <img v-if="petAvatar" class="w-full h-full object-cover" :src="petAvatar" />
            <span v-else class="material-symbols-outlined text-5xl text-on-surface-variant">add_a_photo</span>
          </div>
          <div class="absolute bottom-0 right-0 bg-primary p-1.5 rounded-full text-white shadow-md">
            <span class="material-symbols-outlined text-[16px]">{{ avatarUploading ? 'hourglass_top' : 'edit' }}</span>
          </div>
        </div>
        <p class="mt-2 text-sm text-tertiary">{{ avatarUploading ? '上传中...' : '点击上传宠物照片' }}</p>
      </section>

      <!-- Pet Type -->
      <section class="mb-lg animate-float-up stagger-3">
        <div class="flex items-center gap-2 mb-3">
          <span class="material-symbols-outlined text-primary text-lg">category</span>
          <label class="font-label-bold text-label-bold text-on-surface">宠物类型 *</label>
        </div>
        <div class="grid grid-cols-3 gap-3">
          <button v-for="type in petTypes" :key="type.id" @click="selectPetType(type.id)"
            class="flex flex-col items-center gap-2 p-4 rounded-2xl transition-all btn-jelly"
            :class="petType === type.id ? 'bg-primary text-on-primary shadow-md' : 'glass-card text-on-surface-variant'">
            <span class="material-symbols-outlined text-2xl">{{ type.icon }}</span>
            <span class="text-xs font-label-bold">{{ type.name }}</span>
          </button>
        </div>
      </section>

      <!-- Basic Info -->
      <section class="mb-lg animate-float-up stagger-4">
        <div class="flex items-center gap-2 mb-3">
          <span class="material-symbols-outlined text-primary text-lg">pets</span>
          <label class="font-label-bold text-label-bold text-on-surface">基本信息</label>
        </div>
        <div class="space-y-4">
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">宠物名称 *</label>
            <input v-model="petName" placeholder="例如：豆豆" class="w-full glass-input rounded-xl px-4 py-3 font-body-sm text-on-surface" />
          </div>
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">品种 *</label>
            <input v-model="petBreed" placeholder="例如：金毛寻回犬" class="w-full glass-input rounded-xl px-4 py-3 font-body-sm text-on-surface" />
          </div>
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">年龄</label>
            <input v-model="petAge" placeholder="例如：2岁" class="w-full glass-input rounded-xl px-4 py-3 font-body-sm text-on-surface" />
          </div>
        </div>
      </section>

      <!-- Health Notes -->
      <section class="mb-lg animate-float-up stagger-5">
        <div class="flex items-center gap-2 mb-3">
          <span class="material-symbols-outlined text-primary text-lg">medical_information</span>
          <label class="font-label-bold text-label-bold text-on-surface">健康档案</label>
        </div>
        <textarea v-model="petNotes" placeholder="描述过敏、近期疫苗接种、特殊护理需求..." rows="3"
          class="w-full glass-input rounded-xl px-4 py-3 font-body-sm text-on-surface resize-none"></textarea>
      </section>

      <!-- Submit -->
      <button @click="handleSubmit" :disabled="submitting || avatarUploading"
        class="w-full py-3.5 bg-primary text-on-primary rounded-2xl font-label-bold text-label-bold btn-jelly shadow-md disabled:opacity-50 animate-float-up stagger-6">
        {{ submitting ? '保存中...' : '保存' }}
      </button>
    </main>
  </div>
</template>
