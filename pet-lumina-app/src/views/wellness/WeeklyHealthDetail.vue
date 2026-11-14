<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { healthApi } from '@/api/health'
import { useUserStore } from '@/stores/user'
import { formatDateShort } from '@/utils/format'
import type { PetHealthData } from '@/types'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { currentPet } = storeToRefs(userStore)
const loading = ref(false)

const goBack = () => {
  router.back()
}

const weeklyData = ref<PetHealthData[]>([])
// 从对话里的健康引用跳过来时带着 petId 与 date：那只宠物 + 那一天要被框出来，
// 否则用户点进来只看到一片"本周"，还得自己找是哪一条。
const queryPetId = typeof route.query.petId === 'string' ? route.query.petId : ''
const focusDate = typeof route.query.date === 'string' ? route.query.date.slice(0, 10) : ''

const dayKey = (day: PetHealthData): string => (day.date ? String(day.date).slice(0, 10) : '')

const isFocusedDay = (day: PetHealthData): boolean => !!focusDate && dayKey(day) === focusDate

const hasFocus = computed(
  () => !!focusDate && weeklyData.value.some((day) => isFocusedDay(day))
)

onMounted(async () => {
  const petId = queryPetId || currentPet.value?.id
  if (!petId) return
  try {
    loading.value = true
    const data = await healthApi.weekly(petId)
    weeklyData.value = Array.isArray(data) ? data : []
    if (hasFocus.value) {
      // 等一帧让 v-highlight 的类名先挂上，再滚过去
      await Promise.resolve()
      document
        .querySelector('[data-citation-focus="true"]')
        ?.scrollIntoView({ block: 'center', behavior: 'smooth' })
    }
  } catch (e) {
    weeklyData.value = []
  } finally {
    loading.value = false
  }
})

const targets = {
  heartRate: { min: 60, max: 100, unit: 'bpm' },
  sleep: { min: 8, max: 12, unit: 'hrs' },
  steps: { min: 5000, max: 10000, unit: '步' },
  calories: { min: 300, max: 600, unit: 'kcal' },
  exercise: { min: 30, max: 60, unit: 'min' }
}

const hasData = computed(() => weeklyData.value.length > 0)

const average = (pick: (record: PetHealthData) => number | undefined): number | null => {
  const values = weeklyData.value
    .map(pick)
    .filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
  if (values.length === 0) return null
  return values.reduce((sum, value) => sum + value, 0) / values.length
}

const formatNumber = (value: number | null, digits = 0) => {
  if (value === null) return '--'
  return digits > 0 ? value.toFixed(digits) : String(Math.round(value))
}

const formatSteps = (value: number | null) => {
  if (value === null) return '--'
  return value >= 1000 ? `${(value / 1000).toFixed(1)}k` : String(Math.round(value))
}

// 概览全部由后端 weekly 接口的真实记录计算，没有记录时显示 "--"
const overview = computed(() => [
  { label: '平均心率', value: formatNumber(average(r => r.heartRate)) },
  { label: '平均睡眠', value: formatNumber(average(r => r.sleepHours), 1) },
  { label: '日均步数', value: formatSteps(average(r => r.steps)) },
  { label: '日均消耗', value: formatNumber(average(r => r.calories)) },
  { label: '日均运动', value: formatNumber(average(r => r.exercise)) }
])

type IndicatorStatus = 'good' | 'low' | 'high' | 'unknown'

const getIndicatorStatus = (value: number | undefined, min: number, max: number): IndicatorStatus => {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'unknown'
  if (value >= min && value <= max) return 'good'
  if (value < min) return 'low'
  return 'high'
}

const getStatusColor = (status: IndicatorStatus) => {
  switch (status) {
    case 'good': return 'text-emerald-500'
    case 'low': return 'text-amber-500'
    case 'high': return 'text-rose-500'
    default: return 'text-on-surface-variant'
  }
}

const getStatusIcon = (status: IndicatorStatus) => {
  switch (status) {
    case 'good': return 'check_circle'
    case 'low': return 'arrow_downward'
    case 'high': return 'arrow_upward'
    default: return 'info'
  }
}

const getDayLabel = (record: PetHealthData) => {
  const formatted = formatDateShort(record.date)
  return formatted || '--'
}

// 未填写运动数据时不要显示"运动不足"，避免把缺失当成不达标
const getExerciseBadge = (value?: number) => {
  const status = getIndicatorStatus(value, targets.exercise.min, targets.exercise.max)
  if (status === 'unknown') return { text: '未记录', cls: 'bg-surface-container text-on-surface-variant' }
  return status === 'good'
    ? { text: '运动达标', cls: 'bg-emerald-100 text-emerald-700' }
    : { text: '运动不足', cls: 'bg-amber-100 text-amber-700' }
}

