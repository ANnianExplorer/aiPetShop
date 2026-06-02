<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const route = useRoute()
const { showToast } = useToast()
const userStore = useUserStore()
const { pets, getPetById } = storeToRefs(userStore)

const petId = computed(() => Number(route.params.id))
const pet = computed(() => getPetById.value(petId.value))

const isEditing = ref(false)
const editForm = ref({
  name: '',
  breed: '',
  age: '',
  notes: '',
  avatar: ''
})

const avatarInput = ref<HTMLInputElement | null>(null)

const goBack = () => {
  router.back()
}

const startEdit = () => {
  if (!pet.value) return
  editForm.value = {
    name: pet.value.name,
    breed: pet.value.breed,
    age: pet.value.age,
    notes: pet.value.notes || '',
    avatar: pet.value.avatar
  }
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
}

const handleAvatarClick = () => {
  avatarInput.value?.click()
}

const handleFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files && input.files[0]) {
    const reader = new FileReader()
    reader.onload = (e) => {
      if (e.target?.result) {
        editForm.value.avatar = e.target.result as string
      }
    }
    reader.readAsDataURL(input.files[0])
  }
}

const saveEdit = () => {
  if (!editForm.value.name || !editForm.value.breed) {
    showToast('请填写完整信息', 'error')
    return
  }
  userStore.updatePet(petId.value, {
    name: editForm.value.name,
    breed: editForm.value.breed,
    age: editForm.value.age,
    notes: editForm.value.notes
  })
  showToast('保存成功', 'success')
  isEditing.value = false
}

const getHealthLevel = (score: number) => {
  if (score >= 90) return { text: '优秀', color: 'text-emerald-500', bg: 'bg-emerald-50' }
  if (score >= 70) return { text: '良好', color: 'text-blue-500', bg: 'bg-blue-50' }
  if (score >= 50) return { text: '一般', color: 'text-amber-500', bg: 'bg-amber-50' }
  return { text: '需关注', color: 'text-rose-500', bg: 'bg-rose-50' }
}

