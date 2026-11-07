<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { notificationApi } from '@/api/notification'
import { useUserStore } from '@/stores/user'
import { formatDate } from '@/utils/format'
import type { Notification } from '@/types'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const notifications = ref<Notification[]>([])
const unreadCount = ref(0)
const selectedNotification = ref<Notification | null>(null)
const showDetail = ref(false)
const detailLoading = ref(false)

const fetchNotifications = async () => {
  try {
    const res = await notificationApi.listPage({ pageSize: 20 })
    notifications.value = res?.records || []
  } catch (e) {
    console.error('Failed to fetch notifications:', e)
  }
}

const fetchUnreadCount = async () => {
  try {
    unreadCount.value = await notificationApi.unreadCount() || 0
  } catch {}
}

onMounted(() => {
  fetchNotifications()
  fetchUnreadCount()
})

const openDetail = async (notification: Notification) => {
  if (notification.isRead === 0) {
    await notificationApi.markAsRead(notification.id)
    notification.isRead = 1
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    userStore.unreadNotifications = Math.max(0, userStore.unreadNotifications - 1)
  }
  detailLoading.value = true
  showDetail.value = true
  try {
    const detail = await notificationApi.getDetail(notification.id)
    selectedNotification.value = detail || notification
  } catch {
    selectedNotification.value = notification
  } finally {
    detailLoading.value = false
  }
}

const closeDetail = () => {
  showDetail.value = false
  selectedNotification.value = null
}

const markAllAsRead = async () => {
  await notificationApi.markAllAsRead()
  notifications.value.forEach(n => (n.isRead = 1))
  unreadCount.value = 0
  userStore.unreadNotifications = 0
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, string> = {
    reminder: 'notifications_active',
    social: 'group',
    health: 'monitor_heart',
    system: 'info',
    update: 'update',
    campaign: 'campaign',
    priority: 'priority_high',
  }
  return icons[type] || 'info'
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    reminder: 'bg-primary-fixed text-primary',
    social: 'bg-secondary-fixed text-secondary',
    health: 'bg-tertiary-container text-tertiary',
    system: 'bg-surface-container-high text-on-surface',
    update: 'bg-blue-100 text-blue-600',
    campaign: 'bg-purple-100 text-purple-600',
    priority: 'bg-red-100 text-red-600',
  }
  return colors[type] || 'bg-surface-container-high text-on-surface'
}

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    reminder: t('notification.reminder'),
    social: t('notification.social'),
    health: t('notification.health'),
    system: t('notification.system'),
    update: t('notification.update'),
    campaign: t('notification.activity'),
    priority: t('notification.urgent'),
  }
  return labels[type] || t('notification.notifications')
}

const goBack = () => router.back()
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4">
      <div class="px-container-padding max-w-screen-xl mx-auto">
        <!-- Header -->
        <div class="flex items-center justify-between py-md mb-md animate-float-up">
          <button @click="goBack" class="icon-btn p-2 rounded-full">
            <span class="material-symbols-outlined text-primary">arrow_back</span>
          </button>
          <span class="font-title-sm text-on-surface">{{ t('notification.notifications') }}</span>
          <button @click="markAllAsRead" class="text-primary font-label-bold text-label-bold px-3 py-1 rounded-full active:bg-primary-fixed transition-colors">
            {{ t('notification.markAllRead') }}
          </button>
        </div>

        <!-- Unread count -->
        <div v-if="unreadCount > 0" class="mb-md animate-float-up stagger-1">
          <span class="px-3 py-1 bg-primary/10 text-primary text-xs font-label-bold rounded-full">
            {{ t('notification.unreadCount', { count: unreadCount }) }}
          </span>
        </div>

        <!-- Notification List -->
        <div class="space-y-3 animate-float-up stagger-2">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            @click="openDetail(notification)"
            class="glass-card p-4 rounded-2xl flex items-start gap-4 cursor-pointer ripple-card"
            :class="{ 'opacity-60': notification.isRead === 1 }"
          >
            <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" :class="getTypeColor(notification.type)">
              <span class="material-symbols-outlined text-xl">{{ getTypeIcon(notification.type) }}</span>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-2">
                <h3 class="text-sm font-semibold truncate" :class="{ 'font-bold text-on-surface': notification.isRead === 0, 'text-on-surface-variant': notification.isRead === 1 }">
                  {{ notification.title }}
                </h3>
                <span v-if="notification.isRead === 0" class="w-2 h-2 bg-primary rounded-full flex-shrink-0 animate-pulse-glow"></span>
              </div>
              <p class="text-xs text-on-surface-variant mt-1 line-clamp-2">{{ notification.content }}</p>
              <p class="text-[11px] text-on-surface-variant/50 mt-2">{{ formatDate(notification.createTime) }}</p>
            </div>
          </div>
        </div>

        <!-- Empty -->
        <div v-if="notifications.length === 0" class="flex flex-col items-center justify-center py-20 animate-fade-in">
          <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">notifications_none</span>
          <p class="mt-4 font-title-md text-on-surface-variant">{{ t('notification.noNotifications') }}</p>
        </div>
      </div>
    </main>

    <!-- Detail Modal -->
    <Teleport to="body">
      <Transition name="slide-up">
        <div v-if="showDetail" class="fixed inset-0 z-50 flex items-end justify-center">
          <div class="absolute inset-0 bg-black/30" @click="closeDetail"></div>
          <div class="relative w-full max-w-lg bg-surface-container-low rounded-t-3xl overflow-hidden animate-slide-up max-h-[80vh]">
            <div class="p-5 pb-8">
              <!-- Drag handle -->
              <div class="flex justify-center mb-4">
                <div class="w-10 h-1 rounded-full bg-surface-variant"></div>
              </div>

              <!-- Loading -->
              <div v-if="detailLoading" class="flex justify-center py-10">
                <div class="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
              </div>

              <!-- Detail Content -->
              <template v-else-if="selectedNotification">
                <!-- Type badge + time -->
                <div class="flex items-center gap-3 mb-4">
                  <span class="px-3 py-1 rounded-full text-xs font-label-bold" :class="getTypeColor(selectedNotification.type)">
                    {{ getTypeLabel(selectedNotification.type) }}
                  </span>
                  <span class="text-xs text-on-surface-variant">{{ formatDate(selectedNotification.createTime) }}</span>
                </div>

                <!-- Title -->
                <h2 class="font-title-sm text-title-sm text-on-surface mb-4">{{ selectedNotification.title }}</h2>

                <!-- Content -->
                <div class="bg-surface-container rounded-2xl p-5 mb-6">
                  <p class="text-sm text-on-surface-variant leading-relaxed whitespace-pre-wrap">{{ selectedNotification.content }}</p>
                </div>

                <!-- Actions -->
                <button @click="closeDetail" class="w-full py-3 bg-primary text-on-primary rounded-2xl font-label-bold text-label-bold btn-jelly shadow-md">
                  {{ t('notification.gotIt') }}
                </button>
              </template>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
}
</style>
