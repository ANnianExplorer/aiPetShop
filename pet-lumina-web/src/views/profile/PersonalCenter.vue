<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const profile = ref({
  name: 'Admin User',
  role: 'Super Admin',
  bio: '负责 PetLumina 全平台宠物健康管理与设施调度系统的最高决策管理，拥有最高系统访问权限。',
  email: 'admin@petlumina.com',
  phone: '+86 138-0000-0000',
  joinDate: '2023.05.12',
  securityScore: 98,
  twoFA: true,
})

const loginHistory = ref([
  { id: 1, time: '今天 14:23:12', device: 'MacBook Pro / Chrome', ip: '192.168.1.105', location: '中国, 上海', status: 'current' },
  { id: 2, time: '昨日 09:45:01', device: 'iPhone 15 Pro / App', ip: '112.64.12.89', location: '中国, 北京', status: 'success' },
  { id: 3, time: '2024.03.18 21:12:44', device: 'Surface Book / Edge', ip: '210.13.44.112', location: '中国, 杭州', status: 'success' },
])

const statCards = [
  { label: '累计管理时长', value: '1,280', unit: '小时', icon: 'analytics', color: 'primary' },
  { label: '已完成任务', value: '342', unit: '件', icon: 'task_alt', color: 'secondary' },
  { label: '接入设施数', value: '18', unit: '个中心', icon: 'hub', color: 'tertiary' },
]
</script>

