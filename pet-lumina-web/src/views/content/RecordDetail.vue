<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

const recordData = ref({
  id: route.params.id,
  title: '布丁的日常饮食',
  date: '2023年10月24日 08:30',
  location: '上海·静安中心',
  fullLocation: '上海市静安区静安嘉里中心 T1-802室',
  type: 'feeding',
  content: [
    '今天的早餐为布丁准备了新鲜的三文鱼片搭配自制的有机鸡肉糜。布丁的表现非常兴奋，进食速度适中，大约在5分钟内完成了全部进食。餐后状态良好，眼神清亮，已经开始在客厅追逐它的羽毛玩具了。',
    '注意事项：由于最近天气转凉，在鸡肉糜中稍微拌入了一些温开水以保证它的水分摄入和胃部舒适度。未见软便现象，毛色在充足的Omega-3摄入下保持了极佳的光泽度。',
  ],
  images: ['https://images.unsplash.com/photo-1589924691995-400dc9ecc119?w=800&h=500&fit=crop'],
  tags: ['饮食健康', '每日早餐', '布丁专属', 'Omega-3补充'],
  pet: {
    name: '布丁 (Pudding)',
    breed: '英国短毛猫',
    age: '2岁',
    weight: '4.8 kg',
    healthScore: 98,
  },
  stats: {
    weeklyCalories: '2,450kcal',
    dailyWater: '180ml',
  },
  comments: [
    { id: 1, author: '宠物营养师·林先生', time: '2小时前', content: '非常科学的喂养方案，三文鱼的摄入对英短的毛发健康非常有益，建议观察其对鸡肉的耐受性。' },
    { id: 2, author: '管理员·陈主管', time: '5小时前', content: '请将此类高蛋白饮食记录同步至其健康档案中。' },
  ],
})

const typeConfig: Record<string, { label: string; icon: string; bg: string; color: string }> = {
  feeding: { label: '饮食记录', icon: 'restaurant', bg: 'bg-orange-50', color: 'text-orange-600' },
  walking: { label: '运动记录', icon: 'directions_run', bg: 'bg-blue-50', color: 'text-blue-600' },
  grooming: { label: '美容记录', icon: 'content_cut', bg: 'bg-pink-50', color: 'text-pink-600' },
  medical: { label: '医疗记录', icon: 'medical_services', bg: 'bg-red-50', color: 'text-red-600' },
}

onMounted(async () => {
  loading.value = true
  try { /* const res = await logApi.getDetail(route.params.id) */ } catch (e) { console.error(e) } finally { loading.value = false }
})
</script>

