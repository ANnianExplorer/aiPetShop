<script setup lang="ts">
import { useRouter } from 'vue-router'
import type { LogEntry } from '@/types'

const router = useRouter()

const props = defineProps<{
  log: LogEntry
}>()

const navigateToLog = () => {
  router.push({ name: 'logDetail', params: { id: props.log.id } })
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, string> = {
    feeding: 'restaurant',
    walking: 'directions_walk',
    grooming: 'content_cut',
    medical: 'medical_services',
    other: 'event_note'
  }
  return icons[type] || 'event_note'
}
</script>

<template>
  <div @click="navigateToLog" class="break-inside-avoid bg-surface-container-lowest rounded-xl overflow-hidden shadow-[0_-4px_20px_rgba(0,0,0,0.03)] group mb-card-gutter cursor-pointer hover:shadow-md transition-shadow">
    <div class="relative overflow-hidden">
      <img 
        v-if="log.images.length > 0"
        :src="log.images[0]" 
        class="w-full object-cover group-hover:scale-105 transition-transform duration-500" 
      />
      <div class="absolute top-2 left-2 w-8 h-8 bg-white/80 backdrop-blur-md rounded-full flex items-center justify-center">
        <span class="material-symbols-outlined text-sm text-primary">{{ getTypeIcon(log.type) }}</span>
      </div>
    </div>
    <div class="p-3">
      <p class="font-label-bold text-on-surface leading-tight mb-1">{{ log.title }}</p>
      <div class="flex items-center justify-between text-[10px] text-outline">
        <span>{{ log.createdAt }}</span>
        <div class="flex gap-1 flex-wrap">
          <span v-for="tag in log.tags.slice(0, 2)" :key="tag" class="text-primary">#{{ tag }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
