<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useToast } from '@/composables/useToast'
import { healthApi } from '@/api/health'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const { showToast } = useToast()
const userStore = useUserStore()
const { currentPet } = storeToRefs(userStore)
const submitting = ref(false)

const planType = ref('')
const planTitle = ref('')
const planTime = ref('')
const planDescription = ref('')
const planFrequency = ref('daily')
const planStandard = ref('')
const planStandardValue = ref('')

const planTypes = [
  { id: 'feeding', name: '喂食计划', icon: 'restaurant' },
  { id: 'exercise', name: '运动计划', icon: 'directions_run' },
  { id: 'medical', name: '医疗计划', icon: 'local_hospital' },
  { id: 'grooming', name: '美容计划', icon: 'content_cut' },
  { id: 'training', name: '训练计划', icon: 'school' }
]

const frequencies = [
  { id: 'daily', name: '每天' },
  { id: 'weekly', name: '每周' },
  { id: 'monthly', name: '每月' }
]

const standards = [
  { id: 'steps', name: '步数', icon: 'directions_walk', unit: '步', placeholder: '例如：5000' },
  { id: 'calories', name: '消耗', icon: 'local_fire_department', unit: 'kcal', placeholder: '例如：320' },
  { id: 'exercise', name: '运动', icon: 'fitness_center', unit: '分钟', placeholder: '例如：30' },
  { id: 'sleep', name: '睡眠', icon: 'bedtime', unit: '小时', placeholder: '例如：8' },
  { id: 'heartRate', name: '心率', icon: 'ecg_heart', unit: 'bpm', placeholder: '例如：75' }
]

const selectPlanType = (type: string) => {
  planType.value = type
}

const selectStandard = (id: string) => {
  planStandard.value = id
  planStandardValue.value = ''
}

const goBack = () => {
  router.back()
}

const handleSubmit = async () => {
  const pet = currentPet.value
  if (!pet) {
    showToast('请先选择宠物', 'error')
    return
  }
  if (!planType.value || !planTitle.value || !planTime.value) {
    showToast('请填写完整信息', 'error')
    return
  }
  try {
    submitting.value = true
    await healthApi.addPlan({
      petId: pet.id,
      type: planType.value,
      title: planTitle.value,
      time: planTime.value,
      frequency: planFrequency.value,
      standard: planStandard.value || undefined,
      standardValue: planStandardValue.value ? Number(planStandardValue.value) : undefined,
      notes: planDescription.value || undefined
    })
    showToast('计划创建成功', 'success')
    setTimeout(() => {
      router.back()
    }, 1000)
  } catch (e) {
    showToast('创建失败，请重试', 'error')
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
        <span class="font-title-sm text-on-surface">新增计划</span>
        <div class="w-10"></div>
      </div>

      <section class="mb-lg">
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">计划类型</h3>
        <div class="grid grid-cols-5 gap-3">
          <button 
            v-for="type in planTypes" 
            :key="type.id"
            @click="selectPlanType(type.id)"
            class="flex flex-col items-center gap-2 p-3 rounded-xl transition-all active:scale-95"
            :class="planType === type.id ? 'bg-primary text-on-primary shadow-md' : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'"
          >
            <span class="material-symbols-outlined text-2xl">{{ type.icon }}</span>
            <span class="text-xs font-label-bold">{{ type.name }}</span>
          </button>
        </div>
      </section>

      <section class="space-y-4 mb-lg">
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">计划名称</label>
          <input 
            v-model="planTitle" 
            placeholder="例如：晨间喂食" 
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
          />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">计划时间</label>
          <input 
            v-model="planTime" 
            type="time" 
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
          />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">重复频率</label>
          <div class="flex gap-3">
            <button 
              v-for="freq in frequencies" 
              :key="freq.id"
              @click="planFrequency = freq.id"
              class="flex-1 py-2.5 rounded-xl font-label-bold text-sm transition-all active:scale-95"
              :class="planFrequency === freq.id ? 'bg-primary text-on-primary' : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'"
            >
              {{ freq.name }}
            </button>
          </div>
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">完成标准（关联周健康指标）</label>
          <div class="grid grid-cols-5 gap-3 mb-3">
            <button 
              v-for="standard in standards" 
              :key="standard.id"
              @click="selectStandard(standard.id)"
              class="flex flex-col items-center gap-1 p-2 rounded-xl transition-all active:scale-95"
              :class="planStandard === standard.id ? 'bg-primary text-on-primary shadow-md' : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'"
            >
              <span class="material-symbols-outlined text-xl">{{ standard.icon }}</span>
              <span class="text-xs font-label-bold">{{ standard.name }}</span>
            </button>
          </div>
          <div v-if="planStandard" class="flex gap-3">
            <input 
              v-model="planStandardValue" 
              type="number"
              :placeholder="standards.find(s => s.id === planStandard)?.placeholder"
              class="flex-1 bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
            />
            <div class="flex items-center px-4 bg-surface-container rounded-xl font-body-sm text-on-surface-variant">
              {{ standards.find(s => s.id === planStandard)?.unit }}
            </div>
          </div>
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">备注说明</label>
          <textarea 
            v-model="planDescription" 
            placeholder="添加备注信息..." 
            rows="3"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none" 
          ></textarea>
        </div>
      </section>

      <button
        @click="handleSubmit"
        :disabled="submitting"
        class="w-full py-3.5 bg-primary text-on-primary rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform shadow-md disabled:opacity-60"
      >
        {{ submitting ? '保存中...' : '保存计划' }}
      </button>
    </main>
  </div>
</template>
