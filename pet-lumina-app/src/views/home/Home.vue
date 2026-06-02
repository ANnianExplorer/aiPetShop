<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import TodayReminders from '@/components/home/TodayReminders.vue'
import PetStatusBento from '@/components/home/PetStatusBento.vue'
import CommunityTrends from '@/components/home/CommunityTrends.vue'
import { reminderApi } from '@/api/reminder'
import { postApi } from '@/api/post'
import type { Reminder, Post } from '@/types'

const router = useRouter()
const userStore = useUserStore()
const { currentUser, currentPet, tasks } = storeToRefs(userStore)

const reminders = ref<Reminder[]>([])
const trends = ref<Post[]>([])

const addNewReminder = () => {
  router.push({ name: 'addReminder' })
}

const goToProfile = () => {
  router.push({ name: 'profile' })
}

const goToNotifications = () => {
  router.push({ name: 'notifications' })
}

onMounted(async () => {
  // 获取今日提醒
  try {
    const today = new Date().toISOString().split('T')[0]
    const res = await reminderApi.listPage({ pageSize: 5, startDate: today }) as any
    reminders.value = res?.records || []
  } catch (e) {
    reminders.value = []
  }

  // 获取社区热门帖子
  try {
    const res = await postApi.listPage({ pageSize: 3 }) as any
    trends.value = res?.records || []
  } catch (e) {
    trends.value = []
  }
})
</script>

<template>
  <div class="pb-32">
    <!-- TopAppBar -->
    <header class="fixed top-0 w-full z-50 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-xl border-b border-zinc-100/50 dark:border-zinc-800/50 shadow-sm">
      <div class="flex justify-between items-center px-5 py-3 w-full max-w-screen-xl mx-auto">
        <div class="flex items-center gap-3">
          <div @click="goToProfile" class="w-10 h-10 rounded-full overflow-hidden border-2 border-primary-fixed cursor-pointer active:scale-95 transition-transform">
            <img class="w-full h-full object-cover" :src="currentUser?.avatar" alt="Avatar" />
          </div>
          <span class="text-xl font-bold tracking-tighter text-emerald-800 dark:text-emerald-100 font-['Plus_Jakarta_Sans']">PetLumina</span>
        </div>
        <div @click="goToNotifications" class="active:scale-95 transition-transform duration-200 cursor-pointer">
          <span class="material-symbols-outlined text-emerald-700 dark:text-emerald-400">notifications</span>
        </div>
      </div>
    </header>

    <main class="pt-20 px-container-padding space-y-lg max-w-screen-xl mx-auto">
      <!-- Welcome Section -->
      <section class="mt-4">
        <h1 class="font-display-lg text-display-lg text-on-background">你好, {{ currentUser?.nickname }}</h1>
        <p class="font-body-md text-body-md text-on-surface-variant opacity-70">今天也是充满活力的一天！</p>
      </section>

      <!-- Extracted Components -->
      <TodayReminders :reminders="reminders" />
      <PetStatusBento v-if="currentPet" :pet="currentPet" />
      <CommunityTrends :trends="trends" />
    </main>

    <!-- FAB -->
    <button @click="addNewReminder" class="fixed bottom-24 right-5 w-14 h-14 bg-primary text-on-primary rounded-full shadow-lg flex items-center justify-center z-40 active:scale-90 transition-transform">
      <span class="material-symbols-outlined text-3xl">add</span>
    </button>
  </div>
</template>