const goToRecord = () => {
  router.push({ name: 'recordHealthData' })
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

      <div v-if="loading" class="flex flex-col items-center justify-center py-20">
        <div class="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        <p class="mt-4 text-on-surface-variant text-sm">加载中…</p>
      </div>

      <template v-else-if="hasData">
        <section class="mb-6">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">本周数据概览</h3>
          <div class="grid grid-cols-5 gap-3">
            <div v-for="item in overview" :key="item.label" class="bg-surface-container-low rounded-xl p-3 text-center">
              <p class="text-2xl font-display-lg text-on-surface">{{ item.value }}</p>
              <p class="text-xs text-tertiary mt-1">{{ item.label }}</p>
            </div>
          </div>
        </section>

        <section class="mb-6">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">每日详细数据</h3>
          <div class="space-y-3">
            <div
              v-for="(day, index) in weeklyData"
              :key="day.date || day.id || index"
              class="bg-surface-container-low rounded-xl p-4"
              :class="isFocusedDay(day) ? 'ring-2 ring-primary bg-primary/5' : ''"
              :data-citation-focus="isFocusedDay(day) ? 'true' : undefined"
            >
              <div class="flex items-center justify-between mb-3">
                <span class="font-label-bold text-label-bold text-on-surface">{{ getDayLabel(day) }}</span>
                <div class="flex items-center gap-2">
                  <span
                    class="text-xs px-2 py-0.5 rounded-full"
                    :class="getExerciseBadge(day.exercise).cls"
                  >
                    {{ getExerciseBadge(day.exercise).text }}
                  </span>
                </div>
              </div>
              <div class="grid grid-cols-5 gap-3">
                <div class="text-center">
                  <div class="flex items-center justify-center gap-1 mb-1">
                    <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(day.heartRate, targets.heartRate.min, targets.heartRate.max))">
                      {{ getStatusIcon(getIndicatorStatus(day.heartRate, targets.heartRate.min, targets.heartRate.max)) }}
                    </span>
                    <span class="text-sm font-label-bold text-on-surface">{{ day.heartRate ?? '--' }}</span>
                  </div>
                  <p class="text-[10px] text-tertiary">心率</p>
                </div>
                <div class="text-center">
                  <div class="flex items-center justify-center gap-1 mb-1">
                    <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(day.sleepHours, targets.sleep.min, targets.sleep.max))">
                      {{ getStatusIcon(getIndicatorStatus(day.sleepHours, targets.sleep.min, targets.sleep.max)) }}
                    </span>
                    <span class="text-sm font-label-bold text-on-surface">{{ day.sleepHours ?? '--' }}</span>
                  </div>
                  <p class="text-[10px] text-tertiary">睡眠</p>
                </div>
                <div class="text-center">
                  <div class="flex items-center justify-center gap-1 mb-1">
                    <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(day.steps, targets.steps.min, targets.steps.max))">
                      {{ getStatusIcon(getIndicatorStatus(day.steps, targets.steps.min, targets.steps.max)) }}
                    </span>
                    <span class="text-sm font-label-bold text-on-surface">{{ typeof day.steps === 'number' ? (day.steps / 1000).toFixed(1) + 'k' : '--' }}</span>
                  </div>
                  <p class="text-[10px] text-tertiary">步数</p>
                </div>
                <div class="text-center">
                  <div class="flex items-center justify-center gap-1 mb-1">
                    <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(day.calories, targets.calories.min, targets.calories.max))">
                      {{ getStatusIcon(getIndicatorStatus(day.calories, targets.calories.min, targets.calories.max)) }}
                    </span>
                    <span class="text-sm font-label-bold text-on-surface">{{ day.calories ?? '--' }}</span>
                  </div>
                  <p class="text-[10px] text-tertiary">消耗</p>
                </div>
                <div class="text-center">
                  <div class="flex items-center justify-center gap-1 mb-1">
                    <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(day.exercise, targets.exercise.min, targets.exercise.max))">
                      {{ getStatusIcon(getIndicatorStatus(day.exercise, targets.exercise.min, targets.exercise.max)) }}
                    </span>
                    <span class="text-sm font-label-bold text-on-surface">{{ day.exercise ?? '--' }}</span>
                  </div>
                  <p class="text-[10px] text-tertiary">运动</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </template>

      <section v-else class="flex flex-col items-center justify-center py-20">
        <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">monitor_heart</span>
        <p class="mt-4 font-title-md text-on-surface-variant">本周还没有健康记录</p>
        <button @click="goToRecord" class="mt-4 px-6 py-2 bg-primary text-on-primary rounded-full font-label-bold">
          去录入
        </button>
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
