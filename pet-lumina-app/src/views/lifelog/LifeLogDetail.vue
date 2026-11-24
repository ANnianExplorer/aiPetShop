<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'
import ShareModal from '@/components/common/ShareModal.vue'
import type { LogEntry } from '@/types'
import { logApi } from '@/api/log'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { showToast } = useToast()

const logId = computed(() => String(route.params.id))

const log = ref<LogEntry | null>(null)
const loading = ref(true)
const isLiked = ref(false)
const likeCount = ref(0)
const showShareModal = ref(false)

onMounted(async () => {
  try {
    log.value = await logApi.getById(logId.value)
    likeCount.value = log.value?.likes || 0
  } catch (e) {
    console.error('Failed to fetch log:', e)
    log.value = null
  } finally {
    loading.value = false
  }
})

const toggleLike = async () => {
  try {
    const result = await logApi.toggleLike(logId.value)
    isLiked.value = !!result
    likeCount.value += result ? 1 : -1
  } catch {
    showToast(t('common.error'), 'error')
  }
}

const goBack = () => {
  router.back()
}

const openShare = () => {
  showShareModal.value = true
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

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    feeding: 'bg-primary-container text-primary',
    walking: 'bg-secondary-container text-secondary',
    grooming: 'bg-tertiary-container text-tertiary',
    medical: 'bg-error-container text-error',
    other: 'bg-surface-container-high text-on-surface'
  }
  return colors[type] || 'bg-surface-container-high text-on-surface'
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main v-if="log" class="pt-4">
      <div class="p-container-padding space-y-lg max-w-screen-xl mx-auto">
        <div class="flex items-center justify-between py-md mb-md">
          <button type="button" @click="goBack" :aria-label="t('common.back')" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
            <span class="material-symbols-outlined text-emerald-700" aria-hidden="true">arrow_back</span>
          </button>
          <span class="font-title-sm text-on-surface">{{ t('log.logDetail') }}</span>
          <button type="button" @click="openShare" :aria-label="t('a11y.shareLog')" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
            <span class="material-symbols-outlined text-emerald-700" aria-hidden="true">more_vert</span>
          </button>
        </div>
        <div class="flex items-center gap-sm">
          <div class="w-12 h-12 rounded-xl flex items-center justify-center" :class="getTypeColor(log.type)" aria-hidden="true">
            <span class="material-symbols-outlined text-2xl">{{ getTypeIcon(log.type) }}</span>
          </div>
          <div>
            <h2 class="font-headline-sm text-headline-sm text-on-surface">{{ log.title }}</h2>
            <p class="text-xs text-on-surface-variant">{{ log.createTime }}</p>
          </div>
        </div>

        <div v-if="log.imageList && log.imageList.length > 0" class="rounded-xl overflow-hidden">
          <img class="w-full h-auto object-cover" :src="log.imageList[0]" :alt="t('a11y.logImage', { title: log.title })" />
        </div>

        <p class="font-body-md text-body-md text-on-surface leading-relaxed">{{ log.content }}</p>

        <div class="flex gap-sm flex-wrap">
          <span v-for="tag in (log.tagList || [])" :key="tag" class="px-3 py-1 bg-primary-container text-primary rounded-full text-xs font-label-bold">
            #{{ tag }}
          </span>
        </div>

        <div class="flex items-center justify-between py-md border-t border-b border-surface-variant/30">
          <button @click="toggleLike" class="flex items-center gap-2 px-4 py-2 rounded-full transition-colors" :class="isLiked ? 'text-red-500' : 'text-on-surface-variant hover:bg-surface-container'">
            <span class="material-symbols-outlined">{{ isLiked ? 'favorite' : 'favorite_border' }}</span>
            <span class="font-label-bold">{{ likeCount }}</span>
          </button>
          <button @click="openShare" class="flex items-center gap-2 px-4 py-2 rounded-full text-on-surface-variant hover:bg-surface-container transition-colors">
            <span class="material-symbols-outlined">share</span>
            <span class="font-label-bold">{{ t('log.share') }}</span>
          </button>
        </div>
      </div>
    </main>

    <!-- Loading state -->
    <div v-else-if="loading" class="pt-20 px-container-padding flex flex-col items-center justify-center min-h-[60vh]">
      <div class="w-10 h-10 border-3 border-primary/30 border-t-primary rounded-full animate-spin"></div>
      <p class="mt-4 text-tertiary">{{ t('common.loading') }}</p>
    </div>

    <!-- Not found state -->
    <div v-else class="pt-20 px-container-padding flex flex-col items-center justify-center min-h-[60vh]">
      <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">error_outline</span>
      <p class="mt-4 font-title-md text-on-surface-variant">{{ t('log.logNotFound') }}</p>
      <button @click="goBack" class="mt-4 px-6 py-2 bg-primary text-on-primary rounded-full font-label-bold">{{ t('common.back') }}</button>
    </div>

    <Teleport to="body">
      <ShareModal
        v-model:visible="showShareModal"
        :post="log ? { title: log.title, image: (log.imageList && log.imageList[0]) || '', author: t('log.myPetRecords') } : null"
      />
    </Teleport>
  </div>
</template>
