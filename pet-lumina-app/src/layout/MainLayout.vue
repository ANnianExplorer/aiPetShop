<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const active = ref('home')

const tabs = computed(() => [
  { name: 'home', path: '/app', icon: 'home', labelKey: 'nav.home' },
  { name: 'lifeLog', path: '/life-log', icon: 'edit_note', labelKey: 'nav.lifeLog' },
  { name: 'community', path: '/community', icon: 'groups', labelKey: 'nav.community' },
  { name: 'wellness', path: '/wellness', icon: 'restaurant', labelKey: 'nav.wellness' },
  { name: 'profile', path: '/profile', icon: 'person', labelKey: 'nav.profile' },
])

watch(
  () => route.name,
  (newVal) => {
    if (newVal && typeof newVal === 'string') {
      active.value = newVal
    }
  },
  { immediate: true }
)

const navigate = (tab: { name: string; path: string; icon: string; labelKey: string }) => {
  if (active.value !== tab.name) {
    router.push(tab.path)
  }
}
</script>

<template>
  <div class="min-h-screen bg-background relative">
    <!-- Ambient decorative glows -->
    <div class="fixed top-[-10%] left-[-5%] w-[50%] h-[50%] bg-primary-fixed-dim/20 dark:bg-primary/10 blur-[100px] rounded-full pointer-events-none animate-ambient-drift z-0" />
    <div class="fixed bottom-[10%] right-[-5%] w-[40%] h-[40%] bg-secondary-container/10 dark:bg-secondary/5 blur-[80px] rounded-full pointer-events-none animate-ambient-drift z-0" style="animation-delay: -4s" />

    <!-- 页面内容区域 -->
    <RouterView />

    <!-- 全局底部导航 - 胶囊样式 -->
    <nav class="fixed bottom-3 left-4 right-4 z-50 pb-safe">
      <div class="bg-white/80 dark:bg-surface-container/80 backdrop-blur-2xl rounded-[28px] shadow-[0_8px_32px_rgba(75,100,85,0.12),0_0_0_1px_rgba(255,255,255,0.5)] dark:shadow-[0_8px_32px_rgba(0,0,0,0.2),0_0_0_1px_rgba(255,255,255,0.08)] px-2 py-2">
        <div class="flex justify-around items-center max-w-screen-xl mx-auto">
          <div
            v-for="tab in tabs"
            :key="tab.name"
            @click="navigate(tab)"
            class="flex flex-col items-center justify-center cursor-pointer transition-all duration-300 ease-out relative rounded-[20px] py-2 px-3 min-w-[56px]"
            :class="active === tab.name
              ? 'bg-primary/10 dark:bg-primary/20 scale-105'
              : 'active:scale-90 active:bg-black/[0.03] dark:active:bg-white/[0.05]'"
          >
            <span
              class="material-symbols-outlined mb-0.5 transition-all duration-300 text-[22px]"
              :style="active === tab.name
                ? 'font-variation-settings: \'FILL\' 1, \'wght\' 600; filter: drop-shadow(0 0 6px rgba(75,100,85,0.4))'
                : 'font-variation-settings: \'FILL\' 0, \'wght\' 400; opacity: 0.5'"
              :class="active === tab.name ? 'text-primary' : 'text-on-surface'"
            >{{ tab.icon }}</span>
            <span
              class="font-['Plus_Jakarta_Sans'] text-[9px] tracking-wide transition-all duration-300"
              :class="active === tab.name
                ? 'font-bold text-primary'
                : 'font-medium text-on-surface-variant/60'"
            >{{ t(tab.labelKey) }}</span>
          </div>
        </div>
      </div>
    </nav>
  </div>
</template>
