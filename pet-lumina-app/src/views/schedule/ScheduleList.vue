<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import type { Reminder } from '@/types'
import { reminderApi } from '@/api/reminder'
import { isToday, isWithinNextDays } from '@/utils/schedule'

const { t } = useI18n()
const router = useRouter()

const filterTabs = computed(() => [
  { key: 'all', label: t('reminder.filterAll') },
  { key: 'today', label: t('reminder.filterToday') },
  { key: 'week', label: t('reminder.filterWeek') },
  { key: 'completed', label: t('reminder.filterCompleted') }
])
const activeTab = ref('all')

const reminders = ref<Reminder[]>([])

const fetchReminders = async () => {
  try {
    const res = await reminderApi.listPage({ pageSize: 50 }) as any
    reminders.value = res?.records ?? []
  } catch (e) {
    console.error('Failed to fetch reminders:', e)
  }
}

onMounted(() => {
  fetchReminders()
})

const filteredReminders = computed(() => {
  switch (activeTab.value) {
    case 'today':
      // 后端存的是 yyyy-MM-dd HH:mm:ss，按本地自然日比较（旧代码用 includes('今天')，永远为空）
      return reminders.value.filter(r => isToday(r.remindTime))
    case 'week':
      // 未来 7 天且未完成：左闭右开，今天的也算
      return reminders.value.filter(r => r.isCompleted === 0 && isWithinNextDays(r.remindTime, 7))
    case 'completed':
      return reminders.value.filter(r => r.isCompleted === 1)
    default:
      return reminders.value
  }
})

const toggleReminder = async (reminder: Reminder) => {
  try {
    await reminderApi.toggleComplete(reminder.id)
    reminder.isCompleted = reminder.isCompleted === 1 ? 0 : 1
  } catch (e) {
    console.error('Failed to toggle reminder:', e)
  }
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
          <span class="font-title-sm text-on-surface">{{ t('reminder.allSchedules') }}</span>
          <button @click="addNewReminder" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
            <span class="material-symbols-outlined text-emerald-700">add</span>
          </button>
        </div>
        <div class="flex gap-sm overflow-x-auto no-scrollbar py-md">
          <button
            v-for="tab in filterTabs"
            :key="tab.key"
            @click="activeTab = tab.key"
            class="px-4 py-2 rounded-full font-label-bold whitespace-nowrap transition-colors"
            :class="activeTab === tab.key ? 'bg-primary text-white' : 'bg-surface-container-high text-on-surface-variant hover:bg-primary-fixed'"
          >
            {{ tab.label }}
          </button>
        </div>

        <div class="space-y-md">
          <div
            v-for="reminder in filteredReminders"
            :key="reminder.id"
            @click="toggleReminder(reminder)"
            class="glass-card bg-white/70 dark:bg-surface-container/70 p-container-padding rounded-xl shadow-sm border border-white/40 dark:border-surface-variant/20 flex items-center gap-4 cursor-pointer transition-all duration-200 active:scale-[0.98] hover:shadow-md"
            :class="{ 'opacity-60': reminder.isCompleted === 1 }"
          >
            <div
              class="w-12 h-12 rounded-full flex items-center justify-center transition-all flex-shrink-0"
              :class="getTypeColor(reminder.type)"
            >
              <span class="material-symbols-outlined">{{ reminder.isCompleted === 1 ? 'check_circle' : getTypeIcon(reminder.type) }}</span>
            </div>
            <div class="flex-1">
              <h3 class="font-title-sm text-title-sm" :class="{ 'line-through': reminder.isCompleted === 1 }">{{ reminder.title }}</h3>
              <p class="font-caption-sm text-caption-sm text-on-surface-variant mt-1">{{ reminder.remindTime }}</p>
              <p class="font-caption-sm text-caption-sm text-on-surface-variant opacity-70">{{ reminder.location }}</p>
            </div>
            <div class="w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all flex-shrink-0" :class="reminder.isCompleted === 1 ? 'bg-primary border-primary' : 'border-surface-variant'">
              <span v-if="reminder.isCompleted === 1" class="material-symbols-outlined text-white text-sm">check</span>
            </div>
          </div>
        </div>

        <div v-if="filteredReminders.length === 0" class="flex flex-col items-center justify-center py-20">
          <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">event_available</span>
          <p class="mt-4 font-title-md text-on-surface-variant">{{ t('reminder.noSchedule') }}</p>
          <button @click="addNewReminder" class="mt-4 px-6 py-2 bg-primary text-on-primary rounded-full font-label-bold active:scale-95 transition-transform">
            {{ t('reminder.addReminder') }}
          </button>
        </div>
      </div>
    </main>
  </div>
</template>
