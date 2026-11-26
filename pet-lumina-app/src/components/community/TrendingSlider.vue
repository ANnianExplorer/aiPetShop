<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import type { Topic } from '@/types'

const { t } = useI18n()
const props = defineProps<{
  topics: Topic[]
}>()

let sliderSequence = 0
const headingId = `trending-topics-title-${++sliderSequence}`

const currentIndex = ref(0)
const isDragging = ref(false)
const startX = ref(0)
const scrollLeft = ref(0)
const sectionRef = ref<HTMLElement | null>(null)
const sliderRef = ref<HTMLElement | null>(null)
let autoPlayTimer: ReturnType<typeof setInterval> | null = null

const canGoPrev = computed(() => currentIndex.value > 0)
const canGoNext = computed(() => currentIndex.value < props.topics.length - 1)

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  typeof window.matchMedia === 'function' &&
  window.matchMedia('(prefers-reduced-motion: reduce)').matches

const stopAutoPlay = () => {
  if (autoPlayTimer) {
    clearInterval(autoPlayTimer)
    autoPlayTimer = null
  }
}

const scrollToIndex = (index: number) => {
  const slider = sliderRef.value
  if (!slider) return
  const cardWidth = slider.children[0]?.clientWidth || 0
  const gap = 16
  const left = index * (cardWidth + gap)
  try {
    slider.scrollTo({ left, behavior: prefersReducedMotion() ? 'auto' : 'smooth' })
  } catch {
    slider.scrollLeft = left
  }
}

const startAutoPlay = () => {
  stopAutoPlay()
  if (props.topics.length <= 1 || prefersReducedMotion()) return
  autoPlayTimer = setInterval(() => {
    if (currentIndex.value < props.topics.length - 1) {
      currentIndex.value++
    } else {
      currentIndex.value = 0
    }
    scrollToIndex(currentIndex.value)
  }, 4000)
}

const handleSectionBlur = (event: FocusEvent) => {
  const next = event.relatedTarget as Node | null
  if (next && sectionRef.value?.contains(next)) return
  startAutoPlay()
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

onMounted(() => {
  startAutoPlay()
})

onUnmounted(() => {
  stopAutoPlay()
})
</script>

<template>
  <section
    ref="sectionRef"
    class="mt-4"
    :aria-labelledby="headingId"
    @mouseenter="stopAutoPlay"
    @mouseleave="startAutoPlay"
    @focusin="stopAutoPlay"
    @focusout="handleSectionBlur"
  >
    <div class="flex justify-between items-center mb-md">
      <h2 :id="headingId" class="font-headline-md text-headline-md text-on-surface">{{ t('community.trending') }}</h2>
      <RouterLink
        :to="{ name: 'topicsList' }"
        class="font-label-bold text-label-bold text-primary hover:opacity-70 transition-opacity"
      >
        {{ t('community.viewAll') }}
      </RouterLink>
    </div>

    <div class="relative">
      <div
        ref="sliderRef"
        @touchstart="handleTouchStart"
        @touchmove="handleTouchMove"
        @touchend="handleTouchEnd"
        class="flex gap-md overflow-x-auto no-scrollbar pb-2 scroll-smooth"
      >
        <RouterLink
          v-for="topic in topics"
          :key="topic.id"
          :to="{ name: 'topicDetail', params: { id: topic.id } }"
          :aria-label="t('a11y.topicCard', { title: topic.title })"
          class="block flex-shrink-0 w-72 h-40 rounded-xl relative overflow-hidden shadow-sm cursor-pointer hover:shadow-md transition-all active:scale-[0.98]"
        >
          <img class="absolute inset-0 w-full h-full object-cover" :src="topic.image" alt="" />
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
        </RouterLink>
      </div>

      <button
        v-if="topics.length > 1"
        type="button"
        @click="goToPrev"
        :disabled="!canGoPrev"
        :aria-label="t('a11y.prevTopic')"
        class="absolute left-0 top-1/2 -translate-y-1/2 w-8 h-8 bg-white/80 dark:bg-surface-container/80 backdrop-blur-sm rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform"
        :class="{ 'opacity-0 pointer-events-none': !canGoPrev }"
      >
        <span class="material-symbols-outlined text-sm text-on-surface" aria-hidden="true">chevron_left</span>
      </button>
      <button
        v-if="topics.length > 1"
        type="button"
        @click="goToNext"
        :disabled="!canGoNext"
        :aria-label="t('a11y.nextTopic')"
        class="absolute right-0 top-1/2 -translate-y-1/2 w-8 h-8 bg-white/80 dark:bg-surface-container/80 backdrop-blur-sm rounded-full flex items-center justify-center shadow-md active:scale-90 transition-transform"
        :class="{ 'opacity-0 pointer-events-none': !canGoNext }"
      >
        <span class="material-symbols-outlined text-sm text-on-surface" aria-hidden="true">chevron_right</span>
      </button>
    </div>

    <div v-if="topics.length > 1" class="flex justify-center gap-1.5 mt-3" aria-hidden="true">
      <span
        v-for="(_, index) in topics"
        :key="index"
        class="h-1.5 rounded-full transition-all duration-300"
        :class="currentIndex === index ? 'w-6 bg-primary' : 'w-1.5 bg-on-surface-variant/30'"
      ></span>
    </div>
  </section>
</template>
