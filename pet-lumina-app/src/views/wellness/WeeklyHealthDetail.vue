<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  router.back()
}

const weeklyData = ref([
  { day: '周一', heartRate: 72, sleep: 8.5, steps: 5200, calories: 320, exercise: 25 },
  { day: '周二', heartRate: 78, sleep: 9.2, steps: 6800, calories: 410, exercise: 40 },
  { day: '周三', heartRate: 75, sleep: 7.8, steps: 4500, calories: 280, exercise: 20 },
  { day: '周四', heartRate: 82, sleep: 9.5, steps: 8200, calories: 520, exercise: 55 },
  { day: '周五', heartRate: 80, sleep: 9.0, steps: 7500, calories: 480, exercise: 50 },
  { day: '周六', heartRate: 76, sleep: 10.2, steps: 9000, calories: 580, exercise: 65 },
  { day: '周日', heartRate: 74, sleep: 9.8, steps: 7800, calories: 450, exercise: 45 }
])

const targets = {
  heartRate: { min: 60, max: 100, unit: 'bpm' },
  sleep: { min: 8, max: 12, unit: 'hrs' },
  steps: { min: 5000, max: 10000, unit: '步' },
  calories: { min: 300, max: 600, unit: 'kcal' },
  exercise: { min: 30, max: 60, unit: 'min' }
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

const getStatusText = (status: string) => {
  switch (status) {
    case 'good': return '达标'
    case 'low': return '偏低'
    case 'high': return '偏高'
    default: return '正常'
  }
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex items-center justify-between py-md mb-lg">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">周健康指标详情</span>
        <div class="w-10"></div>
      </div>

      <section class="mb-6">
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">本周数据概览</h3>
        <div class="grid grid-cols-5 gap-3">
          <div class="bg-surface-container-low rounded-xl p-3 text-center">
            <p class="text-2xl font-display-lg text-on-surface">78</p>
            <p class="text-xs text-tertiary mt-1">平均心率</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3 text-center">
            <p class="text-2xl font-display-lg text-on-surface">9.2</p>
            <p class="text-xs text-tertiary mt-1">平均睡眠</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3 text-center">
            <p class="text-2xl font-display-lg text-on-surface">6.9k</p>
            <p class="text-xs text-tertiary mt-1">日均步数</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3 text-center">
            <p class="text-2xl font-display-lg text-on-surface">434</p>
            <p class="text-xs text-tertiary mt-1">日均消耗</p>
          </div>
          <div class="bg-surface-container-low rounded-xl p-3 text-center">
            <p class="text-2xl font-display-lg text-on-surface">43</p>
            <p class="text-xs text-tertiary mt-1">日均运动</p>
          </div>
        </div>
      </section>

      <section class="mb-6">
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">每日详细数据</h3>
        <div class="space-y-3">
          <div 
            v-for="day in weeklyData" 
            :key="day.day"
            class="bg-surface-container-low rounded-xl p-4"
          >
            <div class="flex items-center justify-between mb-3">
              <span class="font-label-bold text-label-bold text-on-surface">{{ day.day }}</span>
              <div class="flex items-center gap-2">
                <span class="text-xs px-2 py-0.5 rounded-full" :class="getIndicatorStatus(day.exercise, targets.exercise.min, targets.exercise.max) === 'good' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'">
                  {{ getIndicatorStatus(day.exercise, targets.exercise.min, targets.exercise.max) === 'good' ? '运动达标' : '运动不足' }}
                </span>
              </div>
            </div>
            <div class="grid grid-cols-5 gap-3">
              <div class="text-center">
                <div class="flex items-center justify-center gap-1 mb-1">
                  <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(day.heartRate, targets.heartRate.min, targets.heartRate.max))">
                    {{ getStatusIcon(getIndicatorStatus(day.heartRate, targets.heartRate.min, targets.heartRate.max)) }}
                  </span>
                  <span class="text-sm font-label-bold text-on-surface">{{ day.heartRate }}</span>
                </div>
                <p class="text-[10px] text-tertiary">心率</p>
              </div>
              <div class="text-center">
                <div class="flex items-center justify-center gap-1 mb-1">
                  <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(day.sleep, targets.sleep.min, targets.sleep.max))">
                    {{ getStatusIcon(getIndicatorStatus(day.sleep, targets.sleep.min, targets.sleep.max)) }}
                  </span>
                  <span class="text-sm font-label-bold text-on-surface">{{ day.sleep }}</span>
                </div>
                <p class="text-[10px] text-tertiary">睡眠</p>
              </div>
              <div class="text-center">
                <div class="flex items-center justify-center gap-1 mb-1">
                  <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(day.steps, targets.steps.min, targets.steps.max))">
                    {{ getStatusIcon(getIndicatorStatus(day.steps, targets.steps.min, targets.steps.max)) }}
                  </span>
                  <span class="text-sm font-label-bold text-on-surface">{{ (day.steps / 1000).toFixed(1) }}k</span>
                </div>
                <p class="text-[10px] text-tertiary">步数</p>
              </div>
              <div class="text-center">
                <div class="flex items-center justify-center gap-1 mb-1">
                  <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(day.calories, targets.calories.min, targets.calories.max))">
                    {{ getStatusIcon(getIndicatorStatus(day.calories, targets.calories.min, targets.calories.max)) }}
                  </span>
                  <span class="text-sm font-label-bold text-on-surface">{{ day.calories }}</span>
                </div>
                <p class="text-[10px] text-tertiary">消耗</p>
              </div>
              <div class="text-center">
                <div class="flex items-center justify-center gap-1 mb-1">
                  <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(day.exercise, targets.exercise.min, targets.exercise.max))">
                    {{ getStatusIcon(getIndicatorStatus(day.exercise, targets.exercise.min, targets.exercise.max)) }}
                  </span>
                  <span class="text-sm font-label-bold text-on-surface">{{ day.exercise }}</span>
                </div>
                <p class="text-[10px] text-tertiary">运动</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section>
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">指标说明</h3>
        <div class="space-y-2">
          <div class="flex items-center gap-3 p-3 bg-surface-container-low rounded-xl">
            <span class="material-symbols-outlined text-emerald-500">check_circle</span>
            <div>
              <p class="text-sm font-label-bold text-on-surface">达标</p>
              <p class="text-xs text-tertiary">指标在正常范围内</p>
            </div>
          </div>
          <div class="flex items-center gap-3 p-3 bg-surface-container-low rounded-xl">
            <span class="material-symbols-outlined text-amber-500">arrow_downward</span>
            <div>
              <p class="text-sm font-label-bold text-on-surface">偏低</p>
              <p class="text-xs text-tertiary">指标低于正常范围，需要关注</p>
            </div>
          </div>
          <div class="flex items-center gap-3 p-3 bg-surface-container-low rounded-xl">
            <span class="material-symbols-outlined text-rose-500">arrow_upward</span>
            <div>
              <p class="text-sm font-label-bold text-on-surface">偏高</p>
              <p class="text-xs text-tertiary">指标高于正常范围，建议调整</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
