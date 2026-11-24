<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import type { LogEntry } from '@/types'

const { t } = useI18n()

defineProps<{
  log: LogEntry
}>()

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
  <RouterLink
    :to="{ name: 'logDetail', params: { id: log.id } }"
    class="block break-inside-avoid bg-surface-container-lowest rounded-xl overflow-hidden shadow-[0_-4px_20px_rgba(0,0,0,0.03)] group mb-card-gutter cursor-pointer hover:shadow-md transition-shadow"
    :aria-label="t('a11y.logCard', { title: log.title })"
  >
    <div class="relative overflow-hidden">
      <img
        v-if="log.imageList && log.imageList.length > 0"
        :src="log.imageList[0]"
        :alt="t('a11y.logImage', { title: log.title })"
        class="w-full object-cover group-hover:scale-105 transition-transform duration-500"
      />
      <div class="absolute top-2 left-2 w-8 h-8 bg-white/80 dark:bg-surface-container/80 backdrop-blur-md rounded-full flex items-center justify-center" aria-hidden="true">
        <span class="material-symbols-outlined text-sm text-primary">{{ getTypeIcon(log.type) }}</span>
      </div>
    </div>
    <div class="p-3">
      <p class="font-label-bold text-on-surface leading-tight mb-1">{{ log.title }}</p>
      <div class="flex items-center justify-between text-[10px] text-outline">
        <span>{{ log.createTime }}</span>
        <div class="flex gap-1 flex-wrap">
          <span v-for="tag in (log.tagList || []).slice(0, 2)" :key="tag" class="text-primary">#{{ tag }}</span>
        </div>
      </div>
    </div>
  </RouterLink>
</template>
