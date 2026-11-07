<script setup lang="ts">
import { ref, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import type { HealthPlan } from '@/types'

const props = defineProps<{
  tasks: HealthPlan[]
}>()

const emit = defineEmits<{
  update: [tasks: HealthPlan[]]
}>()

const userStore = useUserStore()
const { getPetById } = storeToRefs(userStore)

const showStandards = ref(false)

const toggleTask = (task: HealthPlan) => {
  task.isActive = task.isActive === 1 ? 0 : 1
  emit('update', props.tasks)
}

const getPetName = (petId: string) => {
  const pet = getPetById.value(petId)
  return pet?.name || ''
}

const getPetAvatar = (petId: string) => {
  const pet = getPetById.value(petId)
  return pet?.avatar || ''
}

const getIconConfig = (type: string) => {
  switch (type) {
    case 'daily':
      return { icon: 'restaurant', bg: 'bg-primary-fixed', text: 'text-primary' }
    case 'activity':
      return { icon: 'pets', bg: 'bg-secondary-fixed', text: 'text-secondary' }
    case 'medical':
      return { icon: 'medication', bg: 'bg-surface-container-high', text: 'text-tertiary' }
    default:
      return { icon: 'task_alt', bg: 'bg-surface-variant', text: 'text-on-surface-variant' }
  }
}

const getStandardColor = (standard: string) => {
  switch (standard) {
    case 'steps': return 'bg-blue-50 text-blue-600'
    case 'calories': return 'bg-orange-50 text-orange-600'
    case 'exercise': return 'bg-emerald-50 text-emerald-600'
    case 'sleep': return 'bg-purple-50 text-purple-600'
    case 'heartRate': return 'bg-rose-50 text-rose-600'
    default: return 'bg-surface-container text-on-surface-variant'
  }
}

const getStandardIcon = (standard: string) => {
  switch (standard) {
    case 'steps': return 'directions_walk'
    case 'calories': return 'local_fire_department'
    case 'exercise': return 'fitness_center'
    case 'sleep': return 'bedtime'
    case 'heartRate': return 'ecg_heart'
    default: return 'check_circle'
  }
}

const getStandardLabel = (standard: string) => {
  switch (standard) {
    case 'steps': return '步数'
    case 'calories': return '消耗'
    case 'exercise': return '运动'
    case 'sleep': return '睡眠'
    case 'heartRate': return '心率'
    default: return '完成'
  }
}
</script>

<template>
  <section class="space-y-md">
    <div class="flex items-center justify-between px-1">
      <h3 class="text-on-surface font-title-sm text-title-sm">今日任务</h3>
      <button 
        @click="showStandards = !showStandards"
        class="text-xs text-primary font-label-bold flex items-center gap-1"
      >
        <span class="material-symbols-outlined text-sm">{{ showStandards ? 'visibility_off' : 'visibility' }}</span>
        {{ showStandards ? '隐藏标准' : '完成标准' }}
      </button>
    </div>
    <div class="space-y-sm">
      <div 
        v-for="task in tasks" 
        :key="task.id"
        class="flex items-center justify-between p-4 bg-white/50 dark:bg-surface-container/50 border border-surface-variant dark:border-surface-variant/50 rounded-xl group hover:border-primary/30 transition-all cursor-pointer active:scale-[0.98]"
        :class="{ 'opacity-60': task.isActive }"
      >
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 flex items-center justify-center rounded-xl" :class="getIconConfig(task.type).bg">
            <span class="material-symbols-outlined" :class="getIconConfig(task.type).text">{{ task.isActive ? 'check_circle' : getIconConfig(task.type).icon }}</span>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <p class="font-title-sm text-[16px]" :class="{ 'line-through': task.isActive }">{{ task.title }}</p>
              <div class="flex items-center gap-1 bg-surface-container rounded-full px-2 py-0.5">
                <div class="w-4 h-4 rounded-full overflow-hidden">
                  <img class="w-full h-full object-cover" :src="getPetAvatar(task.petId)" />
                </div>
                <span class="text-xs text-tertiary">{{ getPetName(task.petId) }}</span>
              </div>
            </div>
            <p class="text-tertiary font-caption-sm text-caption-sm">{{ task.time || '待定' }}{{ task.notes ? ' · ' + task.notes : '' }}</p>
            <div v-if="showStandards && task.standard" class="flex items-center gap-1 mt-1">
              <span class="material-symbols-outlined text-xs" :class="getStandardColor(task.standard).split(' ')[1]">
                {{ getStandardIcon(task.standard) }}
              </span>
              <span class="text-xs px-2 py-0.5 rounded-full" :class="getStandardColor(task.standard)">
                {{ getStandardLabel(task.standard) }}: {{ task.standardValue || '--' }}
              </span>
            </div>
          </div>
        </div>
        <button 
          @click.stop="toggleTask(task)"
          class="w-8 h-8 rounded-full border-2 transition-colors flex items-center justify-center"
          :class="task.isActive ? 'bg-primary border-primary' : 'border-primary/20 group-hover:border-primary'"
        >
          <span 
            class="material-symbols-outlined transition-transform"
            :class="task.isActive ? 'text-on-primary scale-100' : 'text-primary scale-0 group-hover:scale-100'"
          >
            check
          </span>
        </button>
      </div>
    </div>
  </section>
</template>
