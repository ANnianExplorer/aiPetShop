<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useToast } from '@/composables/useToast'
import { healthApi } from '@/api/health'
import { useUserStore } from '@/stores/user'
import { formatDate } from '@/utils/format'

const router = useRouter()
const { showToast } = useToast()
const userStore = useUserStore()
const { currentPet } = storeToRefs(userStore)
const submitting = ref(false)

const healthData = ref({
  heartRate: '',
  sleepHours: '',
  steps: '',
  calories: '',
  exercise: '',
  weight: '',
  waterIntake: '',
  mood: ''
})

const moods = [
  { id: 'happy', name: '开心', icon: 'sentiment_very_satisfied' },
  { id: 'normal', name: '正常', icon: 'sentiment_neutral' },
  { id: 'tired', name: '疲惫', icon: 'sentiment_dissatisfied' },
  { id: 'active', name: '活跃', icon: 'emoji_events' }
]

const targets = {
  heartRate: { min: 60, max: 100, unit: 'bpm' },
  sleepHours: { min: 8, max: 12, unit: '小时' },
  steps: { min: 5000, max: 10000, unit: '步' },
  calories: { min: 300, max: 600, unit: 'kcal' },
  exercise: { min: 30, max: 60, unit: '分钟' },
  weight: { min: 10, max: 20, unit: 'kg' },
  waterIntake: { min: 200, max: 500, unit: 'ml' }
}

const analysisResult = ref<{
  score: number
  metCount: number
  totalCount: number
  suggestions: string[]
} | null>(null)

const metCount = computed(() => {
  let count = 0
  let total = 0

  if (healthData.value.heartRate) {
    total++
    const val = Number(healthData.value.heartRate)
    if (val >= targets.heartRate.min && val <= targets.heartRate.max) count++
  }
  if (healthData.value.sleepHours) {
    total++
    const val = Number(healthData.value.sleepHours)
    if (val >= targets.sleepHours.min && val <= targets.sleepHours.max) count++
  }
  if (healthData.value.steps) {
    total++
    const val = Number(healthData.value.steps)
    if (val >= targets.steps.min && val <= targets.steps.max) count++
  }
  if (healthData.value.calories) {
    total++
    const val = Number(healthData.value.calories)
    if (val >= targets.calories.min && val <= targets.calories.max) count++
  }
  if (healthData.value.exercise) {
    total++
    const val = Number(healthData.value.exercise)
    if (val >= targets.exercise.min && val <= targets.exercise.max) count++
  }
  if (healthData.value.weight) {
    total++
    const val = Number(healthData.value.weight)
    if (val >= targets.weight.min && val <= targets.weight.max) count++
  }
  if (healthData.value.waterIntake) {
    total++
    const val = Number(healthData.value.waterIntake)
    if (val >= targets.waterIntake.min && val <= targets.waterIntake.max) count++
  }

  return { met: count, total }
})

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

const generateSuggestions = () => {
  const suggestions: string[] = []
  
  if (healthData.value.heartRate) {
    const val = Number(healthData.value.heartRate)
    const status = getIndicatorStatus(val, targets.heartRate.min, targets.heartRate.max)
    if (status === 'low') suggestions.push('心率偏低，建议增加适量运动')
    if (status === 'high') suggestions.push('心率偏高，建议适当休息')
  }
  
  if (healthData.value.sleepHours) {
    const val = Number(healthData.value.sleepHours)
    const status = getIndicatorStatus(val, targets.sleepHours.min, targets.sleepHours.max)
    if (status === 'low') suggestions.push('睡眠不足，建议保证充足休息时间')
  }
  
  if (healthData.value.steps) {
    const val = Number(healthData.value.steps)
    const status = getIndicatorStatus(val, targets.steps.min, targets.steps.max)
    if (status === 'low') suggestions.push('步数偏少，建议增加户外活动')
  }
  
  if (healthData.value.exercise) {
    const val = Number(healthData.value.exercise)
    const status = getIndicatorStatus(val, targets.exercise.min, targets.exercise.max)
    if (status === 'low') suggestions.push('运动量不足，建议增加锻炼时间')
  }
  
  if (healthData.value.waterIntake) {
    const val = Number(healthData.value.waterIntake)
    const status = getIndicatorStatus(val, targets.waterIntake.min, targets.waterIntake.max)
    if (status === 'low') suggestions.push('饮水量不足，注意及时补水')
  }
  
  if (suggestions.length === 0) {
    suggestions.push('各项指标良好，继续保持！')
  }
  
  return suggestions
}

