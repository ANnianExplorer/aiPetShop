<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { useUserStore } from '@/stores/user'
import type { Reminder } from '@/types'

const router = useRouter()
const { showToast } = useToast()
const userStore = useUserStore()

const form = ref({
  title: '',
  date: '',
  time: '',
  location: '',
  type: 'daily' as Reminder['type'],
  repeat: 'none',
  notes: ''
})

const typeOptions = [
  { value: 'daily', label: '日常护理', icon: 'water_drop', color: 'bg-secondary-fixed text-secondary' },
  { value: 'medical', label: '医疗健康', icon: 'medical_services', color: 'bg-primary-fixed text-primary' },
  { value: 'activity', label: '运动训练', icon: 'pets', color: 'bg-tertiary-container text-tertiary' }
]

const repeatOptions = [
  { value: 'none', label: '不重复' },
  { value: 'daily', label: '每天' },
  { value: 'weekly', label: '每周' },
  { value: 'monthly', label: '每月' }
]

const goBack = () => {
  router.back()
}

const submitForm = () => {
  if (!form.value.title) {
    showToast('请输入提醒标题', 'warning')
    return
  }
  
  const newReminder: Reminder = {
    id: `r${Date.now()}`,
    petId: userStore.currentPet?.id || 'p1',
    title: form.value.title,
    time: form.value.time || form.value.date || '待定',
    location: form.value.location || '待定',
    type: form.value.type,
    isCompleted: false
  }
  
  showToast('提醒创建成功！', 'success')
  setTimeout(() => {
    router.back()
  }, 800)
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <div class="flex items-center justify-between py-md mb-md">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">新增提醒</span>
        <button @click="submitForm" class="active:scale-95 transition-transform px-4 py-2 bg-primary text-white rounded-full font-label-bold text-label-bold">
          保存
        </button>
      </div>
      <section class="space-y-md">
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">提醒标题 *</label>
          <input 
            v-model="form.title" 
            type="text" 
            placeholder="例如：年度疫苗接种" 
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">提醒类型</label>
          <div class="grid grid-cols-3 gap-sm">
            <button 
              v-for="option in typeOptions" 
              :key="option.value"
              @click="form.type = option.value as Reminder['type']"
              class="flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all"
              :class="form.type === option.value ? 'border-primary bg-primary-container' : 'border-surface-variant bg-surface-container'"
            >
              <span class="material-symbols-outlined" :class="option.color">{{ option.icon }}</span>
              <span class="font-label-bold text-xs">{{ option.label }}</span>
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-md">
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">日期</label>
            <input 
              v-model="form.date" 
              type="date" 
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">时间</label>
            <input 
              v-model="form.time" 
              type="time" 
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">地点</label>
          <div class="relative">
            <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">location_on</span>
            <input 
              v-model="form.location" 
              type="text" 
              placeholder="例如：宠物医院" 
              class="w-full bg-surface-container rounded-xl pl-10 pr-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">重复</label>
          <div class="flex gap-sm flex-wrap">
            <button 
              v-for="option in repeatOptions" 
              :key="option.value"
              @click="form.repeat = option.value"
              class="px-4 py-2 rounded-full font-label-bold transition-colors"
              :class="form.repeat === option.value ? 'bg-primary text-white' : 'bg-surface-container-high text-on-surface-variant'"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">备注</label>
          <textarea 
            v-model="form.notes" 
            rows="3" 
            placeholder="添加备注信息..." 
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          ></textarea>
        </div>
      </section>
    </main>
  </div>
</template>
