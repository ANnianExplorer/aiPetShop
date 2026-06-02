<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

defineProps<{
  heartRate: number
  sleepHours: number
  steps: number
  calories: number
  exercise: number
  metRate?: number
}>()

const goToDetail = () => {
  router.push({ name: 'weeklyHealthDetail' })
}

const getIndicatorStatus = (value: number, min: number, max: number) => {
  if (value >= min && value <= max) return 'good'
  if (value < min) return 'low'
  return 'high'
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'good': return 'text-emerald-500'
    case 'low': return 'text-amber-500'
    case 'high': return 'text-rose-500'
    default: return 'text-on-surface-variant'
  }
}

const getStatusBg = (status: string) => {
  switch (status) {
    case 'good': return 'bg-emerald-50'
    case 'low': return 'bg-amber-50'
    case 'high': return 'bg-rose-50'
    default: return 'bg-surface-container'
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'good': return 'check_circle'
    case 'low': return 'arrow_downward'
    case 'high': return 'arrow_upward'
    default: return 'info'
  }
}
</script>

<template>
  <section class="glass-card p-6 rounded-2xl border border-white/50 bg-white/60">
    <div class="flex justify-between items-center mb-6">
      <div class="flex items-center gap-2">
        <h3 class="text-on-surface font-title-sm text-title-sm">昨日健康指标</h3>
        <span class="text-xs px-2 py-0.5 rounded-full" :class="(metRate ?? 0) >= 70 ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'">
          达标率 {{ metRate ?? 0 }}%
        </span>
      </div>
      <button @click="goToDetail" class="text-primary font-label-bold text-label-bold flex items-center">
        详细数据 <span class="material-symbols-outlined text-[16px]">chevron_right</span>
      </button>
    </div>
    <div class="grid grid-cols-5 gap-3">
      <div class="p-3 bg-surface-container-low rounded-xl text-center">
        <div class="flex items-center justify-center gap-1 mb-1">
          <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(heartRate, 60, 100))">
            {{ getStatusIcon(getIndicatorStatus(heartRate, 60, 100)) }}
          </span>
          <span class="text-lg font-title-sm text-on-surface">{{ heartRate }}</span>
        </div>
        <p class="text-[10px] text-tertiary">心率 bpm</p>
      </div>
      <div class="p-3 bg-surface-container-low rounded-xl text-center">
        <div class="flex items-center justify-center gap-1 mb-1">
          <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(sleepHours, 8, 12))">
            {{ getStatusIcon(getIndicatorStatus(sleepHours, 8, 12)) }}
          </span>
          <span class="text-lg font-title-sm text-on-surface">{{ sleepHours }}</span>
        </div>
        <p class="text-[10px] text-tertiary">睡眠 hrs</p>
      </div>
      <div class="p-3 bg-surface-container-low rounded-xl text-center">
        <div class="flex items-center justify-center gap-1 mb-1">
          <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(steps, 5000, 10000))">
            {{ getStatusIcon(getIndicatorStatus(steps, 5000, 10000)) }}
          </span>
          <span class="text-lg font-title-sm text-on-surface">{{ (steps / 1000).toFixed(1) }}k</span>
        </div>
        <p class="text-[10px] text-tertiary">步数</p>
      </div>
      <div class="p-3 bg-surface-container-low rounded-xl text-center">
        <div class="flex items-center justify-center gap-1 mb-1">
          <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(calories, 300, 600))">
            {{ getStatusIcon(getIndicatorStatus(calories, 300, 600)) }}
          </span>
          <span class="text-lg font-title-sm text-on-surface">{{ calories }}</span>
        </div>
        <p class="text-[10px] text-tertiary">消耗 kcal</p>
      </div>
      <div class="p-3 bg-surface-container-low rounded-xl text-center">
        <div class="flex items-center justify-center gap-1 mb-1">
          <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(exercise, 30, 60))">
            {{ getStatusIcon(getIndicatorStatus(exercise, 30, 60)) }}
          </span>
          <span class="text-lg font-title-sm text-on-surface">{{ exercise }}</span>
        </div>
        <p class="text-[10px] text-tertiary">运动 min</p>
      </div>
    </div>
  </section>
</template>
