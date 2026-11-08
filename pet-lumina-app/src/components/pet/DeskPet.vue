<script setup lang="ts">
/**
 * 桌宠（档 A：H5 + SVG）。
 *
 * 只用真实数据驱动状态（见 utils/petMood.ts），不编造亲密度；
 * 点击说话、可关闭、尊重 reduced-motion；关闭状态存在 localStorage。
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import { derivePetMood, moodAnimation } from '@/utils/petMood'

const HIDDEN_KEY = 'petlumina-deskpet-hidden'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const { currentPet, unreadNotifications } = storeToRefs(userStore)

const hidden = ref(false)
const speaking = ref(false)
const reduced = ref(false)
let speakTimer: ReturnType<typeof setTimeout> | null = null
let mediaQuery: MediaQueryList | null = null

const mood = computed(() =>
  derivePetMood({
    petName: currentPet.value?.name,
    healthScore: currentPet.value?.healthScore,
    todaySteps: currentPet.value?.todaySteps,
    feedingCount: currentPet.value?.feedingCount,
    feedingTotal: currentPet.value?.feedingTotal,
    unreadReminders: unreadNotifications.value,
  }),
)

const animationClass = computed(() => moodAnimation(mood.value.mood, reduced.value))

const bubble = computed(() => {
  // 说话优先用状态说明，其次回到名字；count 供「有 N 条未读」那条文案用
  return t(mood.value.hintKey, { name: mood.value.name, count: unreadNotifications.value })
})

function onReducedChange(event: MediaQueryListEvent | MediaQueryList) {
  reduced.value = event.matches
}

function speak() {
  speaking.value = true
  if (speakTimer) clearTimeout(speakTimer)
  speakTimer = setTimeout(() => {
    speaking.value = false
  }, 4200)
}

function openChat() {
  router.push({ name: 'chat' })
}

function hidePet() {
  hidden.value = true
  try {
    localStorage.setItem(HIDDEN_KEY, '1')
  } catch {
    // 隐私模式下存不了就算了，下次刷新再出现
  }
}

onMounted(() => {
  try {
    hidden.value = localStorage.getItem(HIDDEN_KEY) === '1'
  } catch {
    hidden.value = false
  }
  if (typeof window !== 'undefined' && window.matchMedia) {
    mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    onReducedChange(mediaQuery)
    mediaQuery.addEventListener('change', onReducedChange)
  }
  // 进页面主动打个招呼：用户不点也知道它「活着」，三秒后自动收起
  speakTimer = setTimeout(() => speak(), 800)
})

onBeforeUnmount(() => {
  if (speakTimer) clearTimeout(speakTimer)
  mediaQuery?.removeEventListener('change', onReducedChange)
})
</script>

<template>
  <Teleport to="body">
    <div v-if="!hidden" class="desk-pet" role="complementary" :aria-label="t('pet.aria')" @click="speak">
    <transition name="pet-pop">
      <button
        v-if="speaking"
        class="pet-bubble"
        type="button"
        @click.stop="openChat"
      >
        {{ bubble }}
      </button>
    </transition>

    <div class="pet-body" :class="animationClass">
      <svg viewBox="0 0 96 96" class="pet-svg" aria-hidden="true">
        <ellipse cx="48" cy="86" rx="26" ry="5" class="pet-shadow" />
        <path
          d="M48 14c16 0 27 12 27 28 0 17-11 30-27 30S21 59 21 42c0-16 11-28 27-28z"
          class="pet-fur"
        />
        <path d="M30 18l-7-11 15 6z" class="pet-fur pet-ear" />
        <path d="M66 18l7-11-15 6z" class="pet-fur pet-ear" />
        <ellipse cx="48" cy="52" rx="16" ry="13" class="pet-face" />
        <g class="pet-eyes">
          <circle cx="41" cy="45" r="2.6" class="pet-eye" />
          <circle cx="55" cy="45" r="2.6" class="pet-eye" />
        </g>
        <path d="M45 52h6l-3 3z" class="pet-nose" />
        <path d="M44 57c1.6 2 6.4 2 8 0" class="pet-mouth" />
        <circle cx="32" cy="52" r="3.4" class="pet-cheek" />
        <circle cx="64" cy="52" r="3.4" class="pet-cheek" />
      </svg>
      <span v-if="mood.mood === 'sleepy'" class="pet-zzz" aria-hidden="true">z</span>
    </div>

    <button class="pet-close" type="button" :aria-label="t('pet.hide')" @click.stop="hidePet">
      <span class="material-symbols-outlined">close</span>
    </button>
    </div>
  </Teleport>
</template>

<style scoped>
.desk-pet {
  position: fixed;
  /* 避开右下角的「新建提醒」FAB（56px 宽、right 20px）与底部胶囊导航 */
  right: 84px;
  bottom: 104px;
  z-index: 45;
  width: 96px;
  pointer-events: auto;
  cursor: pointer;
}

