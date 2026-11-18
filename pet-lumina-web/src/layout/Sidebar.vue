<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAdminStore } from '@/stores/admin'

const router = useRouter()
const route = useRoute()
const adminStore = useAdminStore()

const menuItems = [
  { path: '/dashboard', icon: 'dashboard', label: '数据概览' },
  { path: '/user', icon: 'group', label: '用户管理' },
  { path: '/pet', icon: 'pets', label: '宠物管理' },
  { path: '/post', icon: 'article', label: '帖子管理' },
  { path: '/comment', icon: 'chat_bubble', label: '评论管理' },
  { path: '/log', icon: 'history_edu', label: '生活记录' },
  { path: '/topic', icon: 'topic', label: '话题管理' },
  { path: '/health', icon: 'monitor_heart', label: '健康数据' },
  { path: '/notification', icon: 'notifications', label: '通知管理' },
  { path: '/violation', icon: 'gpp_maybe', label: '违规管理' },
  { path: '/agent/sessions', icon: 'forum', label: '会话工作台' },
  { path: '/agent/memory', icon: 'psychology', label: '长期记忆' },
  { path: '/agent/graph', icon: 'hub', label: '知识图谱' },
  { path: '/agent/profile', icon: 'pets', label: '宠物画像' },
  { path: '/agent/queue', icon: 'queue', label: '队列运维' },
  { path: '/agent/model', icon: 'tune', label: '模型配置' },
]

const bottomMenuItems = [
  { path: '/settings', icon: 'settings', label: '系统设置' },
]

const isActive = (path: string) => route.path === path || route.path.startsWith(path + '/')
const showMenu = ref(false)

const navigate = (path: string) => {
  router.push(path)
}

const handleLogout = () => {
  showMenu.value = false
  adminStore.logout()
  router.push('/login')
}
</script>

<template>
  <aside class="fixed left-4 top-4 bottom-4 flex flex-col py-8 w-60 bg-white/70 backdrop-blur-2xl rounded-[28px] shadow-[0_8px_32px_rgba(75,100,85,0.1),0_0_0_1px_rgba(255,255,255,0.5)] z-50">
    <!-- Logo -->
    <div class="px-8 mb-6">
      <h1 class="text-2xl font-black text-primary-container drop-shadow-[0_0_8px_rgba(109,175,146,0.4)] font-[Plus_Jakarta_Sans]">PetLumina</h1>
      <p class="text-xs font-[Plus_Jakarta_Sans] font-medium text-slate-500 mt-1 uppercase tracking-widest">Management Portal</p>
    </div>

    <!-- Main Menu -->
    <nav class="flex-1 flex flex-col gap-1 px-4 overflow-y-auto no-scrollbar">
      <a
        v-for="(item, index) in menuItems"
        :key="item.path"
        @click="navigate(item.path)"
        class="flex items-center gap-4 px-4 py-2.5 rounded-xl transition-all duration-300 cursor-pointer font-[Plus_Jakarta_Sans] text-[13px] animate-float-up"
        :class="isActive(item.path)
          ? 'text-primary-container font-bold border-l-[3px] border-primary-container bg-primary-container/8 shadow-[inset_0_0_20px_rgba(109,175,146,0.06)]'
          : 'text-slate-500 font-medium hover:bg-white/40 hover:text-on-surface hover:scale-[1.01] hover:shadow-[inset_0_0_12px_rgba(255,255,255,0.3)] active:scale-[0.98]'"
        :style="{ animationDelay: `${index * 0.05}s` }"
      >
        <span class="material-symbols-outlined" :class="{ 'glow-icon': isActive(item.path) }">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </a>
    </nav>

    <!-- Bottom Menu -->
    <div class="px-4 mb-2">
      <a
        v-for="item in bottomMenuItems"
        :key="item.path"
        @click="navigate(item.path)"
        class="flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 cursor-pointer font-[Plus_Jakarta_Sans] text-sm"
        :class="isActive(item.path)
          ? 'text-primary-container font-bold border-r-2 border-primary-container bg-white/10'
          : 'text-slate-500 font-medium hover:bg-white/30 hover:scale-[1.02]'"
      >
        <span class="material-symbols-outlined" :class="{ 'glow-icon': isActive(item.path) }">{{ item.icon }}</span>
        <span>{{ item.label }}</span>
      </a>
    </div>

    <!-- Admin Info -->
    <div class="relative px-8 border-t border-white/10 pt-6">
      <div class="flex items-center gap-4 cursor-pointer group" @click="showMenu = !showMenu">
        <div class="w-10 h-10 rounded-full border-2 border-primary-container/30 bg-primary-container/20 flex items-center justify-center text-white font-bold text-sm overflow-hidden transition-all duration-300 group-hover:border-primary-container/60 group-hover:shadow-[0_0_12px_rgba(109,175,146,0.2)]">
          <span class="material-symbols-outlined text-primary-container text-lg">person</span>
        </div>
        <div class="flex-1 min-w-0">
          <p class="font-label text-sm font-bold text-on-surface truncate">{{ adminStore.currentUser?.nickname || '管理员' }}</p>
          <p class="text-[10px] text-slate-500 uppercase tracking-tight">Super Admin</p>
        </div>
        <span class="material-symbols-outlined text-slate-400 text-lg transition-transform duration-300" :class="{ 'rotate-180': showMenu }">expand_more</span>
      </div>

      <!-- Dropdown Menu -->
      <Transition name="dropdown">
        <div v-if="showMenu" class="absolute bottom-full left-4 right-4 mb-2 glass-panel-deep rounded-2xl overflow-hidden shadow-xl">
          <button @click="navigate('/profile'); showMenu = false" class="w-full flex items-center gap-3 px-5 py-3.5 text-sm text-on-surface hover:bg-white/30 transition-colors font-[Plus_Jakarta_Sans] font-medium">
            <span class="material-symbols-outlined text-lg text-primary-container">person</span>
            <span>个人中心</span>
          </button>
          <div class="border-t border-white/10" />
          <button @click="handleLogout" class="w-full flex items-center gap-3 px-5 py-3.5 text-sm text-error hover:bg-white/30 transition-colors font-[Plus_Jakarta_Sans] font-medium">
            <span class="material-symbols-outlined text-lg">logout</span>
            <span>退出登录</span>
          </button>
        </div>
      </Transition>
    </div>
  </aside>
</template>

<style scoped>
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.95);
}
</style>