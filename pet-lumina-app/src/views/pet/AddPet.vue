<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { useUserStore } from '@/stores/user'

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

const petTypes = [
  { id: 'dog', name: '狗狗', icon: 'pets' },
  { id: 'cat', name: '猫咪', icon: 'cat' },
  { id: 'other', name: '其他', icon: 'paw' }
]

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
        petAvatar.value = e.target.result as string
      }
    }
    reader.readAsDataURL(input.files[0])
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
      <div class="flex items-center justify-between py-md mb-lg">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">添加宠物</span>
        <div class="w-10"></div>
      </div>

      <section class="mb-lg flex flex-col items-center">
        <div class="relative group cursor-pointer" @click="handleAvatarClick">
          <div class="w-32 h-32 rounded-full border-4 border-white shadow-xl overflow-hidden bg-surface-container flex items-center justify-center">
            <img v-if="petAvatar" class="w-full h-full object-cover" :src="petAvatar" />
            <span v-else class="material-symbols-outlined text-6xl text-on-surface-variant">add_a_photo</span>
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
        <p class="mt-2 text-sm text-tertiary">点击上传宠物照片</p>
      </section>

      <section class="space-y-4 mb-lg">
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">宠物类型</label>
          <div class="grid grid-cols-3 gap-3">
            <button 
              v-for="type in petTypes" 
              :key="type.id"
              @click="selectPetType(type.id)"
              class="flex flex-col items-center gap-2 p-3 rounded-xl transition-all active:scale-95"
              :class="petType === type.id ? 'bg-primary text-on-primary shadow-md' : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'"
            >
              <span class="material-symbols-outlined text-2xl">{{ type.icon }}</span>
              <span class="text-xs font-label-bold">{{ type.name }}</span>
            </button>
          </div>
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">宠物名称</label>
          <input 
            v-model="petName" 
            placeholder="例如：豆豆" 
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
          />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">品种</label>
          <input 
            v-model="petBreed" 
            placeholder="例如：金毛寻回犬" 
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
          />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">年龄</label>
          <input 
            v-model="petAge" 
            placeholder="例如：2岁" 
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
          />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">备注说明</label>
          <textarea 
            v-model="petDescription" 
            placeholder="添加备注信息..." 
            rows="3"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none" 
          ></textarea>
        </div>
      </section>

      <button
        @click="handleSubmit"
        :disabled="submitting"
        class="w-full py-3.5 bg-primary text-on-primary rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform shadow-md disabled:opacity-50"
      >
        {{ submitting ? '保存中...' : '保存' }}
      </button>
    </main>
  </div>
</template>
