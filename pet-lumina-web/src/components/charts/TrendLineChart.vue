<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { theme } from './echarts'

const props = defineProps<{
  data: { label: string; value: number }[]
  height?: string
  color?: string
  smooth?: boolean
  showArea?: boolean
}>()

const option = computed(() => ({
  tooltip: { trigger: 'axis', ...theme.tooltip },
  xAxis: {
    type: 'category',
    data: props.data.map(i => i.label),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: theme.textColor, fontFamily: theme.fontFamily, fontSize: 11 },
  },
  yAxis: {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: theme.splitLine } },
    axisLabel: { color: theme.textColor, fontFamily: theme.fontFamily, fontSize: 11 },
  },
  series: [{
    data: props.data.map(i => i.value),
    type: 'line',
    smooth: props.smooth ?? true,
    symbol: 'circle',
    symbolSize: 8,
    lineStyle: { color: props.color || theme.primary, width: 3 },
    itemStyle: { color: props.color || theme.primary, borderColor: '#fff', borderWidth: 2 },
    ...(props.showArea !== false ? {
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: `${props.color || theme.primary}4D` },
            { offset: 1, color: `${props.color || theme.primary}05` },
          ],
        },
      },
    } : {}),
  }],
  grid: { left: '3%', right: '4%', bottom: '3%', top: '8%', containLabel: true },
}))
</script>

<template>
  <v-chart :option="option" autoresize :style="{ height: height || '300px' }" />
</template>
