<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { dashboardApi } from '@/api/dashboard'
import type { DashboardStats } from '@/types'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart, BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, PieChart, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const stats = ref<DashboardStats | null>(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    stats.value = await dashboardApi.getStats() as any
  } catch (e) {
    console.error('Failed to fetch stats:', e)
  } finally {
    loading.value = false
  }
})

const lineOption = ref({})
const pieOption = ref({})

const updateCharts = () => {
  if (!stats.value) return
  lineOption.value = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255,255,255,0.9)',
      borderColor: 'rgba(109,175,146,0.2)',
      borderRadius: 12,
      textStyle: { fontFamily: 'Plus Jakarta Sans' }
    },
    xAxis: {
      type: 'category',
      data: stats.value.activeUserTrend.map(i => i.date),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#404944', fontFamily: 'Plus Jakarta Sans', fontSize: 11 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
      axisLabel: { color: '#404944', fontFamily: 'Plus Jakarta Sans', fontSize: 11 }
    },
    series: [{
      data: stats.value.activeUserTrend.map(i => i.count),
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { color: '#6daf92', width: 3 },
      itemStyle: { color: '#6daf92', borderColor: '#fff', borderWidth: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(109,175,146,0.3)' },
            { offset: 1, color: 'rgba(109,175,146,0.02)' }
          ]
        }
      }
    }],
    grid: { left: '3%', right: '4%', bottom: '3%', top: '8%', containLabel: true },
  }
  const pieData = Object.entries(stats.value.petTypeDistribution).map(([name, value]) => ({ name, value }))
  pieOption.value = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.9)',
      borderColor: 'rgba(109,175,146,0.2)',
      borderRadius: 12,
      textStyle: { fontFamily: 'Plus Jakarta Sans' }
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      textStyle: { fontFamily: 'Noto Sans SC', fontSize: 12, color: '#404944' }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      avoidLabelOverlap: false,
      itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 3 },
      label: { show: false },
      emphasis: {
        label: { show: true, fontSize: 14, fontWeight: 'bold', fontFamily: 'Plus Jakarta Sans' },
        itemStyle: { shadowBlur: 20, shadowOffsetX: 0, shadowColor: 'rgba(109,175,146,0.3)' }
      },
      data: pieData,
      color: ['#6daf92', '#91d4b6', '#bcedda', '#3a6758']
    }],
  }
}

onMounted(() => { setTimeout(updateCharts, 100) })

const statCards = [
  { key: 'userTotal', label: '用户总数', icon: 'group', color: 'primary-container', trend: '+12%', trendUp: true },
  { key: 'petTotal', label: '活跃宠物', icon: 'pets', color: 'secondary-container', trend: '+8.4%', trendUp: true },
  { key: 'postTotal', label: '今日动态', icon: 'bolt', color: 'primary-fixed', trend: '-2%', trendUp: false },
  { key: 'topicTotal', label: '新增记录', icon: 'history_edu', color: 'tertiary-container', trend: '+24%', trendUp: true },
]

const recentActivities = [
  { icon: 'add_reaction', iconBg: 'bg-emerald-100', iconColor: 'text-emerald-600', action: '新帖子: "我的金毛学会握手了"', user: '张小伟', time: '10:42 AM', status: '成功', statusClass: 'badge-success' },
  { icon: 'edit_note', iconBg: 'bg-amber-100', iconColor: 'text-amber-600', action: '宠物资料更新', user: '李美美', time: '09:15 AM', status: '待审核', statusClass: 'badge-warning' },
  { icon: 'report_gmailerrorred', iconBg: 'bg-red-100', iconColor: 'text-red-600', action: '可疑评论行为', user: '王大勇', time: '08:02 AM', status: '已拦截', statusClass: 'badge-error' },
]

const getStatValue = (key: string) => {
  if (!stats.value) return 0
  return (stats.value as any)[key] ?? 0
}
</script>

