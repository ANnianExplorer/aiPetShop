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
  try {
    const today = new Date().toISOString().split('T')[0]
    const res = await reminderApi.listPage({ pageSize: 5, startDate: today }) as any
    reminders.value = res?.records || []
  } catch (e) {
    reminders.value = []
  }

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
    <header class="fixed top-0 w-full z-50 bg-white/70 backdrop-blur-2xl border-b border-white/30 shadow-[0_4px_20px_rgba(75,100,85,0.04)]">
      <div class="flex justify-between items-center px-5 py-3 w-full max-w-screen-xl mx-auto">
        <div class="flex items-center gap-3">
          <div @click="goToProfile" class="w-10 h-10 rounded-full overflow-hidden border-2 border-primary-fixed cursor-pointer active:scale-90 transition-all duration-300 shadow-md">
            <img class="w-full h-full object-cover" :src="currentUser?.avatar" alt="Avatar" />
          </div>
          <span class="text-xl font-bold tracking-tighter text-primary font-['Plus_Jakarta_Sans']">PetLumina</span>
        </div>
        <div @click="goToNotifications" class="icon-btn cursor-pointer p-2 rounded-full">
          <span class="material-symbols-outlined text-primary">notifications</span>
        </div>
      </div>
    </header>

    <main class="pt-20 px-container-padding space-y-lg max-w-screen-xl mx-auto">
      <!-- Welcome Section -->
      <section class="mt-4 animate-float-up">
        <h1 class="font-display-lg text-display-lg text-on-background">你好, {{ currentUser?.nickname }}</h1>
        <p class="font-body-md text-body-md text-on-surface-variant opacity-70">今天也是充满活力的一天！</p>
      </section>

      <!-- Extracted Components with stagger -->
      <div class="animate-float-up stagger-1">
        <TodayReminders :reminders="reminders" />
      </div>
      <div class="animate-float-up stagger-2">
        <PetStatusBento v-if="currentPet" :pet="currentPet" />
      </div>
      <div class="animate-float-up stagger-3">
        <CommunityTrends :trends="trends" />
      </div>
    </main>

    <!-- FAB with jelly effect -->
    <button
      @click="addNewReminder"
      class="fixed bottom-24 right-5 w-14 h-14 bg-primary text-on-primary rounded-full shadow-[0_8px_24px_rgba(75,100,85,0.3)] flex items-center justify-center z-40 btn-jelly animate-scale-in"
      style="animation-delay: 0.4s"
    >
      <span class="material-symbols-outlined text-3xl">add</span>
    </button>
  </div>
</template>
