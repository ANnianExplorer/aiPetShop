<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import type { Reminder } from '@/types'

const router = useRouter()

const filterTabs = ['全部', '今日', '本周', '已完成']
const activeTab = ref('全部')

const reminders = ref<Reminder[]>([
  {
    id: 'r1',
    petId: 'p1',
    title: '年度疫苗接种',
    time: '下午 2:30',
    location: '宠物医院',
    type: 'medical',
    isCompleted: false
  },
  {
    id: 'r2',
    petId: 'p1',
    title: '定期体内驱虫',
    time: '今天之内完成',
    location: '在家',
    type: 'daily',
    isCompleted: false
  },
  {
    id: 'r3',
    petId: 'p1',
    title: '户外散步训练',
    time: '早上 8:00',
    location: '小区公园',
    type: 'activity',
    isCompleted: true
  },
  {
    id: 'r4',
    petId: 'p2',
    title: '洗澡美容',
    time: '明天 下午 3:00',
    location: '宠物美容店',
    type: 'daily',
    isCompleted: false
  },
  {
    id: 'r5',
    petId: 'p1',
    title: '体检预约',
    time: '下周一 上午 10:00',
    location: '宠物医院',
    type: 'medical',
    isCompleted: false
  },
  {
    id: 'r6',
    petId: 'p2',
    title: '更换猫砂',
    time: '每三天',
    location: '在家',
    type: 'daily',
    isCompleted: true
  }
])

const filteredReminders = computed(() => {
  switch (activeTab.value) {
    case '今日':
      return reminders.value.filter(r => r.time.includes('今天') || r.time.includes('上午') || r.time.includes('下午') || r.time.includes('早上'))
    case '本周':
      return reminders.value.filter(r => !r.isCompleted)
    case '已完成':
      return reminders.value.filter(r => r.isCompleted)
    default:
      return reminders.value
  }
})

const toggleReminder = (reminder: Reminder) => {
  reminder.isCompleted = !reminder.isCompleted
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, string> = {
    medical: 'medical_services',
    daily: 'water_drop',
    activity: 'pets'
  }
  return icons[type] || 'event'
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    medical: 'bg-primary-fixed text-primary',
    daily: 'bg-secondary-fixed text-secondary',
    activity: 'bg-tertiary-container text-tertiary'
  }
  return colors[type] || 'bg-surface-container-high text-on-surface'
}

const goBack = () => {
  router.back()
}

const addNewReminder = () => {
  router.push({ name: 'addReminder' })
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4">
      <div class="px-container-padding max-w-screen-xl mx-auto">
        <div class="flex items-center justify-between py-md mb-md">
          <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
            <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
          </button>
          <span class="font-title-sm text-on-surface">全部日程</span>
          <button @click="addNewReminder" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
            <span class="material-symbols-outlined text-emerald-700">add</span>
          </button>
        </div>
        <div class="flex gap-sm overflow-x-auto no-scrollbar py-md">
          <button 
            v-for="tab in filterTabs" 
            :key="tab"
            @click="activeTab = tab"
            class="px-4 py-2 rounded-full font-label-bold whitespace-nowrap transition-colors"
            :class="activeTab === tab ? 'bg-primary text-white' : 'bg-surface-container-high text-on-surface-variant hover:bg-primary-fixed'"
          >
            {{ tab }}
          </button>
        </div>

        <div class="space-y-md">
          <div 
            v-for="reminder in filteredReminders" 
            :key="reminder.id"
            @click="toggleReminder(reminder)"
            class="glass-card bg-white/70 p-container-padding rounded-xl shadow-sm border border-white/40 flex items-center gap-4 cursor-pointer transition-all duration-200 active:scale-[0.98] hover:shadow-md"
            :class="{ 'opacity-60': reminder.isCompleted }"
          >
            <div 
              class="w-12 h-12 rounded-full flex items-center justify-center transition-all flex-shrink-0"
              :class="getTypeColor(reminder.type)"
            >
              <span class="material-symbols-outlined">{{ reminder.isCompleted ? 'check_circle' : getTypeIcon(reminder.type) }}</span>
            </div>
            <div class="flex-1">
              <h3 class="font-title-sm text-title-sm" :class="{ 'line-through': reminder.isCompleted }">{{ reminder.title }}</h3>
              <p class="font-caption-sm text-caption-sm text-on-surface-variant mt-1">{{ reminder.time }}</p>
              <p class="font-caption-sm text-caption-sm text-on-surface-variant opacity-70">{{ reminder.location }}</p>
            </div>
            <div class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all flex-shrink-0" :class="reminder.isCompleted ? 'bg-primary border-primary' : 'border-surface-variant'">
              <span v-if="reminder.isCompleted" class="material-symbols-outlined text-white text-sm">check</span>
            </div>
          </div>
        </div>

        <div v-if="filteredReminders.length === 0" class="flex flex-col items-center justify-center py-20">
          <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">event_available</span>
          <p class="mt-4 font-title-md text-on-surface-variant">暂无日程</p>
          <button @click="addNewReminder" class="mt-4 px-6 py-2 bg-primary text-on-primary rounded-full font-label-bold active:scale-95 transition-transform">
            新增提醒
          </button>
        </div>
      </div>
    </main>
  </div>
</template>
