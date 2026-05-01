<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { showToast } = useToast()

const goBack = () => {
  router.back()
}

const notificationsEnabled = ref(true)
const darkMode = ref(false)
const language = ref('zh-CN')
const autoBackup = ref(true)

const toggleSetting = (setting: string) => {
  switch (setting) {
    case 'notifications':
      notificationsEnabled.value = !notificationsEnabled.value
      showToast(notificationsEnabled.value ? '通知已开启' : '通知已关闭', 'success')
      break
    case 'darkMode':
      darkMode.value = !darkMode.value
      showToast(darkMode.value ? '深色模式已开启' : '深色模式已关闭', 'success')
      break
    case 'autoBackup':
      autoBackup.value = !autoBackup.value
      showToast(autoBackup.value ? '自动备份已开启' : '自动备份已关闭', 'success')
      break
  }
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex items-center justify-between py-md mb-lg">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">通用设置</span>
        <div class="w-10"></div>
      </div>

      <section class="space-y-4 mb-lg">
        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">通知设置</h3>
          <div class="flex items-center justify-between py-2">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-on-surface-variant">notifications</span>
              <span class="text-sm text-on-surface">推送通知</span>
            </div>
            <button 
              @click="toggleSetting('notifications')"
              class="w-12 h-6 rounded-full transition-colors relative"
              :class="notificationsEnabled ? 'bg-primary' : 'bg-surface-variant'"
            >
              <div 
                class="w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform shadow-sm"
                :class="notificationsEnabled ? 'translate-x-6' : 'translate-x-0.5'"
              ></div>
            </button>
          </div>
        </div>

        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">显示设置</h3>
          <div class="flex items-center justify-between py-2">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-on-surface-variant">dark_mode</span>
              <span class="text-sm text-on-surface">深色模式</span>
            </div>
            <button 
              @click="toggleSetting('darkMode')"
              class="w-12 h-6 rounded-full transition-colors relative"
              :class="darkMode ? 'bg-primary' : 'bg-surface-variant'"
            >
              <div 
                class="w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform shadow-sm"
                :class="darkMode ? 'translate-x-6' : 'translate-x-0.5'"
              ></div>
            </button>
          </div>
        </div>

        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">数据设置</h3>
          <div class="flex items-center justify-between py-2">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-on-surface-variant">cloud_upload</span>
              <span class="text-sm text-on-surface">自动备份</span>
            </div>
            <button 
              @click="toggleSetting('autoBackup')"
              class="w-12 h-6 rounded-full transition-colors relative"
              :class="autoBackup ? 'bg-primary' : 'bg-surface-variant'"
            >
              <div 
                class="w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform shadow-sm"
                :class="autoBackup ? 'translate-x-6' : 'translate-x-0.5'"
              ></div>
            </button>
          </div>
        </div>

        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">缓存管理</h3>
          <button 
            @click="showToast('缓存已清除', 'success')"
            class="w-full py-3 bg-surface-container text-on-surface rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform"
          >
            清除缓存
          </button>
        </div>
      </section>
    </main>
  </div>
</template>
