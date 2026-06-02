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
]

const isActive = (path: string) => route.path === path
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
  <aside class="fixed left-0 top-0 h-full flex flex-col py-8 h-screen w-72 border-r border-white/20 bg-white/40 backdrop-blur-[20px] shadow-[10px_0_30px_-15px_rgba(0,0,0,0.05)] z-50">
    <!-- Logo -->
    <div class="px-8 mb-12">
      <h1 class="text-2xl font-black text-primary-container drop-shadow-[0_0_8px_rgba(109,175,146,0.4)] font-[Plus_Jakarta_Sans]">PetLumina</h1>
      <p class="text-xs font-[Plus_Jakarta_Sans] font-medium text-slate-500 mt-1 uppercase tracking-widest">Management Portal</p>
    </div>

    <!-- Menu -->
    <nav class="flex-1 flex flex-col gap-2 px-4">
      <a
        v-for="item in menuItems"
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
    </nav>

    <!-- Admin Info -->
    <div class="relative px-8 mt-auto border-t border-white/10 pt-6">
      <div class="flex items-center gap-4 cursor-pointer" @click="showMenu = !showMenu">
        <div class="w-10 h-10 rounded-full border-2 border-primary-container bg-primary-container/20 flex items-center justify-center text-white font-bold text-sm">
          A
        </div>
        <div class="flex-1">
          <p class="font-label text-sm font-bold text-on-surface">{{ adminStore.currentUser?.nickname || '管理员' }}</p>
          <p class="text-[10px] text-slate-500 uppercase tracking-tight">Super Admin</p>
        </div>
        <span class="material-symbols-outlined text-slate-400 text-lg transition-transform" :class="{ 'rotate-180': showMenu }">expand_more</span>
      </div>
      <!-- Logout Dropdown -->
      <Transition name="dropdown">
        <div v-if="showMenu" class="absolute bottom-full left-4 right-4 mb-2 glass-panel-deep rounded-2xl overflow-hidden shadow-xl">
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
  transition: all 0.2s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
