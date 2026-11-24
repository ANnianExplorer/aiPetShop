<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { logApi } from '@/api/log'
import LogCard from '@/components/lifelog/LogCard.vue'
import type { LogEntry } from '@/types'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const { currentUser, currentPet } = storeToRefs(userStore)

const goToNotifications = () => {
  router.push({ name: 'notifications' })
}

const categories = computed(() => [
  t('log.all'),
  t('log.daily'),
  t('log.health'),
  t('log.outdoor')
])
const activeCategory = ref('')
const searchQuery = ref('')

const filteredLogs = computed(() => {
  let result = logs.value

  if (activeCategory.value && activeCategory.value !== t('log.all')) {
    result = result.filter(l => (l.tagList || []).some(tag => tag.includes(activeCategory.value)))
  }

  if (searchQuery.value.trim()) {
    const query = searchQuery.value.trim().toLowerCase()
    result = result.filter(l =>
      l.title.toLowerCase().includes(query) ||
      l.content.toLowerCase().includes(query) ||
      (l.tagList || []).some(tag => tag.toLowerCase().includes(query))
    )
  }

  return result
})

const goToNewTopic = () => {
  router.push({ name: 'newLog' })
}

const logs = ref<LogEntry[]>([])
const loading = ref(false)

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await logApi.listPage({ pageSize: 20 })
    logs.value = res?.records || []
  } catch (e) {
    console.error('Failed to fetch logs:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  activeCategory.value = t('log.all')
  fetchLogs()
})
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex justify-between items-center py-md mb-md">
        <div class="flex items-center gap-3">
          <div class="w-8 h-8 rounded-full bg-primary-fixed overflow-hidden border border-primary/10">
            <img :src="currentPet?.avatar" class="w-full h-full object-cover" alt="" />
          </div>
          <h1 class="text-xl font-bold tracking-tighter text-emerald-800 dark:text-emerald-100 font-['Plus_Jakarta_Sans']">PetLumina</h1>
        </div>
        <div class="flex gap-4">
          <button type="button" @click="goToNotifications" :aria-label="t('notification.notifications')" class="material-symbols-outlined text-emerald-700 dark:text-emerald-400 active:scale-95 transition-transform duration-200">notifications</button>
        </div>
      </div>
      <!-- Search Bar Section -->
      <div class="mt-4 mb-6">
        <div class="relative flex items-center bg-surface-container-low rounded-full px-4 py-3 shadow-sm group focus-within:ring-2 focus-within:ring-primary/20 transition-all">
          <span class="material-symbols-outlined text-outline mr-3" aria-hidden="true">search</span>
          <input v-model="searchQuery" type="text" :placeholder="t('log.searchPlaceholder')" :aria-label="t('log.searchPlaceholder')" class="bg-transparent border-none focus:ring-0 w-full text-body-md placeholder:text-outline-variant font-body-md outline-none" />
        </div>
      </div>

      <!-- Category Tabs -->
      <div class="flex gap-3 overflow-x-auto pb-4 no-scrollbar">
        <button
          v-for="cat in categories"
          :key="cat"
          @click="activeCategory = cat"
          class="px-6 py-2 rounded-full font-label-bold whitespace-nowrap shadow-sm transition-colors"
          :class="activeCategory === cat ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-on-surface-variant hover:bg-emerald-50'"
        >
          {{ cat }}
        </button>
      </div>

      <!-- Masonry Grid Layout -->
      <div class="columns-2 gap-card-gutter mt-2">
        <LogCard
          v-for="log in filteredLogs"
          :key="log.id"
          :log="log"
        />
      </div>

      <div v-if="loading" class="flex flex-col items-center justify-center py-20">
        <span class="material-symbols-outlined text-6xl text-primary animate-spin">progress_activity</span>
        <p class="mt-4 font-title-md text-on-surface-variant">{{ t('common.loading') }}</p>
      </div>

      <div v-else-if="filteredLogs.length === 0" class="flex flex-col items-center justify-center py-20">
        <span class="material-symbols-outlined text-6xl text-on-surface-variant opacity-30">edit_note</span>
        <p class="mt-4 font-title-md text-on-surface-variant">{{ t('log.noRecords') }}</p>
      </div>
    </main>

    <!-- Floating Action Button -->
    <button @click="goToNewTopic" class="fixed bottom-24 right-6 w-14 h-14 bg-primary text-on-primary rounded-full flex items-center justify-center shadow-xl z-40 active:scale-90 transition-all">
      <span class="material-symbols-outlined text-3xl">add</span>
    </button>
  </div>
</template>