const handleSubmit = async () => {
  const pet = currentPet.value
  if (!pet) {
    showToast('请先选择宠物', 'error')
    return
  }

  const filledFields = Object.values(healthData.value).filter(v => v !== '').length
  if (filledFields === 0) {
    showToast('请至少填写一项健康数据', 'error')
    return
  }

  const score = Math.round((metCount.value.met / metCount.value.total) * 100) || 0

  analysisResult.value = {
    score,
    metCount: metCount.value.met,
    totalCount: metCount.value.total,
    suggestions: generateSuggestions()
  }

  try {
    submitting.value = true
    await healthApi.addRecord({
      petId: pet.id,
      date: formatDate(new Date()),
      heartRate: healthData.value.heartRate ? Number(healthData.value.heartRate) : undefined,
      sleepHours: healthData.value.sleepHours ? Number(healthData.value.sleepHours) : undefined,
      steps: healthData.value.steps ? Number(healthData.value.steps) : undefined,
      calories: healthData.value.calories ? Number(healthData.value.calories) : undefined,
      exercise: healthData.value.exercise ? Number(healthData.value.exercise) : undefined,
      weight: healthData.value.weight ? Number(healthData.value.weight) : undefined,
      waterIntake: healthData.value.waterIntake ? Number(healthData.value.waterIntake) : undefined,
      mood: healthData.value.mood || undefined
    })
    showToast('健康数据保存成功', 'success')
  } catch (e) {
    showToast('保存失败，请重试', 'error')
  } finally {
    submitting.value = false
  }
}

const handleReset = () => {
  healthData.value = {
    heartRate: '',
    sleepHours: '',
    steps: '',
    calories: '',
    exercise: '',
    weight: '',
    waterIntake: '',
    mood: ''
  }
  analysisResult.value = null
}

