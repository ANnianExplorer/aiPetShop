<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { Reminder } from '@/types'

const router = useRouter()

const props = defineProps<{
  reminders: Reminder[]
}>()

const toggleReminder = (reminder: Reminder) => {
  reminder.isCompleted = reminder.isCompleted ? 0 : 1
}

const viewAllSchedules = () => {
  router.push({ name: 'scheduleList' })
}
</script>

<template>
  <section>
    <div class="flex justify-between items-end mb-md">
      <h2 class="font-headline-md text-headline-md">今日提醒</h2>
      <span @click="viewAllSchedules" class="font-label-bold text-label-bold text-primary cursor-pointer active:opacity-50 transition-opacity">全部日程</span>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-card-gutter">
      <div
        v-for="(reminder, index) in reminders"
        :key="reminder.id"
        @click="toggleReminder(reminder)"
        class="glass-card p-container-padding rounded-2xl flex items-center gap-4 cursor-pointer ripple-card anim-shadow-breathe"
        :class="{ 'opacity-60': reminder.isCompleted === 1 }"
        :style="{ animationDelay: `${index * -0.8}s` }"
      >
        <div
          class="w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shrink-0"
          :class="reminder.type === 'medical' ? 'bg-primary-fixed text-primary' : 'bg-secondary-fixed text-secondary'"
        >
          <span class="material-symbols-outlined" :class="{ 'anim-icon-pulse': !reminder.isCompleted }">
            {{ reminder.isCompleted === 1 ? 'check_circle' : (reminder.type === 'medical' ? 'medical_services' : 'water_drop') }}
          </span>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="font-title-sm text-title-sm truncate" :class="{ 'line-through': reminder.isCompleted === 1 }">{{ reminder.title }}</h3>
          <p class="font-caption-sm text-caption-sm text-on-surface-variant">{{ reminder.remindTime }} · {{ reminder.location }}</p>
        </div>
        <div class="w-7 h-7 rounded-full border-2 flex items-center justify-center transition-all duration-300 shrink-0 press-effect" :class="reminder.isCompleted === 1 ? 'bg-primary border-primary' : 'border-surface-variant'">
          <span v-if="reminder.isCompleted === 1" class="material-symbols-outlined text-white text-sm">check</span>
        </div>
      </div>
    </div>
  </section>
</template>
