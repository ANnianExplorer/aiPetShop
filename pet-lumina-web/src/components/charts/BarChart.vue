<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { theme } from './echarts'

const props = defineProps<{
  data: { label: string; value: number }[]
  height?: string
  color?: string
  horizontal?: boolean
}>()

const option = computed(() => {
  const categoryAxis = {
    type: 'category',
    data: props.data.map(i => i.label),
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: theme.textColor, fontFamily: theme.fontFamily, fontSize: 11 },
  }
  const valueAxis = {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: theme.splitLine } },
    axisLabel: { color: theme.textColor, fontFamily: theme.fontFamily, fontSize: 11 },
  }

  return {
    tooltip: { trigger: 'axis', ...theme.tooltip },
    xAxis: props.horizontal ? valueAxis : categoryAxis,
    yAxis: props.horizontal ? categoryAxis : valueAxis,
    series: [{
      data: props.data.map(i => i.value),
      type: 'bar',
      barWidth: '60%',
      itemStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: props.horizontal ? 1 : 0, y2: props.horizontal ? 0 : 1,
          colorStops: [
            { offset: 0, color: props.color || theme.primary },
            { offset: 1, color: `${props.color || theme.primary}80` },
          ],
        },
        borderRadius: props.horizontal ? [0, 6, 6, 0] : [6, 6, 0, 0],
      },
    }],
    grid: { left: '3%', right: '4%', bottom: '3%', top: '8%', containLabel: true },
  }
})
</script>

<template>
  <v-chart :option="option" autoresize :style="{ height: height || '300px' }" />
</template>
