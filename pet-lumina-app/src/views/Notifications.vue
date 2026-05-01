<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const notifications = ref([
  {
    id: 'n1',
    title: '疫苗接种提醒',
    message: '您的宠物年度疫苗接种将在明天下午2:30进行，请准时到达宠物医院。',
    time: '10分钟前',
    type: 'reminder',
    isRead: false
  },
  {
    id: 'n2',
    title: '社区互动',
    message: '林间猫影 点赞了您的帖子',
    time: '1小时前',
    type: 'social',
    isRead: false
  },
  {
    id: 'n3',
    title: '健康报告',
    message: '您宠物的周健康报告已生成，健康评分95分，状态优秀！',
    time: '3小时前',
    type: 'health',
    isRead: true
  },
  {
    id: 'n4',
    title: '系统通知',
    message: 'PetLumina 已更新至最新版本，新增多项实用功能。',
    time: '昨天',
    type: 'system',
    isRead: true
  },
  {
    id: 'n5',
    title: '社区互动',
    message: '德牧小伍 评论了您的帖子："太可爱了！"',
    time: '昨天',
    type: 'social',
    isRead: true
  }
])

const unreadCount = notifications.value.filter(n => !n.isRead).length

const markAsRead = (notification: typeof notifications.value[0]) => {
  notification.isRead = true
}

const markAllAsRead = () => {
  notifications.value.forEach(n => n.isRead = true)
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
            :class="{ 'opacity-70': notification.isRead }"
          >
            <div class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0" :class="getTypeColor(notification.type)">
              <span class="material-symbols-outlined text-xl">{{ getTypeIcon(notification.type) }}</span>
            </div>
            <div class="flex-1">
              <div class="flex items-center justify-between">
                <h3 class="font-title-sm text-title-sm" :class="{ 'font-bold': !notification.isRead }">{{ notification.title }}</h3>
                <span v-if="!notification.isRead" class="w-2 h-2 bg-primary rounded-full flex-shrink-0"></span>
              </div>
              <p class="font-body-sm text-body-sm text-on-surface-variant mt-1">{{ notification.message }}</p>
              <p class="font-caption-sm text-caption-sm text-on-surface-variant opacity-60 mt-2">{{ notification.time }}</p>
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