<template>
  <div v-loading="loading">
    <!-- Welcome Header -->
    <div class="mb-10 animate-float-up">
      <h2 class="font-[Plus_Jakarta_Sans] text-[32px] font-bold text-primary mb-2">欢迎回来，管理员！</h2>
      <p class="text-on-surface-variant text-base max-w-2xl">
        这是 PetLumina 今天的运行概况。您的数据实时同步中，当前系统状态：<span class="text-emerald-600 font-bold">运行良好</span>。
      </p>
    </div>

    <!-- Stat Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
      <div
        v-for="(card, index) in statCards"
        :key="card.key"
        class="glass-panel rounded-2xl p-6 depth-1 hover:depth-2 transition-all duration-400 cursor-default animate-float-up relative overflow-hidden group"
        :style="{ animationDelay: `${index * 0.08}s` }"
      >
        <!-- Ambient glow -->
        <div class="absolute top-0 right-0 w-24 h-24 bg-primary/5 rounded-full blur-2xl -mr-8 -mt-8 transition-all group-hover:bg-primary/10" />

        <div class="relative z-10">
          <div class="flex justify-between items-start mb-4">
            <div class="p-3 rounded-xl" :class="{
              'bg-primary-fixed-dim/30': card.color === 'primary-fixed',
              'bg-secondary-container/40': card.color === 'secondary-container',
              'bg-primary-container/20': card.color === 'primary-container',
              'bg-tertiary-container/20': card.color === 'tertiary-container',
            }">
              <span class="material-symbols-outlined text-2xl glow-icon" :class="{
                'text-primary': card.color === 'primary-container' || card.color === 'primary-fixed',
                'text-secondary': card.color === 'secondary-container',
                'text-tertiary': card.color === 'tertiary-container',
              }">{{ card.icon }}</span>
            </div>
            <span class="text-sm font-bold flex items-center gap-1" :class="card.trendUp ? 'text-emerald-600' : 'text-error'">
              <span class="material-symbols-outlined text-base">{{ card.trendUp ? 'trending_up' : 'trending_down' }}</span>
              {{ card.trend }}
            </span>
          </div>
          <p class="text-on-surface-variant text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-1">{{ card.label }}</p>
          <h3 class="font-[Plus_Jakarta_Sans] text-[32px] font-bold text-on-surface animate-number-pop" style="animation-delay: 0.3s">
            {{ getStatValue(card.key).toLocaleString() }}
          </h3>
        </div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-10">
      <!-- Line Chart -->
      <div class="lg:col-span-2 glass-panel rounded-3xl p-6 depth-2 animate-float-up" style="animation-delay: 0.2s">
        <div class="flex justify-between items-center mb-6">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-primary-container text-xl">trending_up</span>
            <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-lg">每周活跃趋势</h3>
          </div>
          <div class="flex gap-2">
            <button class="px-4 py-1.5 rounded-full bg-white/50 text-xs font-[Plus_Jakarta_Sans] font-semibold border border-emerald-100 text-primary hover:bg-primary-fixed-dim transition-all">本周</button>
            <button class="px-4 py-1.5 rounded-full text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant hover:bg-white/40 transition-all">上周</button>
          </div>
        </div>
        <v-chart :option="lineOption" autoresize style="height: 300px" />
      </div>

      <!-- Pie Chart -->
      <div class="glass-panel rounded-3xl p-6 depth-2 animate-float-up flex flex-col" style="animation-delay: 0.3s">
        <div class="flex items-center gap-2 mb-6">
          <span class="material-symbols-outlined text-primary-container text-xl">donut_large</span>
          <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-lg">宠物种类占比</h3>
        </div>
        <div class="flex-1 flex items-center justify-center">
          <v-chart :option="pieOption" autoresize style="height: 240px; width: 100%" />
        </div>
      </div>
    </div>

    <!-- Recent Activity Table -->
    <section class="glass-panel rounded-3xl overflow-hidden depth-2 animate-float-up" style="animation-delay: 0.4s">
      <div class="p-6 flex justify-between items-center border-b border-white/20">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-primary-container text-xl">history</span>
          <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-lg">近期活动</h3>
        </div>
        <button class="text-primary text-sm font-[Plus_Jakarta_Sans] font-semibold flex items-center gap-2 hover:gap-3 transition-all duration-300">
          查看全部 <span class="material-symbols-outlined text-base">arrow_forward</span>
        </button>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left">
          <thead>
            <tr class="text-on-surface-variant">
              <th class="p-5 text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">行为</th>
              <th class="p-5 text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">所属用户</th>
              <th class="p-5 text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">时间</th>
              <th class="p-5 text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">状态</th>
              <th class="p-5 text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(activity, index) in recentActivities" :key="index" class="border-t border-white/10 hover:bg-white/30 transition-colors">
              <td class="p-5">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full flex items-center justify-center" :class="activity.iconBg">
                    <span class="material-symbols-outlined text-lg" :class="activity.iconColor">{{ activity.icon }}</span>
                  </div>
                  <span class="text-sm font-medium">{{ activity.action }}</span>
                </div>
              </td>
              <td class="p-5 text-sm">{{ activity.user }}</td>
              <td class="p-5 text-sm text-on-surface-variant/70">{{ activity.time }}</td>
              <td class="p-5">
                <span class="px-3 py-1 rounded-full text-xs font-bold" :class="activity.statusClass">{{ activity.status }}</span>
              </td>
              <td class="p-5">
                <button class="p-2 hover:bg-emerald-50 rounded-lg transition-all">
                  <span class="material-symbols-outlined text-on-surface-variant">more_vert</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- FAB -->
    <button class="fab animate-scale-in" style="animation-delay: 0.6s">
      <span class="material-symbols-outlined text-[28px]">add</span>
    </button>
  </div>
</template>