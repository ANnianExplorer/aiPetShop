<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { Reminder } from '@/types'

const router = useRouter()

const props = defineProps<{
  reminders: Reminder[]
}>()

const toggleReminder = (reminder: Reminder) => {
  reminder.isCompleted = !reminder.isCompleted
}

const viewAllSchedules = () => {
  router.push({ name: 'scheduleList' })
}
</script>

<template>
  <section>
    <div class="flex justify-between items-end mb-md">
      <h2 class="font-headline-md text-headline-md">今日提醒</h2>
      <span @click="viewAllSchedules" class="font-label-bold text-label-bold text-primary cursor-pointer hover:opacity-80 transition-opacity">全部日程</span>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-card-gutter">
      <div 
        v-for="reminder in reminders" 
        :key="reminder.id"
        @click="toggleReminder(reminder)"
        class="glass-card bg-white/70 p-container-padding rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.03)] border border-white/40 flex items-center gap-4 cursor-pointer transition-all duration-200 active:scale-[0.98] hover:shadow-md"
        :class="{ 'opacity-60': reminder.isCompleted }"
      >
        <div 
          class="w-12 h-12 rounded-full flex items-center justify-center transition-all"
          :class="reminder.type === 'medical' ? 'bg-primary-fixed text-primary' : 'bg-secondary-fixed text-secondary'"
        >
          <span class="material-symbols-outlined">{{ reminder.isCompleted ? 'check_circle' : (reminder.type === 'medical' ? 'medical_services' : 'water_drop') }}</span>
        </div>
        <div class="flex-1">
          <h3 class="font-title-sm text-title-sm" :class="{ 'line-through': reminder.isCompleted }">{{ reminder.title }}</h3>
          <p class="font-caption-sm text-caption-sm text-on-surface-variant">{{ reminder.time }} · {{ reminder.location }}</p>
        </div>
        <div class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all" :class="reminder.isCompleted ? 'bg-primary border-primary' : 'border-surface-variant'">
          <span v-if="reminder.isCompleted" class="material-symbols-outlined text-white text-sm">check</span>
        </div>
      </div>
    </div>
  </section>
</template>
