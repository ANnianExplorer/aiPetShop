<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const { t } = useI18n()

const menuItems = [
  { icon: 'person_edit', labelKey: 'profile.editProfile', route: 'editProfile' },
  { icon: 'pets', labelKey: 'profile.petStudio', route: 'petStudio' },
  { icon: 'psychology', labelKey: 'profile.myMemory', route: 'myMemory' },
  { icon: 'shield_lock', labelKey: 'profile.accountSecurity', route: 'accountSecurity' },
  { icon: 'settings', labelKey: 'profile.generalSettings', route: 'generalSettings' },
  { icon: 'help_center', labelKey: 'profile.helpFeedback', route: 'helpFeedback' },
]

const handleNavigation = (route: string) => {
  router.push({ name: route })
}
</script>

<template>
  <section class="mt-12 space-y-2">
    <h2 class="font-headline-md text-[16px] text-on-surface px-1 mb-4">{{ t('profile.systemSettings') }}</h2>
    <button
      v-for="(item, index) in menuItems"
      :key="index"
      @click="handleNavigation(item.route)"
      class="w-full flex items-center justify-between p-4 bg-white dark:bg-surface-container-low rounded-xl shadow-[0_4px_20px_rgba(0,0,0,0.02)] dark:shadow-[0_4px_20px_rgba(0,0,0,0.2)] active:scale-[0.98] transition-all hover:shadow-md"
    >
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-surface-container flex items-center justify-center text-primary">
          <span class="material-symbols-outlined">{{ item.icon }}</span>
        </div>
        <span class="font-body-md text-body-md text-on-surface">{{ t(item.labelKey) }}</span>
      </div>
      <span class="material-symbols-outlined text-outline">chevron_right</span>
    </button>
  </section>
</template>