const healthLevel = computed(() => {
  if (!pet.value) return { text: '', color: '', bg: '' }
  return getHealthLevel(pet.value.healthScore)
})
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex items-center justify-between py-md mb-lg">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">宠物详情</span>
        <button @click="startEdit" class="text-primary font-label-bold text-label-bold">编辑</button>
      </div>

      <section v-if="pet" class="flex flex-col items-center mb-lg">
        <div class="w-32 h-32 rounded-full border-4 border-white shadow-xl overflow-hidden">
          <img class="w-full h-full object-cover" :src="pet.avatar" />
        </div>
        <h2 class="mt-4 font-display-lg text-display-lg text-on-surface">{{ pet.name }}</h2>
        <p class="text-tertiary">{{ pet.breed }} · {{ pet.age }}</p>
        <div class="mt-3 flex items-center gap-2" :class="healthLevel.bg">
          <span class="px-3 py-1 rounded-full text-sm font-label-bold" :class="healthLevel.color">
            健康评分 {{ pet.healthScore }} - {{ healthLevel.text }}
          </span>
        </div>
      </section>

      <section v-if="pet" class="grid grid-cols-4 gap-3 mb-lg">
        <div class="bg-surface-container-low rounded-xl p-3 text-center">
          <p class="text-xl font-display-lg text-on-surface">{{ pet.todaySteps }}</p>
          <p class="text-xs text-tertiary mt-1">今日步数</p>
        </div>
        <div class="bg-surface-container-low rounded-xl p-3 text-center">
          <p class="text-xl font-display-lg text-on-surface">{{ pet.feedingCount }}/{{ pet.feedingTotal }}</p>
          <p class="text-xs text-tertiary mt-1">今日喂食</p>
        </div>
        <div class="bg-surface-container-low rounded-xl p-3 text-center">
          <p class="text-xl font-display-lg text-on-surface">{{ pet.healthScore }}</p>
          <p class="text-xs text-tertiary mt-1">健康评分</p>
        </div>
        <div class="bg-surface-container-low rounded-xl p-3 text-center">
          <p class="text-xl font-display-lg text-on-surface">{{ pet.age }}</p>
          <p class="text-xs text-tertiary mt-1">年龄</p>
        </div>
      </section>

      <section v-if="pet" class="mb-lg">
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">基本信息</h3>
        <div class="bg-surface-container-low rounded-xl p-4 space-y-3">
          <div class="flex justify-between">
            <span class="text-sm text-on-surface-variant">类型</span>
            <span class="text-sm font-label-bold text-on-surface">{{ pet.type === 'dog' ? '狗狗' : pet.type === 'cat' ? '猫咪' : '其他' }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-on-surface-variant">品种</span>
            <span class="text-sm font-label-bold text-on-surface">{{ pet.breed }}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-sm text-on-surface-variant">年龄</span>
            <span class="text-sm font-label-bold text-on-surface">{{ pet.age }}</span>
          </div>
        </div>
      </section>

      <section v-if="pet" class="mb-lg">
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">喂食记录</h3>
        <div class="space-y-2">
          <div class="bg-surface-container-low rounded-xl p-4 flex justify-between items-center">
            <div>
              <p class="text-sm font-label-bold text-on-surface">今日已喂食 {{ pet.feedingCount }} 次</p>
              <p class="text-xs text-tertiary">计划 {{ pet.feedingTotal }} 次</p>
            </div>
            <span class="text-sm font-label-bold text-primary">{{ pet.feedingTotal > 0 ? Math.round(pet.feedingCount / pet.feedingTotal * 100) : 0 }}%</span>
          </div>
        </div>
      </section>

      <!-- Edit Modal -->
      <Teleport to="body">
        <Transition name="modal">
          <div v-if="isEditing" class="fixed inset-0 z-50 flex items-end justify-center">
            <div class="absolute inset-0 bg-black/30" @click="cancelEdit"></div>
            <div class="relative w-full max-w-lg bg-surface-container-low rounded-t-3xl overflow-hidden animate-slide-up">
              <div class="p-4 pb-6">
                <div class="flex justify-between items-center mb-4">
                  <h3 class="font-title-sm text-title-sm text-on-surface">编辑宠物信息</h3>
                  <button @click="cancelEdit" class="p-2 rounded-full hover:bg-surface-container-high transition-colors">
                    <span class="material-symbols-outlined text-on-surface-variant">close</span>
                  </button>
                </div>

                <div class="flex justify-center mb-4">
                  <div class="relative cursor-pointer" @click="handleAvatarClick">
                    <div class="w-24 h-24 rounded-full border-4 border-white shadow-xl overflow-hidden">
                      <img class="w-full h-full object-cover" :src="editForm.avatar || pet?.avatar" />
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
                </div>

                <div class="space-y-3">
                  <div>
                    <label class="font-label-bold text-label-bold text-on-surface mb-2 block">宠物名称</label>
                    <input 
                      v-model="editForm.name" 
                      placeholder="请输入宠物名称" 
                      class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
                    />
                  </div>
                  <div>
                    <label class="font-label-bold text-label-bold text-on-surface mb-2 block">品种</label>
                    <input 
                      v-model="editForm.breed" 
                      placeholder="请输入品种" 
                      class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
                    />
                  </div>
                  <div>
                    <label class="font-label-bold text-label-bold text-on-surface mb-2 block">年龄</label>
                    <input 
                      v-model="editForm.age" 
                      placeholder="例如：2岁" 
                      class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
                    />
                  </div>
                </div>

                <div class="flex gap-3 mt-6">
                  <button 
                    @click="cancelEdit" 
                    class="flex-1 py-3.5 bg-surface-container text-on-surface rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform"
                  >
                    取消
                  </button>
                  <button 
                    @click="saveEdit" 
                    class="flex-1 py-3.5 bg-primary text-on-primary rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform shadow-md"
                  >
                    保存
                  </button>
                </div>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>
    </main>
  </div>
</template>