const goBack = () => {
  router.back()
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex items-center justify-between py-md mb-lg">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">录入健康数据</span>
        <button @click="handleReset" class="text-primary font-label-bold text-label-bold">重置</button>
      </div>

      <section class="mb-lg">
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">心情状态</h3>
        <div class="grid grid-cols-4 gap-3">
          <button 
            v-for="mood in moods" 
            :key="mood.id"
            @click="healthData.mood = mood.id"
            class="flex flex-col items-center gap-2 p-3 rounded-xl transition-all active:scale-95"
            :class="healthData.mood === mood.id ? 'bg-primary text-on-primary shadow-md' : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'"
          >
            <span class="material-symbols-outlined text-2xl">{{ mood.icon }}</span>
            <span class="text-xs font-label-bold">{{ mood.name }}</span>
          </button>
        </div>
      </section>

      <section class="space-y-4 mb-lg">
        <h3 class="font-label-bold text-label-bold text-on-surface">健康指标</h3>
        
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">心率 (bpm)</label>
            <input 
              v-model="healthData.heartRate" 
              type="number"
              placeholder="60-100" 
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
            />
          </div>
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">睡眠 (小时)</label>
            <input 
              v-model="healthData.sleepHours" 
              type="number"
              step="0.1"
              placeholder="8-12" 
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
            />
          </div>
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">步数</label>
            <input 
              v-model="healthData.steps" 
              type="number"
              placeholder="5000-10000" 
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
            />
          </div>
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">消耗 (kcal)</label>
            <input 
              v-model="healthData.calories" 
              type="number"
              placeholder="300-600" 
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
            />
          </div>
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">运动 (分钟)</label>
            <input 
              v-model="healthData.exercise" 
              type="number"
              placeholder="30-60" 
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
            />
          </div>
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">体重 (kg)</label>
            <input 
              v-model="healthData.weight" 
              type="number"
              step="0.1"
              placeholder="10-20" 
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
            />
          </div>
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">饮水 (ml)</label>
            <input 
              v-model="healthData.waterIntake" 
              type="number"
              placeholder="200-500" 
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
            />
          </div>
        </div>
      </section>

      <button
        @click="handleSubmit"
        :disabled="submitting"
        class="w-full py-3.5 bg-primary text-on-primary rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform shadow-md mb-lg disabled:opacity-60"
      >
        {{ submitting ? '保存中...' : '提交分析' }}
      </button>

      <section v-if="analysisResult" class="glass-card p-6 rounded-2xl border border-white/50 dark:border-surface-variant/20 bg-white/60 dark:bg-surface-container/60">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-title-sm text-title-sm text-on-surface">分析结果</h3>
          <div class="flex items-center gap-2">
            <span class="text-2xl font-display-lg" :class="analysisResult.score >= 70 ? 'text-emerald-500' : 'text-amber-500'">
              {{ analysisResult.score }}%
            </span>
          </div>
        </div>

        <div class="mb-4">
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-on-surface-variant">达标情况</span>
            <span class="text-sm font-label-bold text-on-surface">{{ analysisResult.metCount }}/{{ analysisResult.totalCount }}</span>
          </div>
          <div class="w-full bg-surface-container rounded-full h-2">
            <div 
              class="h-2 rounded-full transition-all duration-500"
              :class="analysisResult.score >= 70 ? 'bg-emerald-500' : 'bg-amber-500'"
              :style="{ width: analysisResult.score + '%' }"
            ></div>
          </div>
        </div>

        <div class="space-y-2">
          <h4 class="font-label-bold text-label-bold text-on-surface">健康建议</h4>
          <div 
            v-for="(suggestion, index) in analysisResult.suggestions" 
            :key="index"
            class="flex items-start gap-2 p-3 bg-surface-container-low rounded-xl"
          >
            <span class="material-symbols-outlined text-primary text-sm mt-0.5">lightbulb</span>
            <p class="text-sm text-on-surface-variant">{{ suggestion }}</p>
          </div>
        </div>

        <div class="mt-4 pt-4 border-t border-surface-variant/30">
          <h4 class="font-label-bold text-label-bold text-on-surface mb-3">指标状态</h4>
          <div class="grid grid-cols-2 gap-3">
            <div v-if="healthData.heartRate" class="flex items-center justify-between p-3 bg-surface-container-low rounded-xl">
              <span class="text-sm text-on-surface-variant">心率</span>
              <div class="flex items-center gap-1">
                <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(Number(healthData.heartRate), targets.heartRate.min, targets.heartRate.max))">
                  {{ getStatusIcon(getIndicatorStatus(Number(healthData.heartRate), targets.heartRate.min, targets.heartRate.max)) }}
                </span>
                <span class="text-sm font-label-bold text-on-surface">{{ healthData.heartRate }}</span>
              </div>
            </div>
            <div v-if="healthData.sleepHours" class="flex items-center justify-between p-3 bg-surface-container-low rounded-xl">
              <span class="text-sm text-on-surface-variant">睡眠</span>
              <div class="flex items-center gap-1">
                <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(Number(healthData.sleepHours), targets.sleepHours.min, targets.sleepHours.max))">
                  {{ getStatusIcon(getIndicatorStatus(Number(healthData.sleepHours), targets.sleepHours.min, targets.sleepHours.max)) }}
                </span>
                <span class="text-sm font-label-bold text-on-surface">{{ healthData.sleepHours }}h</span>
              </div>
            </div>
            <div v-if="healthData.steps" class="flex items-center justify-between p-3 bg-surface-container-low rounded-xl">
              <span class="text-sm text-on-surface-variant">步数</span>
              <div class="flex items-center gap-1">
                <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(Number(healthData.steps), targets.steps.min, targets.steps.max))">
                  {{ getStatusIcon(getIndicatorStatus(Number(healthData.steps), targets.steps.min, targets.steps.max)) }}
                </span>
                <span class="text-sm font-label-bold text-on-surface">{{ healthData.steps }}</span>
              </div>
            </div>
            <div v-if="healthData.calories" class="flex items-center justify-between p-3 bg-surface-container-low rounded-xl">
              <span class="text-sm text-on-surface-variant">消耗</span>
              <div class="flex items-center gap-1">
                <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(Number(healthData.calories), targets.calories.min, targets.calories.max))">
                  {{ getStatusIcon(getIndicatorStatus(Number(healthData.calories), targets.calories.min, targets.calories.max)) }}
                </span>
                <span class="text-sm font-label-bold text-on-surface">{{ healthData.calories }}kcal</span>
              </div>
            </div>
            <div v-if="healthData.exercise" class="flex items-center justify-between p-3 bg-surface-container-low rounded-xl">
              <span class="text-sm text-on-surface-variant">运动</span>
              <div class="flex items-center gap-1">
                <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(Number(healthData.exercise), targets.exercise.min, targets.exercise.max))">
                  {{ getStatusIcon(getIndicatorStatus(Number(healthData.exercise), targets.exercise.min, targets.exercise.max)) }}
                </span>
                <span class="text-sm font-label-bold text-on-surface">{{ healthData.exercise }}min</span>
              </div>
            </div>
            <div v-if="healthData.weight" class="flex items-center justify-between p-3 bg-surface-container-low rounded-xl">
              <span class="text-sm text-on-surface-variant">体重</span>
              <div class="flex items-center gap-1">
                <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(Number(healthData.weight), targets.weight.min, targets.weight.max))">
                  {{ getStatusIcon(getIndicatorStatus(Number(healthData.weight), targets.weight.min, targets.weight.max)) }}
                </span>
                <span class="text-sm font-label-bold text-on-surface">{{ healthData.weight }}kg</span>
              </div>
            </div>
            <div v-if="healthData.waterIntake" class="flex items-center justify-between p-3 bg-surface-container-low rounded-xl">
              <span class="text-sm text-on-surface-variant">饮水</span>
              <div class="flex items-center gap-1">
                <span class="material-symbols-outlined text-sm" :class="getStatusColor(getIndicatorStatus(Number(healthData.waterIntake), targets.waterIntake.min, targets.waterIntake.max))">
                  {{ getStatusIcon(getIndicatorStatus(Number(healthData.waterIntake), targets.waterIntake.min, targets.waterIntake.max)) }}
                </span>
                <span class="text-sm font-label-bold text-on-surface">{{ healthData.waterIntake }}ml</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
