<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Tabbar, TabbarItem } from 'vant'

const route = useRoute()
const router = useRouter()
const active = ref('home')

watch(
  () => route.name,
  (newVal) => {
    if (newVal && typeof newVal === 'string') {
      active.value = newVal
    }
  },
  { immediate: true }
)
</script>

<template>
  <div class="min-h-screen bg-background">
    <!-- 页面内容区域 -->
    <RouterView />

    <!-- 全局底部导航 -->
    <nav class="fixed bottom-0 left-0 right-0 w-full z-50 pb-safe bg-white/80 dark:bg-zinc-900/80 backdrop-blur-2xl border-t border-zinc-100/30 dark:border-zinc-800/30 shadow-[0_-4px_20px_rgba(0,0,0,0.03)]">
      <div class="flex justify-around items-center h-20 px-2 max-w-screen-xl mx-auto">
        <div @click="router.push('/')" :class="['flex flex-col items-center justify-center cursor-pointer transition-all duration-150 ease-out', active === 'home' ? 'text-emerald-700 scale-110' : 'text-zinc-400 opacity-80 hover:text-emerald-500 active:scale-90']">
          <span class="material-symbols-outlined mb-1" :style="active === 'home' ? 'font-variation-settings: \'FILL\' 1;' : ''">home</span>
          <span class="font-['Plus_Jakarta_Sans'] text-[10px] font-semibold tracking-wide">首页</span>
        </div>
        
        <div @click="router.push('/life-log')" :class="['flex flex-col items-center justify-center cursor-pointer transition-all duration-150 ease-out', active === 'lifeLog' ? 'text-emerald-700 scale-110' : 'text-zinc-400 opacity-80 hover:text-emerald-500 active:scale-90']">
          <span class="material-symbols-outlined mb-1" :style="active === 'lifeLog' ? 'font-variation-settings: \'FILL\' 1;' : ''">edit_note</span>
          <span class="font-['Plus_Jakarta_Sans'] text-[10px] font-semibold tracking-wide">生活记录</span>
        </div>

        <div @click="router.push('/community')" :class="['flex flex-col items-center justify-center cursor-pointer transition-all duration-150 ease-out', active === 'community' ? 'text-emerald-700 scale-110' : 'text-zinc-400 opacity-80 hover:text-emerald-500 active:scale-90']">
          <span class="material-symbols-outlined mb-1" :style="active === 'community' ? 'font-variation-settings: \'FILL\' 1;' : ''">groups</span>
          <span class="font-['Plus_Jakarta_Sans'] text-[10px] font-semibold tracking-wide">宠物社区</span>
        </div>

        <div @click="router.push('/wellness')" :class="['flex flex-col items-center justify-center cursor-pointer transition-all duration-150 ease-out', active === 'wellness' ? 'text-emerald-700 scale-110' : 'text-zinc-400 opacity-80 hover:text-emerald-500 active:scale-90']">
          <span class="material-symbols-outlined mb-1" :style="active === 'wellness' ? 'font-variation-settings: \'FILL\' 1;' : ''">restaurant</span>
          <span class="font-['Plus_Jakarta_Sans'] text-[10px] font-semibold tracking-wide">饮食健康</span>
        </div>

        <div @click="router.push('/profile')" :class="['flex flex-col items-center justify-center cursor-pointer transition-all duration-150 ease-out', active === 'profile' ? 'text-emerald-700 scale-110' : 'text-zinc-400 opacity-80 hover:text-emerald-500 active:scale-90']">
          <span class="material-symbols-outlined mb-1" :style="active === 'profile' ? 'font-variation-settings: \'FILL\' 1;' : ''">person</span>
          <span class="font-['Plus_Jakarta_Sans'] text-[10px] font-semibold tracking-wide">个人中心</span>
        </div>
      </div>
    </nav>
  </div>
</template>