<template>
  <div v-loading="loading" class="space-y-6">
    <!-- Header -->
    <div class="flex items-center gap-6 animate-float-up">
      <button
        class="flex items-center justify-center w-10 h-10 rounded-full glass-panel text-primary transition-all duration-300 active:scale-95"
        @click="router.push('/log')"
      >
        <span class="material-symbols-outlined">arrow_back</span>
      </button>
      <div>
        <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">记录详情</h2>
        <p class="text-xs text-slate-500 font-[Plus_Jakarta_Sans]">Record ID: #{{ recordData.id }}</p>
      </div>
    </div>

    <!-- Breadcrumbs -->
    <div class="flex items-center gap-2 text-sm text-slate-500 animate-float-up" style="animation-delay: 0.05s">
      <span>宠物动态</span>
      <span class="material-symbols-outlined text-xs">chevron_right</span>
      <span>生活记录</span>
      <span class="material-symbols-outlined text-xs">chevron_right</span>
      <span class="text-primary font-bold">{{ recordData.title }}</span>
    </div>

    <!-- Main Content -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
      <!-- Content Section (Left) -->
      <div class="lg:col-span-8 space-y-6">
        <!-- Detail Article -->
        <article class="glass-panel-deep rounded-[32px] p-8 depth-2 animate-float-up stagger-1">
          <div class="flex justify-between items-start mb-8">
            <div>
              <h1 class="font-[Plus_Jakarta_Sans] text-3xl font-bold text-on-surface mb-3">{{ recordData.title }}</h1>
              <div class="flex items-center gap-4">
                <div class="flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full border border-primary/20">
                  <span class="material-symbols-outlined text-sm">schedule</span>
                  <span class="text-xs font-bold">{{ recordData.date }}</span>
                </div>
                <div class="flex items-center gap-2 px-3 py-1 bg-secondary/10 text-secondary rounded-full border border-secondary/20">
                  <span class="material-symbols-outlined text-sm">location_on</span>
                  <span class="text-xs font-bold">{{ recordData.location }}</span>
                </div>
              </div>
            </div>
            <div class="flex gap-2">
              <button class="p-2 rounded-xl glass-panel text-slate-500 hover:text-primary transition-colors">
                <span class="material-symbols-outlined">share</span>
              </button>
              <button class="p-2 rounded-xl glass-panel text-slate-500 hover:text-error transition-colors">
                <span class="material-symbols-outlined">delete</span>
              </button>
            </div>
          </div>

          <!-- Media Gallery -->
          <div class="relative rounded-2xl overflow-hidden aspect-[16/9] mb-8 group">
            <img :src="recordData.images[0]" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
            <div class="absolute bottom-4 right-4 flex gap-2">
              <span class="px-3 py-1.5 bg-black/40 backdrop-blur-md text-white text-xs rounded-full border border-white/20">1 / {{ recordData.images.length }} Photos</span>
            </div>
          </div>

          <!-- Content Text -->
          <div class="space-y-4 mb-10">
            <p v-for="(para, i) in recordData.content" :key="i" class="text-base text-on-surface/80 leading-relaxed">{{ para }}</p>
          </div>

          <!-- Tags -->
          <div class="border-t border-white/20 pt-8">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest flex items-center gap-2">
                <span class="material-symbols-outlined text-lg">sell</span>
                分类标签
              </h3>
              <button class="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-xl shadow-lg shadow-primary/20 hover:scale-[1.05] transition-all duration-300 text-xs font-bold">
                <span class="material-symbols-outlined text-sm">add</span>
                新增标签
              </button>
            </div>
            <div class="flex flex-wrap gap-2">
              <span v-for="tag in recordData.tags" :key="tag" class="px-4 py-2 glass-panel rounded-xl text-primary font-bold text-sm"># {{ tag }}</span>
            </div>
          </div>
        </article>

        <!-- Comments Section -->
        <div class="glass-panel-deep rounded-[32px] p-8 depth-2 animate-float-up stagger-2">
          <h3 class="font-[Plus_Jakarta_Sans] text-xl font-bold mb-6">评论记录 ({{ recordData.comments.length }})</h3>
          <div class="space-y-6">
            <div v-for="comment in recordData.comments" :key="comment.id" class="flex gap-4 p-4 rounded-2xl bg-white/10">
              <div class="w-12 h-12 rounded-full bg-gradient-to-br from-primary-container to-primary flex items-center justify-center text-white text-lg font-bold font-[Plus_Jakarta_Sans] shrink-0">
                {{ comment.author.charAt(0) }}
              </div>
              <div class="flex-1">
                <div class="flex justify-between items-center mb-1">
                  <p class="font-bold text-primary">{{ comment.author }}</p>
                  <span class="text-xs text-slate-400">{{ comment.time }}</span>
                </div>
                <p class="text-on-surface/70 text-sm">{{ comment.content }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Info Section (Right) -->
      <div class="lg:col-span-4 space-y-6">
        <!-- Pet Quick Info -->
        <div class="glass-panel-deep rounded-[32px] p-6 text-center depth-2 animate-float-up stagger-2">
          <div class="relative w-32 h-32 mx-auto mb-4">
            <div class="absolute inset-0 rounded-full bg-gradient-to-tr from-primary to-primary-fixed animate-pulse" />
            <div class="relative z-10 w-full h-full rounded-full border-4 border-white/50 bg-gradient-to-br from-primary-container to-primary flex items-center justify-center text-white text-4xl font-bold font-[Plus_Jakarta_Sans]">
              {{ recordData.pet.name.charAt(0) }}
            </div>
          </div>
          <h2 class="font-[Plus_Jakarta_Sans] text-xl font-bold text-on-surface mb-1">{{ recordData.pet.name }}</h2>
          <p class="text-primary font-bold mb-4">{{ recordData.pet.breed }} · {{ recordData.pet.age }}</p>
          <div class="grid grid-cols-2 gap-3 text-left">
            <div class="p-3 rounded-2xl bg-white/20 border border-white/30">
              <p class="text-[10px] text-slate-500 uppercase font-bold">当前体重</p>
              <p class="font-[Plus_Jakarta_Sans] text-lg font-bold text-primary">{{ recordData.pet.weight }}</p>
            </div>
            <div class="p-3 rounded-2xl bg-white/20 border border-white/30">
              <p class="text-[10px] text-slate-500 uppercase font-bold">健康评分</p>
              <p class="font-[Plus_Jakarta_Sans] text-lg font-bold text-secondary">{{ recordData.pet.healthScore }}%</p>
            </div>
          </div>
          <button class="w-full mt-6 py-3 rounded-2xl bg-white/30 border border-white/50 text-on-surface font-bold hover:bg-white/50 transition-all">
            查看健康报告
          </button>
        </div>

        <!-- Statistics Bento -->
        <div class="glass-panel-deep rounded-[32px] p-6 depth-2 animate-float-up stagger-3">
          <h3 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-lg">analytics</span>
            喂养历史统计
          </h3>
          <div class="space-y-4">
            <div class="flex items-center justify-between p-4 rounded-2xl bg-white/10 hover:bg-white/20 transition-all">
              <div class="flex items-center gap-3">
                <div class="p-2 bg-primary-container rounded-lg">
                  <span class="material-symbols-outlined text-white text-lg">restaurant</span>
                </div>
                <div>
                  <p class="text-sm font-bold">本周总热量</p>
                  <p class="text-xs text-slate-500">摄入总量趋势</p>
                </div>
              </div>
              <p class="font-[Plus_Jakarta_Sans] text-lg font-bold text-primary">{{ recordData.stats.weeklyCalories }}</p>
            </div>
            <div class="flex items-center justify-between p-4 rounded-2xl bg-white/10 hover:bg-white/20 transition-all">
              <div class="flex items-center gap-3">
                <div class="p-2 bg-primary rounded-lg">
                  <span class="material-symbols-outlined text-white text-lg">water_drop</span>
                </div>
                <div>
                  <p class="text-sm font-bold">饮水记录</p>
                  <p class="text-xs text-slate-500">日均摄入量</p>
                </div>
              </div>
              <p class="font-[Plus_Jakarta_Sans] text-lg font-bold text-primary">{{ recordData.stats.dailyWater }}</p>
            </div>
          </div>
        </div>

        <!-- Location Insight -->
        <div class="glass-panel-deep rounded-[32px] p-6 overflow-hidden depth-2 animate-float-up stagger-4">
          <h3 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-4">记录位置</h3>
          <div class="rounded-2xl h-40 bg-slate-200 overflow-hidden relative">
            <div class="w-full h-full bg-gradient-to-br from-primary-container/20 to-primary/10" />
            <div class="absolute inset-0 bg-gradient-to-t from-white/40 to-transparent" />
            <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
              <span class="material-symbols-outlined text-4xl text-primary" style="font-variation-settings: 'FILL' 1">location_on</span>
            </div>
          </div>
          <p class="mt-3 text-xs text-center text-slate-500 italic">{{ recordData.fullLocation }}</p>
        </div>
      </div>
    </div>

    <!-- FAB for Export -->
    <button class="fab animate-scale-in" style="animation-delay: 0.6s">
      <span class="material-symbols-outlined text-[28px]">print</span>
    </button>
  </div>
</template>
