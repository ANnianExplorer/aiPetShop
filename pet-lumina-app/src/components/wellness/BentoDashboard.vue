<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  weight?: number
  weightChange?: string
}>()

const activityData = computed(() => [
  { day: '周一', value: 40, target: 60, met: false },
  { day: '周二', value: 65, target: 60, met: true },
  { day: '周三', value: 50, target: 60, met: false },
  { day: '周四', value: 85, target: 60, met: true },
  { day: '周五', value: 95, target: 60, met: true },
  { day: '周六', value: 60, target: 60, met: true },
  { day: '周日', value: 75, target: 60, met: true }
])

const metRate = computed(() => {
  const metCount = activityData.value.filter(d => d.met).length
  return Math.round((metCount / activityData.value.length) * 100)
})

const maxVal = computed(() => Math.max(...activityData.value.map(d => d.value)))
</script>

<template>
  <section class="grid grid-cols-1 md:grid-cols-3 gap-card-gutter">
    <!-- Weight Card -->
    <div class="glass-card p-6 rounded-2xl depth-2 flex flex-col justify-between h-48 bg-white/60">
      <div class="flex justify-between items-start">
        <div class="bg-primary-fixed p-3 rounded-full">
          <span class="material-symbols-outlined text-primary glow-icon">monitor_weight</span>
        </div>
        <span class="text-emerald-600 font-label-bold text-xs">{{ weightChange }}</span>
      </div>
      <div>
        <p class="text-tertiary font-label-bold text-label-bold">当前体重</p>
        <div class="flex items-baseline gap-1">
          <span class="text-on-surface font-display-lg text-display-lg animate-number-pop">{{ weight }}</span>
          <span class="text-tertiary font-label-bold">kg</span>
        </div>
      </div>
    </div>

    <!-- Activity Trends -->
    <div class="glass-card p-6 rounded-2xl depth-2 md:col-span-2 h-48 relative overflow-hidden bg-white/60">
      <div class="flex justify-between items-center mb-4">
        <div>
          <p class="text-tertiary font-label-bold text-label-bold">活动趋势</p>
          <div class="flex items-center gap-2">
            <h3 class="text-on-surface font-title-sm text-title-sm">本周达标率 {{ metRate }}%</h3>
            <span class="text-xs px-2 py-0.5 rounded-full" :class="metRate >= 70 ? 'badge-success' : 'badge-warning'">
              {{ metRate >= 70 ? '表现优秀' : '继续加油' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Enhanced Chart -->
      <div class="relative h-24 px-2">
        <!-- Target line -->
        <div
          class="absolute left-0 right-0 border-t-2 border-dashed border-primary/30"
          :style="{ bottom: (60 / maxVal * 100) + '%' }"
        >
          <span class="absolute -top-3 right-0 text-[10px] text-primary/60 font-label-bold">目标 60%</span>
        </div>

        <!-- Bars -->
        <div class="flex items-end justify-between h-full gap-3">
          <div
            v-for="(item, index) in activityData"
            :key="index"
            class="flex flex-col items-center gap-2 flex-1 group"
          >
            <div class="relative w-full flex justify-center">
              <!-- Tooltip on hover -->
              <div class="absolute -top-8 left-1/2 -translate-x-1/2 bg-surface-container-high text-on-surface text-xs px-2 py-1 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10 shadow-sm">
                {{ item.value }}% {{ item.met ? '✓' : '✗' }}
              </div>

              <!-- Bar -->
              <div class="relative w-full max-w-[32px]">
                <div
                  class="w-full rounded-t-lg transition-all duration-500 relative overflow-hidden"
                  :class="item.met ? 'bg-gradient-to-t from-primary to-primary-container' : 'bg-gradient-to-t from-surface-variant/30 to-surface-variant/50'"
                  :style="{ height: (item.value / maxVal * 100) + '%' }"
                >
                  <div v-if="item.met" class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -skew-x-12"></div>
                </div>

                <div
                  v-if="item.met"
                  class="absolute -top-5 left-1/2 -translate-x-1/2 animate-bounce"
                >
                  <span class="material-symbols-outlined text-emerald-500 text-sm">check_circle</span>
                </div>
              </div>
            </div>
            <span class="text-[10px] text-tertiary font-label-bold">{{ item.day }}</span>
          </div>
        </div>
      </div>

      <!-- Summary -->
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
        <span class="text-xs text-tertiary">目标: 60%</span>
      </div>
    </div>
  </section>
</template>
