<script setup lang="ts">
import { ref } from 'vue'
import type { Pet } from '@/types'
import { computed } from 'vue'
import { useToast } from '@/composables/useToast'

const props = defineProps<{
  pet: Pet
}>()

const { showToast } = useToast()

const stepPercentage = computed(() => {
  return Math.min((props.pet.todaySteps / 10000) * 100, 100)
})

const showDetail = (type: string) => {
  showToast(`${type}详情功能开发中...`, 'info')
}
</script>

<template>
  <section>
    <h2 class="font-headline-md text-headline-md mb-md">宠物状态</h2>
    <div class="grid grid-cols-2 md:grid-cols-4 gap-card-gutter">
      <div @click="showDetail('今日运动')" class="col-span-2 bg-primary-container text-on-primary-container p-container-padding rounded-2xl relative overflow-hidden h-40 cursor-pointer card-lift depth-1">
        <div class="relative z-10">
          <p class="font-label-bold text-label-bold opacity-80 uppercase">今日运动</p>
          <p class="font-display-lg text-display-lg mt-2">{{ pet.todaySteps.toLocaleString() }} <span class="text-sm font-normal">步</span></p>
          <div class="w-full bg-on-primary-container/20 h-1.5 rounded-full mt-4">
            <div class="bg-on-primary-container h-full rounded-full transition-all duration-1000" :style="{ width: `${stepPercentage}%` }"></div>
          </div>
        </div>
        <span class="material-symbols-outlined absolute -bottom-4 -right-4 text-[120px] opacity-10">pets</span>
      </div>

      <div @click="showDetail('喂食进度')" class="glass-card p-container-padding rounded-2xl flex flex-col justify-between h-40 cursor-pointer depth-1">
        <span class="material-symbols-outlined text-primary text-3xl glow-icon">restaurant</span>
        <div>
          <p class="font-label-bold text-label-bold">喂食进度</p>
          <p class="font-title-sm text-title-sm mt-1">{{ pet.feedingCount }}/{{ pet.feedingTotal }} 次</p>
        </div>
      </div>

      <div @click="showDetail('健康评分')" class="bg-secondary-container text-on-secondary-container p-container-padding rounded-2xl flex flex-col justify-between h-40 cursor-pointer card-lift depth-1">
        <span class="material-symbols-outlined text-on-secondary-container text-3xl">monitor_heart</span>
        <div>
          <p class="font-label-bold text-label-bold">健康评分</p>
          <p class="font-title-sm text-title-sm mt-1">{{ pet.healthScore }} 卓越</p>
        </div>
      </div>
    </div>
  </section>
</template>
