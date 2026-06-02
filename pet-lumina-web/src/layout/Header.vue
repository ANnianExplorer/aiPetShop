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
  <header class="sticky top-0 z-40 w-full flex justify-between items-center px-12 py-4 h-20 ml-72 bg-white/10 backdrop-blur-md border-b border-white/10">
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
