<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import type { Topic } from '@/types'

const router = useRouter()
const props = defineProps<{
  topics: Topic[]
}>()

const currentIndex = ref(0)
const isDragging = ref(false)
const startX = ref(0)
const scrollLeft = ref(0)
const sliderRef = ref<HTMLElement | null>(null)
let autoPlayTimer: ReturnType<typeof setInterval> | null = null

const startAutoPlay = () => {
  autoPlayTimer = setInterval(() => {
    if (currentIndex.value < props.topics.length - 1) {
      currentIndex.value++
    } else {
      currentIndex.value = 0
    }
    scrollToIndex(currentIndex.value)
  }, 4000)
}

const stopAutoPlay = () => {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
}

const scrollToIndex = (index: number) => {
  if (sliderRef.value) {
    const cardWidth = sliderRef.value.children[0]?.clientWidth || 0
    const gap = 16
    sliderRef.value.scrollTo({
      left: index * (cardWidth + gap),
      behavior: 'smooth'
    })
  }
}

const goToPrev = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
    scrollToIndex(currentIndex.value)
  }
}

const goToNext = () => {
  if (currentIndex.value < props.topics.length - 1) {
    currentIndex.value++
    scrollToIndex(currentIndex.value)
  }
}

const handleTouchStart = (e: TouchEvent) => {
  isDragging.value = true
  startX.value = e.touches[0].pageX
  if (sliderRef.value) {
    scrollLeft.value = sliderRef.value.scrollLeft
  }
  stopAutoPlay()
}

const handleTouchMove = (e: TouchEvent) => {
  if (!isDragging.value || !sliderRef.value) return
  const x = e.touches[0].pageX
  const walk = startX.value - x
  sliderRef.value.scrollLeft = scrollLeft.value + walk
}

const handleTouchEnd = () => {
  isDragging.value = false
  if (sliderRef.value) {
    const cardWidth = sliderRef.value.children[0]?.clientWidth || 0
    const gap = 16
    currentIndex.value = Math.round(sliderRef.value.scrollLeft / (cardWidth + gap))
  }
  startAutoPlay()
}

const openTopic = (topic: Topic) => {
  router.push({ name: 'topicDetail', params: { id: topic.id } })
}

const viewAll = () => {
  router.push({ name: 'topicsList' })
}

onMounted(() => {
  startAutoPlay()
})

onUnmounted(() => {
  stopAutoPlay()
})
</script>

<template>
  <section class="mt-4">
    <div class="flex justify-between items-center mb-md">
      <h2 class="font-headline-md text-headline-md text-on-surface">热门话题</h2>
      <span @click="viewAll" class="font-label-bold text-label-bold text-primary cursor-pointer hover:opacity-70 transition-opacity">查看全部</span>
    </div>
    
    <div class="relative">
      <div 
        ref="sliderRef"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
        class="flex gap-md overflow-x-auto no-scrollbar pb-2 scroll-smooth"
      >
        <div 
          v-for="topic in topics" 
          :key="topic.id"
          @click="openTopic(topic)"
          class="flex-shrink-0 w-72 h-40 rounded-xl relative overflow-hidden shadow-sm cursor-pointer hover:shadow-md transition-all active:scale-[0.98]"
        >
          <img class="absolute inset-0 w-full h-full object-cover" :src="topic.image" />
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent"></div>
          <div class="absolute bottom-md left-md right-md">
            <span 
              class="text-white px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider mb-xs inline-block"
              :class="topic.category === '指南' ? 'bg-primary/90' : 'bg-secondary/90'"
            >
              {{ topic.category }}
            </span>
            <h3 class="text-white font-title-sm text-title-sm">{{ topic.title }}</h3>
          </div>
        </div>
      </div>

      <button 
        v-if="topics.length > 1"
        @click="goToPrev"
        class="absolute left-0 top-1/2 -translate-y-1/2 w-8 h-8 bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform"
        :class="{ 'opacity-0 pointer-events-none': currentIndex === 0 }"
      >
        <span class="material-symbols-outlined text-sm text-on-surface">chevron_left</span>
      </button>
      <button 
        v-if="topics.length > 1"
        @click="goToNext"
        class="absolute right-0 top-1/2 -translate-y-1/2 w-8 h-8 bg-white/80 backdrop-blur-sm rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform"
        :class="{ 'opacity-0 pointer-events-none': currentIndex === topics.length - 1 }"
      >
        <span class="material-symbols-outlined text-sm text-on-surface">chevron_right</span>
      </button>
    </div>

    <div v-if="topics.length > 1" class="flex justify-center gap-1.5 mt-3">
      <span 
        v-for="(_, index) in topics" 
        :key="index"
        class="h-1.5 rounded-full transition-all duration-300"
        :class="currentIndex === index ? 'w-6 bg-primary' : 'w-1.5 bg-on-surface-variant/30'"
      ></span>
    </div>
  </section>
</template>
