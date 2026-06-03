<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'

const router = useRouter()
const adminStore = useAdminStore()

const handleLogout = () => {
  adminStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="sticky top-4 z-40 flex justify-between items-center px-8 py-3 h-16 ml-[286px] mr-4 bg-white/70 backdrop-blur-2xl rounded-[20px] shadow-[0_4px_20px_rgba(75,100,85,0.06),0_0_0_1px_rgba(255,255,255,0.5)]">
    <div class="flex items-center gap-6">
      <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-semibold text-on-surface">管理后台</h2>
    </div>
    <div class="flex items-center gap-8">
      <div class="relative cursor-pointer">
        <span class="material-symbols-outlined text-slate-600 hover:opacity-80 transition-opacity">notifications</span>
        <span class="absolute -top-1 -right-1 w-2 h-2 bg-error rounded-full"></span>
      </div>
      <div class="flex items-center gap-3 cursor-pointer" @click="handleLogout">
        <div class="w-8 h-8 rounded-full bg-primary-container/20 flex items-center justify-center text-white text-xs font-bold">A</div>
        <span class="text-sm text-on-surface-variant">退出</span>
      </div>
    </div>
  </header>
</template>