.pet-body {
  pointer-events: auto;
  cursor: pointer;
  transition: transform 160ms ease;
  transform-origin: center bottom;
}.pet-body:active {
  transform: scale(0.94);
}

.pet-svg {
  width: 96px;
  height: 96px;
  filter: drop-shadow(0 8px 14px rgba(75, 100, 85, 0.22));
}
.pet-fur {
  fill: var(--color-primary, #4d6b57);
}
.pet-ear {
  fill: var(--color-primary, #4d6b57);
}
.pet-face {
  fill: #f6f3ea;
}
.pet-eye {
  fill: #2b3a30;
}
.pet-nose {
  fill: #d98d8d;
}
.pet-mouth {
  fill: none;
  stroke: #2b3a30;
  stroke-width: 1.6;
  stroke-linecap: round;
}
.pet-cheek {
  fill: #f0b7b7;
  opacity: 0.75;
}
.pet-shadow {
  fill: rgba(43, 58, 48, 0.12);
}
.pet-zzz {
  position: absolute;
  right: 4px;
  top: 2px;
  font-size: 14px;
  font-weight: 700;
  color: var(--color-primary, #4d6b57);
  animation: pet-zzz-float 2.6s ease-in-out infinite;
}

.pet-bubble {
  position: absolute;
  right: 8px;
  bottom: 100%;
  margin-bottom: 8px;
  width: 168px;
  padding: 8px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  color: #2b3a30;
  font-size: 12px;
  line-height: 1.4;
  text-align: left;
  box-shadow: 0 6px 18px rgba(75, 100, 85, 0.16);
  pointer-events: auto;
}
.dark .pet-bubble {
  background: rgba(38, 48, 42, 0.94);
  color: #eef3ee;
}

.pet-close {
  position: absolute;
  top: -6px;
  left: -6px;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: #6b7a70;
  display: grid;
  place-items: center;
  pointer-events: auto;
}
.pet-close .material-symbols-outlined {
  font-size: 14px;
}

.pet-pop-enter-active,
.pet-pop-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}
.pet-pop-enter-from,
.pet-pop-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

/* 动画：全部是纯 CSS，减少动效时由 pet-static 覆盖 */
.pet-bounce {
  animation: pet-bounce 1.8s ease-in-out infinite;
}
.pet-breathe {
  animation: pet-breathe 3.4s ease-in-out infinite;
}
.pet-wiggle {
  animation: pet-wiggle 2.2s ease-in-out infinite;
}
.pet-shake {
  animation: pet-shake 2.6s ease-in-out infinite;
}
.pet-blink .pet-eyes {
  animation: pet-blink 4.2s ease-in-out infinite;
}
.pet-static,
.pet-static .pet-eyes,
.pet-static .pet-zzz {
  animation: none !important;
}

@keyframes pet-bounce {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-6px);
  }
}
@keyframes pet-breathe {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.04);
  }
}
@keyframes pet-wiggle {
  0%,
  100% {
    transform: rotate(0deg);
  }
  30% {
    transform: rotate(-3deg);
  }
  60% {
    transform: rotate(3deg);
  }
}
@keyframes pet-shake {
  0%,
  100% {
    transform: translateX(0);
  }
  20% {
    transform: translateX(-2px);
  }
  40% {
    transform: translateX(2px);
  }
  60% {
    transform: translateX(-1px);
  }
}
@keyframes pet-blink {
  0%,
  92%,
  100% {
    opacity: 1;
  }
  95% {
    opacity: 0.1;
  }
}
@keyframes pet-zzz-float {
  0% {
    opacity: 0;
    transform: translateY(4px);
  }
  40% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    transform: translateY(-10px);
  }
}

@media (prefers-reduced-motion: reduce) {
  .pet-bounce,
  .pet-breathe,
  .pet-wiggle,
  .pet-shake,
  .pet-blink .pet-eyes,
  .pet-zzz {
    animation: none;
  }
}
</style>
