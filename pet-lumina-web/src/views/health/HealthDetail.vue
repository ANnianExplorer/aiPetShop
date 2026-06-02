<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { healthApi } from '@/api/health'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, GridComponent, TooltipComponent])

const props = defineProps<{ visible: boolean; recordId: number }>()
const emit = defineEmits(['update:visible'])

const detail = ref<any>(null)
const loading = ref(false)

watch(() => props.visible, async (val) => {
  if (val && props.recordId) {
    loading.value = true
    try {
      detail.value = await healthApi.getRecordDetail(props.recordId)
    } catch (e) { console.error(e) } finally { loading.value = false }
  }
})

const handleClose = () => emit('update:visible', false)

const chartOption = computed(() => {
  if (!detail.value?.recentRecords?.length) return {}
  const records = [...detail.value.recentRecords].reverse()
  return {
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: records.map((r: any) => r.date || r.createTime?.substring(0, 10)) },
    yAxis: [
      { type: 'value', name: '心率', position: 'left' },
      { type: 'value', name: '步数', position: 'right' },
    ],
    series: [
      { name: '心率', type: 'line', data: records.map((r: any) => r.heartRate), smooth: true, itemStyle: { color: '#ef4444' } },
      { name: '步数', type: 'line', yAxisIndex: 1, data: records.map((r: any) => r.steps), smooth: true, itemStyle: { color: '#10b981' } },
    ],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  }
})
</script>

<template>
  <el-drawer :model-value="visible" title="健康数据详情" size="600px" @close="handleClose">
    <div v-loading="loading" v-if="detail" class="space-y-5 p-1">
      <!-- Basic Info -->
      <div class="glass-panel rounded-2xl p-5">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-primary-container text-xl">monitor_heart</span>
          <h4 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-sm">基本信息</h4>
        </div>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="宠物">{{ detail.pet?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="类型">{{ detail.pet?.type || '-' }}</el-descriptions-item>
          <el-descriptions-item label="心率">{{ detail.record?.heartRate }} bpm</el-descriptions-item>
          <el-descriptions-item label="睡眠">{{ detail.record?.sleepHours }} hrs</el-descriptions-item>
          <el-descriptions-item label="步数">{{ detail.record?.steps }}</el-descriptions-item>
          <el-descriptions-item label="消耗">{{ detail.record?.calories }} kcal</el-descriptions-item>
          <el-descriptions-item label="体重">{{ detail.record?.weight }} kg</el-descriptions-item>
          <el-descriptions-item label="心情">{{ detail.record?.mood || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- History Table -->
      <div class="glass-panel rounded-2xl p-5">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-primary-container text-xl">history</span>
          <h4 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-sm">历史记录</h4>
        </div>
        <el-table :data="detail.recentRecords || []" stripe size="small" max-height="200">
          <el-table-column prop="date" label="日期" width="100" />
          <el-table-column prop="heartRate" label="心率" width="60" />
          <el-table-column prop="steps" label="步数" width="60" />
          <el-table-column prop="calories" label="消耗" width="60" />
          <el-table-column prop="weight" label="体重" width="60" />
        </el-table>
      </div>

      <!-- Trend Chart -->
      <div class="glass-panel rounded-2xl p-5">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-primary-container text-xl">show_chart</span>
          <h4 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-sm">趋势图</h4>
        </div>
        <v-chart :option="chartOption" autoresize style="height: 250px" />
      </div>
    </div>
  </el-drawer>
</template>
