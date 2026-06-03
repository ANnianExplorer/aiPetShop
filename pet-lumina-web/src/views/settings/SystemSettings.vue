<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const settings = ref({
  acceleration: true,
  cloudBackup: true,
  aiDiagnosis: false,
  emailNotification: true,
  locationMask: true,
  simpleMode: false,
})

const toggleSetting = (key: keyof typeof settings.value) => {
  settings.value[key] = !settings.value[key]
  ElMessage.success(`${key} 已${settings.value[key] ? '开启' : '关闭'}`)
}

const features = [
  { icon: 'analytics', title: '多维健康分析', desc: '基于神经网络的健康趋势预测与风险预警系统。', color: 'primary' },
  { icon: 'hub', title: '全栈互联生态', desc: '无缝连接智能喂食器、项圈及各类监测终端设备。', color: 'secondary' },
  { icon: 'security', title: '银行级隐私防护', desc: '采用端到端加密技术，确保每一条宠物隐私数据的安全。', color: 'tertiary' },
]
</script>

<template>
  <div class="space-y-10 animate-float-up">
    <!-- Version Card -->
    <div class="glass-panel-deep p-8 rounded-3xl relative overflow-hidden depth-2">
      <div class="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -mr-20 -mt-20" />
      <div class="relative z-10 flex items-center gap-8">
        <div class="w-32 h-32 flex-shrink-0 bg-white/40 rounded-3xl p-4 shadow-xl border border-white/40 flex items-center justify-center">
          <span class="material-symbols-outlined text-6xl text-primary glow-icon" style="font-variation-settings: 'FILL' 1">pets</span>
        </div>
        <div class="space-y-2">
          <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface">PetLumina Pro</h2>
          <p class="text-primary font-bold text-lg">
            版本 v2.4.0
            <span class="ml-2 text-xs font-medium px-2 py-0.5 bg-secondary-container text-on-secondary-container rounded-full uppercase tracking-tighter">Latest</span>
          </p>
          <p class="text-on-surface-variant max-w-2xl leading-relaxed">
            下一代智能宠物生态管理系统。通过融合 AI 数据分析与人性化交互设计，为您提供最专业、最温情的宠物全生命周期管理方案。当前版本已针对大规模并发连接进行了深度优化。
          </p>
        </div>
      </div>
    </div>

    <!-- Feature Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div v-for="(feat, i) in features" :key="i" class="glass-panel p-6 rounded-2xl flex items-start gap-4 depth-1 hover:depth-2 transition-all animate-float-up" :style="{ animationDelay: `${0.1 + i * 0.06}s` }">
        <div class="w-12 h-12 rounded-xl flex items-center justify-center"
          :class="feat.color === 'primary' ? 'bg-primary-container/20 text-primary' : feat.color === 'secondary' ? 'bg-secondary-container/30 text-secondary' : 'bg-tertiary-container/30 text-tertiary'"
        >
          <span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1">{{ feat.icon }}</span>
        </div>
        <div>
          <h4 class="font-bold text-on-surface mb-1">{{ feat.title }}</h4>
          <p class="text-xs text-on-surface-variant">{{ feat.desc }}</p>
        </div>
      </div>
    </div>

    <!-- Settings Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-10">
      <!-- System Config -->
      <div class="space-y-4">
        <div class="flex items-center gap-2 mb-4">
          <span class="w-1.5 h-6 bg-primary rounded-full" />
          <h3 class="font-[Plus_Jakarta_Sans] text-xl font-bold text-on-surface">全局系统配置</h3>
        </div>
        <div class="glass-panel rounded-3xl overflow-hidden divide-y divide-white/10 depth-2">
          <div class="p-6 flex items-center justify-between group hover:bg-white/10 transition-colors">
            <div class="flex gap-4">
              <div class="text-primary opacity-60 group-hover:opacity-100 transition-opacity">
                <span class="material-symbols-outlined">rocket_launch</span>
              </div>
              <div>
                <p class="font-bold text-on-surface">加速模式</p>
                <p class="text-sm text-on-surface-variant">启用硬件加速以提升大规模宠物数据加载速度</p>
              </div>
            </div>
            <el-switch v-model="settings.acceleration" active-color="#6daf92" @change="toggleSetting('acceleration')" />
          </div>
          <div class="p-6 flex items-center justify-between group hover:bg-white/10 transition-colors">
            <div class="flex gap-4">
              <div class="text-primary opacity-60 group-hover:opacity-100 transition-opacity">
                <span class="material-symbols-outlined">cloud_sync</span>
              </div>
              <div>
                <p class="font-bold text-on-surface">云端自动备份</p>
                <p class="text-sm text-on-surface-variant">每小时自动同步宠物医疗档案至安全云端</p>
              </div>
            </div>
            <el-switch v-model="settings.cloudBackup" active-color="#6daf92" @change="toggleSetting('cloudBackup')" />
          </div>
          <div class="p-6 flex items-center justify-between group hover:bg-white/10 transition-colors">
            <div class="flex gap-4">
              <div class="text-primary opacity-60 group-hover:opacity-100 transition-opacity">
                <span class="material-symbols-outlined">smart_toy</span>
              </div>
              <div>
                <p class="font-bold text-on-surface">AI 辅助诊断建议</p>
                <p class="text-sm text-on-surface-variant">在宠物详情页自动生成日常护理及异常预警建议</p>
              </div>
            </div>
            <el-switch v-model="settings.aiDiagnosis" active-color="#6daf92" @change="toggleSetting('aiDiagnosis')" />
          </div>
        </div>
      </div>

      <!-- Notification & Privacy -->
      <div class="space-y-4">
        <div class="flex items-center gap-2 mb-4">
          <span class="w-1.5 h-6 bg-secondary rounded-full" />
          <h3 class="font-[Plus_Jakarta_Sans] text-xl font-bold text-on-surface">通知与隐私</h3>
        </div>
        <div class="glass-panel rounded-3xl overflow-hidden divide-y divide-white/10 depth-2">
          <div class="p-6 flex items-center justify-between group hover:bg-white/10 transition-colors">
            <div class="flex gap-4">
              <div class="text-secondary opacity-60 group-hover:opacity-100 transition-opacity">
                <span class="material-symbols-outlined">mail</span>
              </div>
              <div>
                <p class="font-bold text-on-surface">系统邮件通知</p>
                <p class="text-sm text-on-surface-variant">向管理员发送关键系统更新与安全审计报告</p>
              </div>
            </div>
            <el-switch v-model="settings.emailNotification" active-color="#6daf92" @change="toggleSetting('emailNotification')" />
          </div>
          <div class="p-6 flex items-center justify-between group hover:bg-white/10 transition-colors">
            <div class="flex gap-4">
              <div class="text-secondary opacity-60 group-hover:opacity-100 transition-opacity">
                <span class="material-symbols-outlined">location_on</span>
              </div>
              <div>
                <p class="font-bold text-on-surface">实时位置脱敏</p>
                <p class="text-sm text-on-surface-variant">对共享动态中的宠物位置信息进行模糊处理</p>
              </div>
            </div>
            <el-switch v-model="settings.locationMask" active-color="#6daf92" @change="toggleSetting('locationMask')" />
          </div>
          <div class="p-6 flex items-center justify-between group hover:bg-white/10 transition-colors">
            <div class="flex gap-4">
              <div class="text-secondary opacity-60 group-hover:opacity-100 transition-opacity">
                <span class="material-symbols-outlined">visibility_off</span>
              </div>
              <div>
                <p class="font-bold text-on-surface">极简管理模式</p>
                <p class="text-sm text-on-surface-variant">隐藏高级统计图表，仅展示基础管理操作</p>
              </div>
            </div>
            <el-switch v-model="settings.simpleMode" active-color="#6daf92" @change="toggleSetting('simpleMode')" />
          </div>
        </div>
      </div>
    </div>

    <!-- Update Banner -->
    <div class="glass-panel p-6 rounded-3xl border-dashed border-2 border-primary/30 flex flex-col md:flex-row items-center justify-between gap-6 depth-1 animate-float-up" style="animation-delay: 0.4s">
      <div class="flex items-center gap-4">
        <div class="w-14 h-14 rounded-full bg-primary/10 flex items-center justify-center">
          <span class="material-symbols-outlined text-primary text-3xl">download_done</span>
        </div>
        <div>
          <h4 class="font-bold text-on-surface">已有可用更新</h4>
          <p class="text-sm text-on-surface-variant">新版本 v2.4.1 已发布，修复了若干已知问题并提升了 UI 响应效率。</p>
        </div>
      </div>
      <div class="flex gap-4">
        <button class="px-6 py-2.5 rounded-full border border-primary text-primary font-bold hover:bg-primary/5 transition-colors">查看日志</button>
        <button class="px-8 py-2.5 rounded-full bg-primary text-white font-bold shadow-lg shadow-primary/20 hover:opacity-90 transition-opacity btn-jelly">立即升级</button>
      </div>
    </div>
  </div>
</template>
