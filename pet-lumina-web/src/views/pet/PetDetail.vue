<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { petApi } from '@/api/pet'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

const petData = ref({
  id: Number(route.params.id),
  name: 'Mochi',
  breed: '金毛寻回犬',
  type: '狗',
  gender: '公',
  age: '3岁',
  weight: '28.5',
  birthday: '2021.05.12',
  immunizationStatus: '已完成',
  healthScore: 96,
  owner: { name: '李晓芸', phone: '138 **** 9012', email: 'xiaoyun.l@pet.com' },
  healthHistory: [
    { id: 1, icon: 'vaccines', title: '年度核心疫苗接种', date: '2023年11月24日 · 宠物医院总店', status: '已入库', statusType: 'success' },
    { id: 2, icon: 'cleaning_services', title: '全身美容清洁', date: '2023年10月15日 · 悦享宠物会所', status: '已入库', statusType: 'success' },
    { id: 3, icon: 'health_and_safety', title: '驱虫护理 (内外同驱)', date: '2023年09月05日 · 家庭护理', status: '已入库', statusType: 'success' },
  ],
  weeklyActivity: [
    { day: 'Mon', value: 60 }, { day: 'Tue', value: 45 }, { day: 'Wed', value: 85 },
    { day: 'Thu', value: 30 }, { day: 'Fri', value: 55 }, { day: 'Sat', value: 70 }, { day: 'Sun', value: 40 },
  ],
  adminNotes: '"Mochi对鸡肉有过敏倾向，建议饮食中避开相关成分。性格非常温顺，在疫苗接种期间表现极佳。建议下次到店时间：2024年2月。"',
})

onMounted(async () => {
  loading.value = true
  try { /* const res = await petApi.getDetail(route.params.id as string) */ } catch (e) { console.error(e) } finally { loading.value = false }
})

