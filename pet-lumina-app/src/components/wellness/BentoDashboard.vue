<script setup lang="ts">
import { computed } from 'vue'
import type { PetHealthData } from '@/types'

const props = defineProps<{
  weight?: number
  weightChange?: string
  weekly?: PetHealthData[]
}>()

// 目标是 WeeklyHealthDetail 中同一套步数标准（5000 步）
const STEP_TARGET = 5000

const activityData = computed(() => {
  return (props.weekly ?? []).flatMap(record => {
    const steps = record.steps
    if (typeof steps !== 'number') return []
    return [{
      day: formatDay(record.date),
      value: steps,
      target: STEP_TARGET,
      met: steps >= STEP_TARGET
    }]
  })
})

const hasActivity = computed(() => activityData.value.length > 0)

const metRate = computed(() => {
  if (!hasActivity.value) return 0
  const metCount = activityData.value.filter(d => d.met).length
  return Math.round((metCount / activityData.value.length) * 100)
})

const maxVal = computed(() => {
  const maxSteps = Math.max(...activityData.value.map(d => d.value), 0)
  return Math.max(maxSteps, STEP_TARGET)
})

function formatDay(date?: string) {
  if (!date) return '--'
  const parsed = new Date(date.replace(/-/g, '/'))
  if (Number.isNaN(parsed.getTime())) return date.slice(0, 10)
  return `${parsed.getMonth() + 1}/${parsed.getDate()}`
}
</script>

<template>
  <section class="grid grid-cols-1 md:grid-cols-3 gap-card-gutter">
    <!-- Weight Card -->
    <div class="glass-card p-6 rounded-2xl flex flex-col justify-between h-48 ripple-card anim-float">
      <div class="flex justify-between items-start">
        <div class="bg-primary-fixed p-3 rounded-full">
          <span class="material-symbols-outlined text-primary glow-icon anim-icon-pulse">monitor_weight</span>
        </div>
        <span v-if="weightChange" class="text-emerald-600 font-label-bold text-xs">{{ weightChange }}</span>
      </div>
      <div>
        <p class="text-tertiary font-label-bold text-label-bold">当前体重</p>
        <div class="flex items-baseline gap-1">
          <span class="text-on-surface font-display-lg text-display-lg animate-number-pop">{{ weight ?? '--' }}</span>
          <span class="text-tertiary font-label-bold">kg</span>
        </div>
      </div>
    </div>

    <!-- Activity Trends（数据来自后端 weekly 接口，无记录时显示空态） -->
    <div class="glass-card p-6 rounded-2xl md:col-span-2 h-48 relative overflow-hidden ripple-card anim-shadow-breathe">
      <div class="flex justify-between items-center mb-4">
        <div>
          <p class="text-tertiary font-label-bold text-label-bold">活动趋势</p>
          <div v-if="hasActivity" class="flex items-center gap-2">
            <h3 class="text-on-surface font-title-sm text-title-sm">本周步数达标率 {{ metRate }}%</h3>
            <span class="text-xs px-2 py-0.5 rounded-full" :class="metRate >= 70 ? 'badge-success' : 'badge-warning'">
              {{ metRate >= 70 ? '表现优秀' : '继续加油' }}
            </span>
          </div>
          <h3 v-else class="text-on-surface font-title-sm text-title-sm">本周活动数据</h3>
        </div>
      </div>

      <template v-if="hasActivity">
        <div class="relative h-24 px-2">
          <div
            class="absolute left-0 right-0 border-t-2 border-dashed border-primary/30"
            :style="{ bottom: (STEP_TARGET / maxVal * 100) + '%' }"
          >
            <span class="absolute -top-3 right-0 text-[10px] text-primary/60 font-label-bold">目标 {{ STEP_TARGET }} 步</span>
          </div>

          <div class="flex items-end justify-between h-full gap-3">
            <div
              v-for="(item, index) in activityData"
              :key="index"
              class="flex flex-col items-center gap-2 flex-1 group"
            >
              <div class="relative w-full flex justify-center">
                <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-container-high text-on-surface text-xs px-2 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 shadow-sm">
                  {{ item.value }} 步 {{ item.met ? '✓' : '✗' }}
                </div>

                <div class="relative w-full max-w-[32px]">
                  <div
                    class="w-full rounded-t-lg transition-all duration-500 relative overflow-hidden"
                    :class="item.met ? 'bg-gradient-to-t from-primary to-primary-container' : 'bg-gradient-to-t from-surface-variant/30 to-surface-variant/50'"
                    :style="{ height: (item.value / maxVal * 100) + '%' }"
                  >
                    <div v-if="item.met" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12 animate-[shimmerSweep_3s_ease-in-out_infinite]" :style="{ animationDelay: `${index * -0.5}s` }"></div>
                  </div>

                  <div v-if="item.met" class="absolute -top-5 left-1/2 -translate-x-1/2 animate-bounce">
                    <span class="material-symbols-outlined text-emerald-500 text-sm">check_circle</span>
                  </div>
                </div>
              </div>
              <span class="text-[10px] text-tertiary font-label-bold">{{ item.day }}</span>
            </div>
          </div>
        </div>

        <div class="mt-4 flex items-center justify-between px-2">
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-1.5">
              <div class="w-3 h-3 rounded bg-gradient-to-t from-primary to-primary-container"></div>
              <span class="text-xs text-on-surface-variant">达标 {{ activityData.filter(d => d.met).length }} 天</span>
            </div>
            <div class="flex items-center gap-1.5">
              <div class="w-3 h-3 rounded bg-gradient-to-t from-surface-variant/30 to-surface-variant/50"></div>
              <span class="text-xs text-on-surface-variant">未达标 {{ activityData.filter(d => !d.met).length }} 天</span>
            </div>
          </div>
          <span class="text-xs text-tertiary">目标: {{ STEP_TARGET }} 步</span>
        </div>
      </template>

      <div v-else class="flex flex-col items-center justify-center h-24">
        <span class="material-symbols-outlined text-3xl text-on-surface-variant opacity-30">bar_chart</span>
        <p class="mt-2 text-xs text-on-surface-variant">本周还没有活动记录</p>
      </div>
    </div>
  </section>
</template>
