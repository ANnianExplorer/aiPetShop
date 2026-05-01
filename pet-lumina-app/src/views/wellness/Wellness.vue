<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import BentoDashboard from '@/components/wellness/BentoDashboard.vue'
import DailyTasks from '@/components/wellness/DailyTasks.vue'
import YesterdayIndicators from '@/components/wellness/YesterdayIndicators.vue'
import WeeklyIndicators from '@/components/wellness/WeeklyIndicators.vue'

const router = useRouter()
const userStore = useUserStore()
const { currentPet, pets, tasks, getTasksByPetId, getHealthDataByPetId } = storeToRefs(userStore)

const showPetSelector = ref(false)

const goToNotifications = () => {
  router.push({ name: 'notifications' })
}

const currentTasks = computed(() => {
  if (!currentPet.value) return []
  return getTasksByPetId.value(currentPet.value.id)
})

const currentHealthData = computed(() => {
  if (!currentPet.value) return null
  return getHealthDataByPetId.value(currentPet.value.id)
})

const switchPet = (petId: string) => {
  userStore.switchCurrentPet(petId)
  showPetSelector.value = false
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <div class="flex justify-between items-center py-md mb-md">
        <div class="flex items-center gap-3">
          <div @click="showPetSelector = !showPetSelector" class="w-10 h-10 rounded-full overflow-hidden bg-surface-container-high ring-2 ring-primary/10 cursor-pointer relative">
            <img class="w-full h-full object-cover" :src="currentPet?.avatar" />
            <div class="absolute bottom-0 right-0 w-3 h-3 bg-primary rounded-full border-2 border-white"></div>
          </div>
          <div @click="showPetSelector = !showPetSelector" class="cursor-pointer">
            <h1 class="text-xl font-bold tracking-tighter text-emerald-800 dark:text-emerald-100 font-display-lg">{{ currentPet?.name }}的健康</h1>
            <p class="text-xs text-tertiary">点击切换宠物</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <button @click="goToNotifications" class="material-symbols-outlined text-emerald-700 dark:text-emerald-400 hover:bg-emerald-50 p-2 rounded-full transition-colors">notifications</button>
        </div>
      </div>

      <!-- Pet Selector Dropdown -->
      <Transition name="dropdown">
        <div v-if="showPetSelector" class="bg-surface-container-low rounded-xl shadow-lg border border-surface-variant overflow-hidden mb-4">
          <div 
            v-for="pet in pets" 
            :key="pet.id"
            @click="switchPet(pet.id)"
            class="flex items-center gap-3 p-3 hover:bg-surface-container-high cursor-pointer transition-colors"
            :class="{ 'bg-primary/10': currentPet?.id === pet.id }"
          >
            <div class="w-10 h-10 rounded-full overflow-hidden">
              <img class="w-full h-full object-cover" :src="pet.avatar" />
            </div>
            <div class="flex-1">
              <p class="font-label-bold text-label-bold text-on-surface">{{ pet.name }}</p>
              <p class="text-xs text-tertiary">{{ pet.breed }}</p>
            </div>
            <span v-if="currentPet?.id === pet.id" class="material-symbols-outlined text-primary">check_circle</span>
          </div>
        </div>
      </Transition>

      <!-- Dashboard Header -->
      <section class="flex justify-between items-end">
        <div class="space-y-1">
          <span class="text-primary font-label-bold uppercase tracking-widest text-label-bold">健康总览</span>
          <h2 class="text-on-surface font-headline-md text-headline-md">饮食与健康中心</h2>
        </div>
        <div class="flex gap-2">
          <button @click="router.push({ name: 'recordHealthData' })" class="bg-secondary text-on-secondary px-4 py-2 rounded-full flex items-center gap-2 font-label-bold text-label-bold active:scale-95 transition-transform">
            <span class="material-symbols-outlined text-[18px]">monitor_heart</span>
            录入数据
          </button>
          <button @click="router.push({ name: 'addPlan' })" class="bg-primary text-on-primary px-4 py-2 rounded-full flex items-center gap-2 font-label-bold text-label-bold active:scale-95 transition-transform">
            <span class="material-symbols-outlined text-[18px]">add</span>
            新增计划
          </button>
        </div>
      </section>

      <!-- Split Components -->
      <BentoDashboard 
        v-if="currentHealthData"
        :weight="currentHealthData.weight" 
        :weightChange="currentHealthData.weightChange" 
      />
      <DailyTasks :tasks="currentTasks" />
      <YesterdayIndicators 
        v-if="currentHealthData"
        :heartRate="currentHealthData.yesterdayData.heartRate"
        :sleepHours="currentHealthData.yesterdayData.sleepHours"
        :steps="currentHealthData.yesterdayData.steps"
        :calories="currentHealthData.yesterdayData.calories"
        :exercise="currentHealthData.yesterdayData.exercise"
        :metRate="currentHealthData.yesterdayData.metRate"
      />
      <WeeklyIndicators 
        v-if="currentHealthData"
        :heartRate="currentHealthData.weeklyData.heartRate" 
        :sleepHours="currentHealthData.weeklyData.sleepHours" 
      />
    </main>

    <!-- Contextual FAB -->
    <button @click="router.push({ name: 'addPlan' })" class="fixed bottom-24 right-6 w-14 h-14 bg-primary text-on-primary rounded-full shadow-lg flex items-center justify-center active:scale-90 transition-transform z-40">
      <span class="material-symbols-outlined text-[28px]">edit_square</span>
    </button>
  </div>
</template>