const goBack = () => router.push('/pet')
const handleEdit = () => router.push(`/pet/edit/${petData.value.id}`)
const viewAllHealth = () => router.push({ path: '/health', query: { petId: String(petData.value.id) } })
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除宠物「${petData.value.name}」吗？`, '确认删除', { type: 'error' })
    ElMessage.success('删除成功')
    router.push('/pet')
  } catch {}
}
const maxActivity = Math.max(...petData.value.weeklyActivity.map(a => a.value))
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="flex items-center justify-between animate-float-up">
      <div class="flex items-center gap-4">
        <button class="glass-panel rounded-full w-10 h-10 flex items-center justify-center btn-jelly" @click="goBack">
          <span class="material-symbols-outlined text-on-surface-variant">arrow_back</span>
        </button>
        <h1 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">宠物详情</h1>
      </div>
      <div class="flex items-center gap-3">
        <button @click="handleEdit" class="flex items-center gap-2 px-5 py-2.5 rounded-full bg-primary text-white btn-jelly shadow-lg shadow-primary/20 text-sm font-bold">
          <span class="material-symbols-outlined text-lg">edit</span>编辑信息
        </button>
        <button @click="handleDelete" class="w-11 h-11 flex items-center justify-center rounded-full bg-error-container text-error btn-jelly">
          <span class="material-symbols-outlined">delete</span>
        </button>
      </div>
    </div>

    <!-- Main Grid -->
    <div class="grid grid-cols-12 gap-6">
      <!-- Left Column -->
      <div class="col-span-12 lg:col-span-8 space-y-6">
        <!-- Hero -->
        <div class="glass-panel-deep rounded-[32px] overflow-hidden depth-3 animate-float-up stagger-1 relative group">
          <div class="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent z-10" />
          <div class="h-[400px] bg-gradient-to-br from-primary-container/30 via-primary/10 to-secondary-container/20 flex items-center justify-center relative overflow-hidden">
            <span class="material-symbols-outlined text-white/20" style="font-size: 200px">pets</span>
            <div class="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
            <div class="absolute bottom-8 left-10 z-20 text-white">
              <div class="flex items-center gap-4 mb-2">
                <h1 class="font-[Plus_Jakarta_Sans] text-[40px] font-bold drop-shadow-lg">{{ petData.name }}</h1>
                <span class="px-4 py-1 rounded-full bg-primary-container text-xs font-bold uppercase tracking-widest shadow-lg animate-badge-pop">Premium Member</span>
              </div>
              <p class="text-white/90 text-lg">{{ petData.breed }} · {{ petData.age }} · {{ petData.gender }}</p>
            </div>
          </div>
        </div>

        <!-- Bento Info Cards -->
        <div class="grid grid-cols-3 gap-4">
          <div class="glass-panel p-5 rounded-[24px] flex flex-col items-center text-center depth-1 animate-float-up stagger-2">
            <span class="material-symbols-outlined text-primary text-3xl mb-3 glow-icon">monitor_weight</span>
            <span class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold mb-1">当前体重</span>
            <span class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">{{ petData.weight }} kg</span>
          </div>
          <div class="glass-panel p-5 rounded-[24px] flex flex-col items-center text-center depth-1 animate-float-up stagger-3 border-t-2 border-l-2 border-white/40">
            <span class="material-symbols-outlined text-primary text-3xl mb-3 glow-icon">cake</span>
            <span class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold mb-1">生日</span>
            <span class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">{{ petData.birthday }}</span>
          </div>
          <div class="glass-panel p-5 rounded-[24px] flex flex-col items-center text-center depth-1 animate-float-up stagger-4">
            <span class="material-symbols-outlined text-primary text-3xl mb-3 glow-icon">medical_services</span>
            <span class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold mb-1">免疫状态</span>
            <span class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-primary">{{ petData.immunizationStatus }}</span>
          </div>
        </div>

        <!-- Health History -->
        <div class="glass-panel rounded-[32px] p-8 depth-2 animate-float-up stagger-5">
          <div class="flex justify-between items-center mb-6">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-primary glow-icon">history</span>
              <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface text-lg">健康记录</h3>
            </div>
            <button @click="viewAllHealth" class="text-primary text-sm font-semibold hover:underline">查看全部</button>
          </div>
          <div class="space-y-3">
            <div v-for="record in petData.healthHistory" :key="record.id"
              class="flex items-center justify-between p-4 rounded-2xl bg-white/20 hover:bg-white/30 transition-all group/item">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-xl bg-secondary-container flex items-center justify-center text-primary group-hover/item:scale-110 transition-transform">
                  <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">{{ record.icon }}</span>
                </div>
                <div>
                  <p class="font-bold text-on-surface text-sm">{{ record.title }}</p>
                  <p class="text-xs text-slate-500">{{ record.date }}</p>
                </div>
              </div>
              <span class="px-4 py-1.5 rounded-full bg-primary/10 text-primary text-xs font-bold">已入库</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column -->
      <div class="col-span-12 lg:col-span-4 space-y-6">
        <!-- Owner Info -->
        <div class="glass-panel rounded-[32px] p-8 depth-2 animate-float-up stagger-2">
          <h4 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-6">主人信息</h4>
          <div class="flex flex-col items-center text-center">
            <div class="w-24 h-24 rounded-full border-4 border-white/60 mb-4 shadow-xl bg-gradient-to-br from-primary-container to-primary flex items-center justify-center text-white text-3xl font-bold font-[Plus_Jakarta_Sans]">
              {{ petData.owner.name.charAt(0) }}
            </div>
            <p class="font-[Plus_Jakarta_Sans] font-bold text-lg text-on-surface">{{ petData.owner.name }}</p>
            <p class="text-slate-500 mb-6">超级会员</p>
            <div class="w-full space-y-3">
              <div class="flex items-center justify-between px-4 py-3 rounded-xl bg-white/20">
                <span class="material-symbols-outlined text-primary text-sm">call</span>
                <span class="text-sm font-medium">{{ petData.owner.phone }}</span>
              </div>
              <div class="flex items-center justify-between px-4 py-3 rounded-xl bg-white/20">
                <span class="material-symbols-outlined text-primary text-sm">mail</span>
                <span class="text-sm font-medium">{{ petData.owner.email }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Activity Chart -->
        <div class="glass-panel rounded-[32px] p-8 depth-2 animate-float-up stagger-3">
          <h4 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-6">活跃度分析</h4>
          <div class="h-48 flex items-end justify-between gap-2 px-2">
            <div v-for="(item, i) in petData.weeklyActivity" :key="item.day"
              class="w-full rounded-t-lg relative group/bar transition-all duration-500"
              :class="i === 2 ? 'bg-primary/40' : 'bg-primary/20 hover:bg-primary/40'"
              :style="{ height: `${(item.value / maxActivity) * 100}%` }">
              <div v-if="i === 2" class="absolute -top-8 left-1/2 -translate-x-1/2 text-xs font-bold text-primary">8.5h</div>
            </div>
          </div>
          <div class="flex justify-between mt-4 text-[10px] text-slate-400 font-bold uppercase tracking-tighter">
            <span v-for="item in petData.weeklyActivity" :key="item.day" :class="{ 'text-primary font-black': item.day === 'Wed' }">{{ item.day }}</span>
          </div>
        </div>

        <!-- Admin Notes -->
        <div class="glass-panel rounded-[32px] p-8 depth-2 animate-float-up stagger-4">
          <div class="flex items-center gap-2 mb-4">
            <span class="material-symbols-outlined text-primary text-sm">edit_note</span>
            <h4 class="text-xs text-slate-500 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">管理员备注</h4>
          </div>
          <p class="text-sm text-on-surface-variant leading-relaxed italic">{{ petData.adminNotes }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