<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center animate-float-up">
      <div class="flex items-center gap-4">
        <button class="w-10 h-10 rounded-full glass-panel flex items-center justify-center hover:bg-white/50 transition-all" @click="router.back()">
          <span class="material-symbols-outlined text-primary">arrow_back</span>
        </button>
        <div>
          <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">个人中心</h2>
          <p class="text-sm text-on-surface-variant">管理您的账户信息与安全配置</p>
        </div>
      </div>
    </div>

    <!-- Bento Grid Layout -->
    <div class="grid grid-cols-12 gap-6">
      <!-- Main Profile Card -->
      <div class="col-span-12 lg:col-span-8 glass-panel-deep rounded-[32px] p-8 relative overflow-hidden group depth-2 animate-float-up stagger-1">
        <div class="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -mr-32 -mt-32 transition-all group-hover:bg-primary/10" />
        <div class="relative z-10 flex flex-col md:flex-row gap-8 items-start md:items-center">
          <div class="relative">
            <div class="w-32 h-32 rounded-3xl overflow-hidden border-4 border-white shadow-xl bg-gradient-to-br from-primary-container to-primary flex items-center justify-center text-white text-5xl font-bold font-[Plus_Jakarta_Sans]">
              {{ profile.name.charAt(0) }}
            </div>
            <button class="absolute -bottom-2 -right-2 w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center shadow-lg hover:scale-110 transition-transform">
              <span class="material-symbols-outlined text-sm">photo_camera</span>
            </button>
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">{{ profile.name }}</h3>
              <span class="px-3 py-1 bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-widest rounded-full border border-primary/20">{{ profile.role }}</span>
            </div>
            <p class="text-on-surface-variant text-sm mb-6 max-w-lg">{{ profile.bio }}</p>
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-6">
              <div>
                <p class="text-xs text-slate-400 uppercase tracking-tighter mb-1">电子邮箱</p>
                <p class="font-semibold text-on-surface text-sm">{{ profile.email }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-400 uppercase tracking-tighter mb-1">手机号码</p>
                <p class="font-semibold text-on-surface text-sm">{{ profile.phone }}</p>
              </div>
              <div>
                <p class="text-xs text-slate-400 uppercase tracking-tighter mb-1">入职时间</p>
                <p class="font-semibold text-on-surface text-sm">{{ profile.joinDate }}</p>
              </div>
            </div>
          </div>
        </div>
        <div class="mt-6 pt-8 border-t border-white/30 flex gap-4 relative z-10">
          <button class="px-6 py-3 bg-primary text-white rounded-xl font-semibold flex items-center gap-2 hover:opacity-90 transition-opacity text-sm btn-jelly">
            <span class="material-symbols-outlined text-sm">edit</span>
            编辑资料
          </button>
          <button class="px-6 py-3 glass-panel text-primary border-primary/20 rounded-xl font-semibold hover:bg-white/60 transition-all text-sm">
            导出档案
          </button>
        </div>
      </div>

      <!-- Security Quick Actions -->
      <div class="col-span-12 lg:col-span-4 space-y-6 animate-float-up stagger-2">
        <div class="glass-panel-deep rounded-[32px] p-8 depth-2">
          <h4 class="font-[Plus_Jakarta_Sans] text-lg font-bold mb-4 flex items-center gap-2">
            <span class="material-symbols-outlined text-primary" style="font-variation-settings: 'FILL' 1">verified_user</span>
            安全设置
          </h4>
          <div class="space-y-3">
            <div class="flex justify-between items-center p-4 rounded-2xl bg-white/30 hover:bg-white/50 transition-colors cursor-pointer group">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-slate-400 group-hover:text-primary transition-colors">lock</span>
                <span class="text-sm font-medium">修改登录密码</span>
              </div>
              <span class="material-symbols-outlined text-slate-300 text-sm">chevron_right</span>
            </div>
            <div class="flex justify-between items-center p-4 rounded-2xl bg-white/30 hover:bg-white/50 transition-colors cursor-pointer group">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-slate-400 group-hover:text-primary transition-colors">phonelink_lock</span>
                <span class="text-sm font-medium">双重身份验证 (2FA)</span>
              </div>
              <span class="text-[10px] font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">已开启</span>
            </div>
            <div class="flex justify-between items-center p-4 rounded-2xl bg-white/30 hover:bg-white/50 transition-colors cursor-pointer group">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-slate-400 group-hover:text-primary transition-colors">shield</span>
                <span class="text-sm font-medium">操作日志审计</span>
              </div>
              <span class="material-symbols-outlined text-slate-300 text-sm">chevron_right</span>
            </div>
          </div>
        </div>

        <!-- Security Score -->
        <div class="glass-panel-deep rounded-[32px] p-8 bg-gradient-to-br from-primary/10 to-transparent depth-2">
          <div class="flex justify-between items-start mb-4">
            <div>
              <h4 class="font-bold text-on-surface">账号安全评分</h4>
              <p class="text-xs text-on-surface-variant">您的账户目前非常安全</p>
            </div>
            <span class="text-3xl font-black text-primary font-[Plus_Jakarta_Sans]">{{ profile.securityScore }}</span>
          </div>
          <div class="w-full bg-white/40 h-2 rounded-full overflow-hidden">
            <div class="bg-primary h-full shadow-[0_0_10px_#6DAF92] transition-all duration-1000" :style="{ width: `${profile.securityScore}%` }" />
          </div>
        </div>
      </div>

      <!-- Login History -->
      <div class="col-span-12 glass-panel-deep rounded-[32px] p-8 depth-2 animate-float-up stagger-3">
        <div class="flex justify-between items-center mb-6">
          <h4 class="font-[Plus_Jakarta_Sans] text-xl font-bold flex items-center gap-2">
            <span class="material-symbols-outlined text-primary">history</span>
            登录历史
          </h4>
          <button class="text-primary text-sm font-semibold hover:underline">查看全部日志</button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left">
            <thead>
              <tr class="border-b border-white/20">
                <th class="pb-4 text-xs text-slate-400 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">时间</th>
                <th class="pb-4 text-xs text-slate-400 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">设备 / 浏览器</th>
                <th class="pb-4 text-xs text-slate-400 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">IP 地址</th>
                <th class="pb-4 text-xs text-slate-400 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">地理位置</th>
                <th class="pb-4 text-xs text-slate-400 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest text-right">状态</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-white/10">
              <tr v-for="log in loginHistory" :key="log.id" class="hover:bg-white/20 transition-colors">
                <td class="py-4 text-sm">{{ log.time }}</td>
                <td class="py-4">
                  <div class="flex items-center gap-2">
                    <span class="material-symbols-outlined text-slate-400 text-lg">
                      {{ log.device.includes('MacBook') ? 'laptop_mac' : log.device.includes('iPhone') ? 'smartphone' : 'laptop_windows' }}
                    </span>
                    <span class="text-sm">{{ log.device }}</span>
                  </div>
                </td>
                <td class="py-4 text-sm font-[Plus_Jakarta_Sans]">{{ log.ip }}</td>
                <td class="py-4 text-sm">{{ log.location }}</td>
                <td class="py-4 text-right">
                  <span v-if="log.status === 'current'" class="inline-flex items-center gap-1.5 text-[11px] font-bold text-primary">
                    <span class="w-1.5 h-1.5 bg-primary rounded-full" />
                    当前会话
                  </span>
                  <span v-else class="text-[11px] font-bold text-slate-500 bg-slate-100/50 px-2 py-0.5 rounded">成功登录</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Stat Mini Cards -->
      <div v-for="(stat, i) in statCards" :key="i" class="col-span-12 md:col-span-4 glass-panel-deep rounded-[32px] p-6 depth-2 animate-float-up" :style="{ animationDelay: `${0.4 + i * 0.06}s` }">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-2xl flex items-center justify-center"
            :class="stat.color === 'primary' ? 'bg-primary/20 text-primary' : stat.color === 'secondary' ? 'bg-secondary/20 text-secondary' : 'bg-tertiary-container/20 text-tertiary'"
          >
            <span class="material-symbols-outlined">{{ stat.icon }}</span>
          </div>
          <div>
            <p class="text-xs text-slate-500 font-bold uppercase tracking-widest">{{ stat.label }}</p>
            <h5 class="text-2xl font-black text-on-surface font-[Plus_Jakarta_Sans]">{{ stat.value }} <span class="text-sm font-normal">{{ stat.unit }}</span></h5>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
