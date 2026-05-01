<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

const actions = [
  { icon: 'edit_note', label: '生活记录', path: '/life-log' },
  { icon: 'notifications_active', label: '健康提醒', path: '/wellness' },
  { icon: 'fitness_center', label: '训练计划', path: '/wellness' },
  { icon: 'more_horiz', label: '更多', path: '/' },
]
</script>

<template>
  <section>
    <h2 class="font-headline-md text-headline-md mb-md">常用功能</h2>
    <div class="flex justify-between items-center bg-surface-container-low p-md rounded-xl">
      <div 
        v-for="(action, index) in actions" 
        :key="index"
        @click="router.push(action.path)"
        class="flex flex-col items-center gap-2 px-4 cursor-pointer hover:opacity-80 transition-opacity"
      >
        <div class="w-14 h-14 bg-white rounded-2xl shadow-sm flex items-center justify-center text-primary">
          <span class="material-symbols-outlined text-3xl">{{ action.icon }}</span>
        </div>
        <span class="font-label-bold text-[11px]">{{ action.label }}</span>
      </div>
    </div>
  </section>
</template>
