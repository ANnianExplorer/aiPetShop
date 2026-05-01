<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const menuItems = [
  { icon: 'person_edit', label: '编辑个人资料', route: 'editProfile' },
  { icon: 'shield_lock', label: '账号与安全', route: 'accountSecurity' },
  { icon: 'settings', label: '通用设置', route: 'generalSettings' },
  { icon: 'help_center', label: '帮助与反馈', route: 'helpFeedback' },
]

const handleNavigation = (route: string) => {
  router.push({ name: route })
}
</script>

<template>
  <section class="mt-12 space-y-2">
    <h2 class="font-headline-md text-[16px] text-on-surface px-1 mb-4">系统设置</h2>
    <button 
      v-for="(item, index) in menuItems" 
      :key="index"
      @click="handleNavigation(item.route)"
      class="w-full flex items-center justify-between p-4 bg-white rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.02)] active:scale-[0.98] transition-all hover:shadow-md"
    >
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center text-primary">
          <span class="material-symbols-outlined">{{ item.icon }}</span>
        </div>
        <span class="font-body-md text-body-md text-on-surface">{{ item.label }}</span>
      </div>
      <span class="material-symbols-outlined text-outline">chevron_right</span>
    </button>
  </section>
</template>
