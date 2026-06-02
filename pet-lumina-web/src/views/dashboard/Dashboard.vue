<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { dashboardApi } from '@/api/dashboard'
import type { DashboardStats } from '@/types'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'

use([CanvasRenderer, LineChart, PieChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

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
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: stats.value.activeUserTrend.map(i => i.date) },
    yAxis: { type: 'value' },
    series: [{ data: stats.value.activeUserTrend.map(i => i.count), type: 'line', smooth: true, areaStyle: { opacity: 0.1 }, itemStyle: { color: '#10b981' } }],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  }
  const pieData = Object.entries(stats.value.petTypeDistribution).map(([name, value]) => ({ name, value }))
  pieOption.value = {
    tooltip: { trigger: 'item' },
    legend: { orient: 'vertical', left: 'left' },
    series: [{
      type: 'pie',
      radius: '50%',
      data: pieData,
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' } },
    }],
  }
}

onMounted(() => { setTimeout(updateCharts, 100) })
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <!-- Stat Cards -->
    <div class="stat-cards">
      <div class="glass-card rounded-2xl p-6 stat-card">
        <div class="stat-icon-wrapper bg-emerald-500/15">
          <span class="material-symbols-outlined text-emerald-500 text-2xl">group</span>
        </div>
        <div class="stat-number font-[Plus_Jakarta_Sans]">{{ stats?.userTotal ?? 0 }}</div>
        <div class="stat-label">用户总数</div>
      </div>
      <div class="glass-card rounded-2xl p-6 stat-card">
        <div class="stat-icon-wrapper bg-sky-500/15">
          <span class="material-symbols-outlined text-sky-500 text-2xl">pets</span>
        </div>
        <div class="stat-number font-[Plus_Jakarta_Sans]">{{ stats?.petTotal ?? 0 }}</div>
        <div class="stat-label">宠物总数</div>
      </div>
      <div class="glass-card rounded-2xl p-6 stat-card">
        <div class="stat-icon-wrapper bg-violet-500/15">
          <span class="material-symbols-outlined text-violet-500 text-2xl">article</span>
        </div>
        <div class="stat-number font-[Plus_Jakarta_Sans]">{{ stats?.postTotal ?? 0 }}</div>
        <div class="stat-label">社区帖子</div>
      </div>
      <div class="glass-card rounded-2xl p-6 stat-card">
        <div class="stat-icon-wrapper bg-amber-500/15">
          <span class="material-symbols-outlined text-amber-500 text-2xl">forum</span>
        </div>
        <div class="stat-number font-[Plus_Jakarta_Sans]">{{ stats?.topicTotal ?? 0 }}</div>
        <div class="stat-label">话题数量</div>
      </div>
    </div>

    <!-- Charts -->
    <div class="chart-row">
      <div class="glass-panel rounded-3xl p-6">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-primary-container text-xl">trending_up</span>
          <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface">活跃趋势</h3>
        </div>
        <v-chart :option="lineOption" autoresize style="height: 300px" />
      </div>
      <div class="glass-panel rounded-3xl p-6">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-primary-container text-xl">donut_large</span>
          <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface">宠物类型分布</h3>
        </div>
        <v-chart :option="pieOption" autoresize style="height: 300px" />
      </div>
    </div>

    <!-- Tables -->
    <div class="table-row">
      <div class="glass-panel rounded-3xl p-6">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-primary-container text-xl">local_fire_department</span>
          <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface">热门帖子</h3>
        </div>
        <el-table :data="stats?.hotPosts || []" stripe>
          <el-table-column prop="content" label="内容" show-overflow-tooltip />
          <el-table-column prop="author" label="作者" width="100" />
          <el-table-column prop="likes" label="点赞" width="80" />
          <el-table-column prop="comments" label="评论" width="80" />
        </el-table>
      </div>
      <div class="glass-panel rounded-3xl p-6">
        <div class="flex items-center gap-2 mb-4">
          <span class="material-symbols-outlined text-primary-container text-xl">tag</span>
          <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface">热门话题</h3>
        </div>
        <el-table :data="stats?.hotTopics || []" stripe>
          <el-table-column prop="title" label="话题" show-overflow-tooltip />
          <el-table-column prop="postCount" label="帖子数" width="80" />
          <el-table-column prop="followerCount" label="关注数" width="80" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
}
.stat-icon-wrapper {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.stat-number {
  font-size: 32px;
  font-weight: 800;
  color: var(--color-on-surface);
  line-height: 1;
}
.stat-label {
  font-size: 13px;
  color: var(--color-on-surface-variant);
  margin-top: 2px;
}
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}
.table-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
</style>
