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
const { currentPet, pets, getHealthPlansByPetId, getHealthDataByPetId } = storeToRefs(userStore)

const showPetSelector = ref(false)

const goToNotifications = () => {
  router.push({ name: 'notifications' })
}

const currentPlans = computed(() => {
  if (!currentPet.value) return []
  return getHealthPlansByPetId.value(currentPet.value.id)
})

const currentHealthData = computed(() => {
  if (!currentPet.value) return null
  return getHealthDataByPetId.value(currentPet.value.id)
})

const weeklyAvgHeartRate = computed(() => {
  const data = currentHealthData.value?.weeklyData
  if (!data || !Array.isArray(data) || data.length === 0) return 0
  return Math.round(data.reduce((sum, d) => sum + (d.heartRate || 0), 0) / data.length)
})

const weeklyAvgSleep = computed(() => {
  const data = currentHealthData.value?.weeklyData
  if (!data || !Array.isArray(data) || data.length === 0) return 0
  return Math.round((data.reduce((sum, d) => sum + (d.sleepHours || 0), 0) / data.length) * 10) / 10
})

const switchPet = (petId: number) => {
  userStore.switchCurrentPet(petId)
  showPetSelector.value = false
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <!-- Header -->
      <div class="flex justify-between items-center py-md mb-md animate-float-up">
        <div class="flex items-center gap-3">
          <div @click="showPetSelector = !showPetSelector" class="w-10 h-10 rounded-full overflow-hidden glass-panel ring-2 ring-primary/10 cursor-pointer relative active:scale-90 transition-all duration-300">
            <img class="w-full h-full object-cover" :src="currentPet?.avatar" />
            <div class="absolute bottom-0 right-0 w-3 h-3 bg-primary rounded-full border-2 border-white shadow-sm"></div>
          </div>
          <div @click="showPetSelector = !showPetSelector" class="cursor-pointer">
            <h1 class="text-xl font-bold tracking-tighter text-primary font-display-lg">{{ currentPet ? `${currentPet.name}的健康` : '健康中心' }}</h1>
            <p class="text-xs text-tertiary">点击切换宠物</p>
          </div>
        </div>
        <div class="flex items-center gap-4">
          <button @click="goToNotifications" class="icon-btn p-2 rounded-full">
            <span class="material-symbols-outlined text-primary">notifications</span>
          </button>
        </div>
      </div>

      <!-- Pet Selector Dropdown -->
      <Transition name="dropdown">
        <div v-if="showPetSelector" class="glass-panel-deep rounded-2xl depth-2 overflow-hidden mb-4">
          <div
            v-for="pet in pets"
            :key="pet.id"
            @click="switchPet(pet.id)"
            class="flex items-center gap-3 p-3 hover:bg-white/40 cursor-pointer transition-all duration-200"
            :class="{ 'bg-primary/10': currentPet?.id === pet.id }"
          >
            <div class="w-10 h-10 rounded-full overflow-hidden shadow-sm">
              <img class="w-full h-full object-cover" :src="pet.avatar" />
            </div>
            <div class="flex-1">
              <p class="font-label-bold text-label-bold text-on-surface">{{ pet.name }}</p>
              <p class="text-xs text-tertiary">{{ pet.breed }}</p>
            </div>
            <span v-if="currentPet?.id === pet.id" class="material-symbols-outlined text-primary glow-icon">check_circle</span>
          </div>
        </div>
      </Transition>

      <!-- Dashboard Header -->
      <section class="flex justify-between items-end animate-float-up stagger-1">
        <div class="space-y-1">
          <span class="text-primary font-label-bold uppercase tracking-widest text-label-bold">健康总览</span>
          <h2 class="text-on-surface font-headline-md text-headline-md">饮食与健康中心</h2>
        </div>
        <div class="flex gap-2">
          <button @click="router.push({ name: 'recordHealthData' })" class="bg-secondary text-on-secondary px-4 py-2 rounded-full flex items-center gap-2 font-label-bold text-label-bold btn-jelly shadow-md shadow-secondary/20">
            <span class="material-symbols-outlined text-[18px]">monitor_heart</span>
            录入数据
          </button>
          <button @click="router.push({ name: 'addPlan' })" class="bg-primary text-on-primary px-4 py-2 rounded-full flex items-center gap-2 font-label-bold text-label-bold btn-jelly shadow-md shadow-primary/20">
            <span class="material-symbols-outlined text-[18px]">add</span>
            新增计划
          </button>
        </div>
      </section>

      <!-- Empty state when no pet -->
      <div v-if="!currentPet" class="flex flex-col items-center justify-center py-16 animate-float-up stagger-2">
        <span class="material-symbols-outlined text-6xl text-tertiary mb-4">pets</span>
        <p class="text-tertiary text-lg mb-4">还没有添加宠物哦</p>
        <button @click="router.push('/add-pet')" class="bg-primary text-on-primary px-6 py-3 rounded-full font-label-bold btn-jelly shadow-md">
          添加宠物
        </button>
      </div>

      <!-- Split Components -->
      <div v-if="currentHealthData" class="animate-float-up stagger-2">
        <BentoDashboard
          :weight="currentHealthData.weight"
          :weightChange="currentHealthData.weightChange"
        />
      </div>
      <div class="animate-float-up stagger-3">
        <DailyTasks :tasks="currentPlans" />
      </div>
      <div class="animate-float-up stagger-4">
        <YesterdayIndicators
          v-if="currentHealthData?.yesterdayData"
          :heartRate="currentHealthData.yesterdayData.heartRate ?? 0"
          :sleepHours="currentHealthData.yesterdayData.sleepHours ?? 0"
          :steps="currentHealthData.yesterdayData.steps ?? 0"
          :calories="currentHealthData.yesterdayData.calories ?? 0"
          :exercise="currentHealthData.yesterdayData.exercise ?? 0"
        />
      </div>
      <div class="animate-float-up stagger-5">
        <WeeklyIndicators
          v-if="currentHealthData?.weeklyData"
          :heartRate="weeklyAvgHeartRate"
          :sleepHours="weeklyAvgSleep"
        />
      </div>
    </main>

    <!-- Contextual FAB -->
    <button
      @click="router.push({ name: 'addPlan' })"
      class="fixed bottom-24 right-6 w-14 h-14 bg-primary text-on-primary rounded-full shadow-[0_8px_24px_rgba(75,100,85,0.3)] flex items-center justify-center z-40 btn-jelly animate-scale-in"
      style="animation-delay: 0.5s"
    >
      <span class="material-symbols-outlined text-[28px]">edit_square</span>
    </button>
  </div>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.95);
}
</style>
