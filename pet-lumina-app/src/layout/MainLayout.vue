<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const active = ref('home')

const tabs = [
  { name: 'home', path: '/app', icon: 'home', label: '首页' },
  { name: 'lifeLog', path: '/life-log', icon: 'edit_note', label: '生活记录' },
  { name: 'community', path: '/community', icon: 'groups', label: '宠物社区' },
  { name: 'wellness', path: '/wellness', icon: 'restaurant', label: '饮食健康' },
  { name: 'profile', path: '/profile', icon: 'person', label: '个人中心' },
]

watch(
  () => route.name,
  (newVal) => {
    if (newVal && typeof newVal === 'string') {
      active.value = newVal
    }
  },
  { immediate: true }
)

const navigate = (tab: typeof tabs[0]) => {
  if (active.value !== tab.name) {
    router.push(tab.path)
  }
}
</script>

<template>
  <div class="min-h-screen bg-background relative">
    <!-- Ambient decorative glows -->
    <div class="fixed top-[-10%] left-[-5%] w-[50%] h-[50%] bg-primary-fixed-dim/20 blur-[100px] rounded-full pointer-events-none animate-ambient-drift z-0" />
    <div class="fixed bottom-[10%] right-[-5%] w-[40%] h-[40%] bg-secondary-container/10 blur-[80px] rounded-full pointer-events-none animate-ambient-drift z-0" style="animation-delay: -4s" />

    <!-- 页面内容区域 -->
    <RouterView />

    <!-- 全局底部导航 -->
    <nav class="fixed bottom-0 left-0 right-0 w-full z-50 pb-safe bg-white/70 backdrop-blur-2xl border-t border-white/30 shadow-[0_-4px_30px_rgba(75,100,85,0.06)]">
      <div class="flex justify-around items-center h-20 px-2 max-w-screen-xl mx-auto">
        <div
          v-for="tab in tabs"
          :key="tab.name"
          @click="navigate(tab)"
          class="flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ease-out relative px-2"
          :class="active === tab.name
            ? 'text-primary scale-105'
            : 'text-outline-variant/60 active:scale-90'"
        >
          <!-- Active indicator dot -->
          <Transition name="tab-dot">
            <div v-if="active === tab.name" class="absolute -top-1 w-1 h-1 rounded-full bg-primary shadow-[0_0_8px_rgba(75,100,85,0.5)]" />
          </Transition>

          <span
            class="material-symbols-outlined mb-1 transition-all duration-300"
            :style="active === tab.name
              ? 'font-variation-settings: \'FILL\' 1; filter: drop-shadow(0 0 6px rgba(75,100,85,0.4))'
              : 'font-variation-settings: \'FILL\' 0'"
          >{{ tab.icon }}</span>
          <span class="font-['Plus_Jakarta_Sans'] text-[10px] font-semibold tracking-wide transition-all duration-300"
            :class="active === tab.name ? 'font-bold' : ''"
          >{{ tab.label }}</span>
        </div>
      </div>
    </nav>
  </div>
</template>

<style scoped>
.tab-dot-enter-active,
.tab-dot-leave-active {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.tab-dot-enter-from,
.tab-dot-leave-to {
  opacity: 0;
  transform: scale(0);
}
</style>
