<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterView } from 'vue-router'
import Toast from '@/components/common/Toast.vue'
import DeskPet from '@/components/pet/DeskPet.vue'
import { useDarkMode } from '@/composables/useDarkMode'

const { initDarkMode } = useDarkMode()

onMounted(() => {
  initDarkMode()
})
</script>

<template>
  <RouterView />
  <Toast />
  <!-- 桌宠是全局挂件：换页面不掉，对话中的工作状态才连得上 -->
  <DeskPet />
</template>
