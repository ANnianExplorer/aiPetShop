<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

defineProps<{
  heartRate: number
  sleepHours: number
}>()

const goToDetail = () => {
  router.push({ name: 'weeklyHealthDetail' })
}
</script>

<template>
  <section class="glass-card p-6 rounded-2xl border border-white/50 dark:border-surface-variant/20 bg-white/60 dark:bg-surface-container/60">
    <div class="flex justify-between items-center mb-6">
      <h3 class="text-on-surface font-title-sm text-title-sm">周健康指标</h3>
      <button @click="goToDetail" class="text-primary font-label-bold text-label-bold flex items-center">
        详细数据 <span class="material-symbols-outlined text-[16px]">chevron_right</span>
      </button>
    </div>
    <div class="grid grid-cols-2 gap-4">
      <div class="p-4 bg-surface-container-low rounded-xl">
        <div class="flex items-center gap-2 mb-2">
          <span class="material-symbols-outlined text-primary text-[20px]">ecg_heart</span>
          <span class="text-tertiary font-label-bold text-[10px]">平均心率</span>
        </div>
        <p class="text-on-surface font-title-sm">{{ heartRate }} <span class="text-[12px] text-tertiary">bpm</span></p>
      </div>
      <div class="p-4 bg-surface-container-low rounded-xl">
        <div class="flex items-center gap-2 mb-2">
          <span class="material-symbols-outlined text-secondary text-[20px]">sleep</span>
          <span class="text-tertiary font-label-bold text-[10px]">睡眠质量</span>
        </div>
        <p class="text-on-surface font-title-sm">{{ sleepHours }} <span class="text-[12px] text-tertiary">hrs</span></p>
      </div>
    </div>
  </section>
</template>
