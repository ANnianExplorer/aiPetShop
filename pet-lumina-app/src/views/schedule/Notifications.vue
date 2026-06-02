<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { notificationApi } from '@/api/notification'
import type { Notification } from '@/types'

const router = useRouter()

const notifications = ref<Notification[]>([])
const unreadCount = ref(0)

const fetchNotifications = async () => {
  try {
    const res = await notificationApi.listPage({ pageSize: 20 }) as any
    notifications.value = res?.records || []
  } catch (e) {
    console.error('Failed to fetch notifications:', e)
  }
}

const fetchUnreadCount = async () => {
  try {
    unreadCount.value = await notificationApi.unreadCount() as any
  } catch (e) {
    console.error('Failed to fetch unread count:', e)
  }
}

onMounted(() => {
  fetchNotifications()
  fetchUnreadCount()
})

const markAsRead = async (notification: Notification) => {
  await notificationApi.markAsRead(notification.id)
  notification.isRead = 1
  unreadCount.value = Math.max(0, unreadCount.value - 1)
}

const markAllAsRead = async () => {
  await notificationApi.markAllAsRead()
  notifications.value.forEach(n => (n.isRead = 1))
  unreadCount.value = 0
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, string> = {
    reminder: 'notifications_active',
    social: 'group',
    health: 'monitor_heart',
    system: 'info'
  }
  return icons[type] || 'info'
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    reminder: 'bg-primary-fixed text-primary',
    social: 'bg-secondary-fixed text-secondary',
    health: 'bg-tertiary-container text-tertiary',
    system: 'bg-surface-container-high text-on-surface'
  }
  return colors[type] || 'bg-surface-container-high text-on-surface'
}

const goBack = () => {
  router.back()
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
          <span class="font-title-sm text-on-surface">通知</span>
          <button @click="markAllAsRead" class="active:scale-95 transition-transform px-3 py-1 text-primary font-label-bold text-label-bold rounded-full hover:bg-primary-fixed">
            全部已读
          </button>
        </div>
        <div v-if="unreadCount > 0" class="py-md">
          <span class="font-label-bold text-label-bold text-on-surface-variant">{{ unreadCount }} 条未读通知</span>
        </div>

        <div class="space-y-md">
          <div 
            v-for="notification in notifications" 
            :key="notification.id"
            @click="markAsRead(notification)"
            class="glass-card bg-white/70 p-container-padding rounded-xl shadow-sm border border-white/40 flex items-start gap-4 cursor-pointer transition-all duration-200 active:scale-[0.98] hover:shadow-md"
            :class="{ 'opacity-70': notification.isRead === 1 }"
          >
            <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" :class="getTypeColor(notification.type)">
              <span class="material-symbols-outlined text-xl">{{ getTypeIcon(notification.type) }}</span>
            </div>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <h3 class="font-title-sm text-title-sm" :class="{ 'font-bold': notification.isRead === 0 }">{{ notification.title }}</h3>
                <span v-if="notification.isRead === 0" class="w-2 h-2 bg-primary rounded-full flex-shrink-0"></span>
              </div>
              <p class="font-body-sm text-body-sm text-on-surface-variant mt-1">{{ notification.content }}</p>
              <p class="font-caption-sm text-caption-sm text-on-surface-variant opacity-60 mt-2">{{ notification.createTime }}</p>
            </div>
          </div>
        </div>

        <div v-if="notifications.length === 0" class="flex flex-col items-center justify-center py-20">
          <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">notifications_none</span>
          <p class="mt-4 font-title-md text-on-surface-variant">暂无通知</p>
        </div>
      </div>
    </main>
  </div>
</template>
