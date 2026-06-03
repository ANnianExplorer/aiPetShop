<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { theme } from './echarts'

const props = defineProps<{
  data: { name: string; value: number }[]
  height?: string
  innerRadius?: string
  outerRadius?: string
}>()

const option = computed(() => ({
  tooltip: { trigger: 'item', ...theme.tooltip },
  legend: {
    orient: 'vertical',
    left: 'left',
    textStyle: { fontFamily: theme.bodyFont, fontSize: 12, color: theme.textColor },
  },
  series: [{
    type: 'pie',
    radius: [props.innerRadius || '40%', props.outerRadius || '70%'],
    avoidLabelOverlap: false,
    itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 3 },
    label: { show: false },
    emphasis: {
      label: { show: true, fontSize: 14, fontWeight: 'bold', fontFamily: theme.fontFamily },
      itemStyle: { shadowBlur: 20, shadowOffsetX: 0, shadowColor: 'rgba(109,175,146,0.3)' },
    },
    data: props.data,
    color: theme.palette,
  }],
}))
</script>

<template>
  <v-chart :option="option" autoresize :style="{ height: height || '240px', width: '100%' }" />
</template>
