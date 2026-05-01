<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import TodayReminders from '@/components/home/TodayReminders.vue'
import PetStatusBento from '@/components/home/PetStatusBento.vue'
import CommunityTrends from '@/components/home/CommunityTrends.vue'
import type { Reminder, Post } from '@/types'

const router = useRouter()
const userStore = useUserStore()
const { currentUser, currentPet } = storeToRefs(userStore)

const addNewReminder = () => {
  router.push({ name: 'addReminder' })
}

const goToProfile = () => {
  router.push({ name: 'profile' })
}

const goToNotifications = () => {
  router.push({ name: 'notifications' })
}

// Mock Data
const reminders = ref<Reminder[]>([
  {
    id: 'r1',
    title: '年度疫苗接种',
    time: '下午 2:30',
    location: '宠物医院',
    type: 'medical',
    isCompleted: false
  },
  {
    id: 'r2',
    title: '定期体内驱虫',
    time: '今天之内完成',
    location: '在家',
    type: 'daily',
    isCompleted: false
  }
])

const trends = ref<Post[]>([
  {
    id: 't1',
    author: {
      id: 'u2',
      name: '蓝天',
      avatar: 'https://lh3.googleusercontent.com/aida-public/AB6AXuA4LqvOOdWjtzV8kaGyXTNLTNKMASDlXhrEDexZimV4ban-OX3CSeDdHXyoFDPzve7JY32mq0xQZ10siLoOY-KDDHZKam_bWTnXG64uuBbNveFUnuygnwoBu2hjNaXjWV_K6QWje0ugMW_7OLOI1SfU_XAwNCFA1Cw8S9VgFIsGVE4f48RUXOk81k8WfBw_RHBP7O5nigspnMMfpGu9PqCwpOdb30T8OEsyUhqUQAdojgFMCP759M4UarI8UHlQuBVvFI_O0rAkFoXa'
    },
    content: '今天天气特别好，带上我家两个宝贝去了附近的森林公园，它们玩得可开心了...',
    images: ['https://lh3.googleusercontent.com/aida-public/AB6AXuDnGKMOuN_F8H5uOFb3j49b5yd5NLI2h-4SUOh7WHH8RnGv1sMEMlccZ82bMyZNlljpjJ2DkPTc-t0dIiAaW6z27OXMcv8Xh8vwslFjBaNX5Bla3R7DSmj2_fVeHNXO_fll51KIEurZDYy-QfkzhcrBs-mfEeXB2wxyoW7T8FeEvZ0-2un_qapLmF9zTL7zuP7LvLUz0Puo3K54skhjaII91Uyb__7yew_cNqnB6yOrg9o1y-shG7khL5AAHFXqMSJo_hEBNM07LwXs'],
    tags: ['户外'],
    createdAt: '2小时前',
    likes: 120,
    comments: 12
  }
])
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
        <h1 class="font-display-lg text-display-lg text-on-background">你好, {{ currentUser?.name }}</h1>
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
