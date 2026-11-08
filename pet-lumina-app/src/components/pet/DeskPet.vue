<script setup lang="ts">
/**
 * 桌宠外壳：位置 / 视线 / 拖拽 / 气泡 / 爱心 / 隐藏。
 *
 * 角色本体在 ChibiPet.vue（纯展示 + CSS 部件动画）；这里只负责"反应"：
 * 指针移动 → 瞳孔与头部偏移；单击 → 跳跃 + 爱心 + 说一句；拖拽 → 换位并记住；
 * 双击 → 收起。所有定时器与监听在卸载时清理。
 */
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import { derivePetMood } from '@/utils/petMood'
import {
  GAZE_LIMIT,
  clamp,
  movedEnough,
  normalizeGaze,
  smooth,
} from '@/utils/petMotion'
import ChibiPet from '@/components/pet/ChibiPet.vue'
import { loadSprite, type PetSprite } from '@/utils/petSpriteStore'

const HIDDEN_KEY = 'petlumina-deskpet-hidden'
const POS_KEY = 'petlumina-deskpet-pos'
const PET_WIDTH = 132
const PET_HEIGHT = 158
const EDGE = 12

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const { currentPet, unreadNotifications } = storeToRefs(userStore)

const hidden = ref(false)
const speaking = ref(false)
const reduced = ref(false)
const dragging = ref(false)
const pos = ref({ right: 84, bottom: 104 })
const gaze = ref({ x: 0, y: 0 })
const hearts = ref<{ id: number; x: number }[]>([])
const rootEl = ref<HTMLElement | null>(null)
/** 用户用自己图片生成的桌宠；为空时回退到内置角色 */
const sprite = ref<PetSprite | null>(null)

let speakTimer: ReturnType<typeof setTimeout> | null = null
let mediaQuery: MediaQueryList | null = null
let gazeTarget = { x: 0, y: 0 }
let rafId: number | null = null
let heartSeq = 0
let dragStart = { x: 0, y: 0, right: 0, bottom: 0, moved: false }
const heartTimers: ReturnType<typeof setTimeout>[] = []

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

const sleeping = computed(() => mood.value.mood === 'sleepy')

const bubble = computed(() =>
  t(mood.value.hintKey, { name: mood.value.name, count: unreadNotifications.value }),
)

const rootStyle = computed(() => ({
  right: `${pos.value.right}px`,
  bottom: `${pos.value.bottom}px`,
  width: `${PET_WIDTH}px`,
  height: `${PET_HEIGHT}px`,
}))

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
    // 隐私模式存不了就算了，下次刷新再出现
  }
}

/** 视线的平滑推进：用 rAF 而不是 pointermove 里直接改，避免高频重排。 */
function stepGaze() {
  const nx = smooth(gaze.value.x, gazeTarget.x, 0.18)
  const ny = smooth(gaze.value.y, gazeTarget.y, 0.18)
  if (nx !== gaze.value.x || ny !== gaze.value.y) {
    gaze.value = { x: nx, y: ny }
  }
  rafId = requestAnimationFrame(stepGaze)
}

function onPointerMove(event: PointerEvent) {
  if (dragging.value) {
    const dx = event.clientX - dragStart.x
    const dy = event.clientY - dragStart.y
    if (!dragStart.moved && movedEnough(dx, dy)) dragStart.moved = true
    if (dragStart.moved) {
      pos.value = {
        right: clamp(dragStart.right - dx, EDGE, window.innerWidth - PET_WIDTH - EDGE),
        bottom: clamp(dragStart.bottom - dy, EDGE, window.innerHeight - PET_HEIGHT - EDGE),
      }
    }
    return
  }
  const el = rootEl.value
  if (!el) return
  gazeTarget = normalizeGaze(el.getBoundingClientRect(), event.clientX, event.clientY, GAZE_LIMIT)
}

function onPointerDown(event: PointerEvent) {
  dragStart = {
    x: event.clientX,
    y: event.clientY,
    right: pos.value.right,
    bottom: pos.value.bottom,
    moved: false,
  }
  dragging.value = true
  ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
}

function onPointerUp() {
  const wasDrag = dragStart.moved
  dragging.value = false
  if (wasDrag) {
    try {
      localStorage.setItem(POS_KEY, JSON.stringify(pos.value))
    } catch {
      // 存不了位置不影响使用
    }
    return
  }
  // 单击：跳跃 + 爱心 + 说一句
  jump()
  spawnHearts()
  speak()
}

function jump() {
  const el = rootEl.value
  // jsdom / 老浏览器没有 Element.animate：动画降级，但点击反馈（爱心 + 气泡）照常
  if (!el || reduced.value || typeof el.animate !== 'function') return
  el.animate(
    [
      { transform: 'translateY(0) scale(1, 1)' },
      { transform: 'translateY(-10px) scale(0.97, 1.03)', offset: 0.35 },
      { transform: 'translateY(0) scale(1.03, 0.97)', offset: 0.7 },
      { transform: 'translateY(0) scale(1, 1)' },
    ],
    { duration: 420, easing: 'ease-out' },
  )
}

function spawnHearts() {
  if (reduced.value) return
  for (let i = 0; i < 3; i += 1) {
    const heart = { id: (heartSeq += 1), x: 30 + Math.round(Math.random() * 50) }
    hearts.value.push(heart)
    const timer = setTimeout(() => {
      hearts.value = hearts.value.filter((h) => h.id !== heart.id)
    }, 1100)
    heartTimers.push(timer)
  }
}

function onDoubleClick() {
  hidePet()
}

onMounted(() => {
  sprite.value = loadSprite()
  try {
    hidden.value = localStorage.getItem(HIDDEN_KEY) === '1'
    const saved = localStorage.getItem(POS_KEY)
    if (saved) {
      const parsed = JSON.parse(saved) as { right?: number; bottom?: number }
      if (typeof parsed.right === 'number' && typeof parsed.bottom === 'number') {
        pos.value = {
          right: clamp(parsed.right, EDGE, window.innerWidth - PET_WIDTH - EDGE),
          bottom: clamp(parsed.bottom, EDGE, window.innerHeight - PET_HEIGHT - EDGE),
        }
      }
    }
  } catch {
    // 读不到就用默认位置
  }
  if (typeof window !== 'undefined' && window.matchMedia) {
    mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    onReducedChange(mediaQuery)
    mediaQuery.addEventListener('change', onReducedChange)
  }
  window.addEventListener('pointermove', onPointerMove, { passive: true })
  rafId = requestAnimationFrame(stepGaze)
  // 进页面先打个招呼：不点也知道它「活着」
  speakTimer = setTimeout(() => speak(), 800)
})

onBeforeUnmount(() => {
  if (speakTimer) clearTimeout(speakTimer)
  if (rafId !== null) cancelAnimationFrame(rafId)
  heartTimers.forEach((timer) => clearTimeout(timer))
  mediaQuery?.removeEventListener('change', onReducedChange)
  window.removeEventListener('pointermove', onPointerMove)
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="!hidden"
      ref="rootEl"
      class="desk-pet"
      :class="{ dragging }"
      :style="rootStyle"
      role="complementary"
      :aria-label="t('pet.aria')"
      @pointerdown="onPointerDown"
      @pointerup="onPointerUp"
      @pointercancel="onPointerUp"
      @dblclick="onDoubleClick"
    >
      <transition name="pet-pop">
        <button v-if="speaking" class="pet-bubble" type="button" @pointerdown.stop @click.stop="openChat">
          {{ bubble }}
        </button>
      </transition>

      <span
        v-for="heart in hearts"
        :key="heart.id"
        class="pet-heart"
        :style="{ left: `${heart.x}%` }"
        aria-hidden="true"
      >♥</span>

      <span v-if="sprite" class="pet-sprite-wrap" :class="{ sleeping }" aria-hidden="true">
        <img class="pet-sprite" :src="sprite.dataUrl" :alt="mood.name" draggable="false" />
        <span class="pet-sprite-shadow" />
      </span>

      <ChibiPet
        v-else
        class="pet-character"
        :mood="mood.mood"
        :gaze-x="gaze.x"
        :gaze-y="gaze.y"
        :sleeping="sleeping"
        :reduced-motion="reduced"
      />

      <button
        class="pet-close"
        type="button"
        :aria-label="t('pet.hide')"
        @pointerdown.stop
        @click.stop="hidePet"
      >
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>
  </Teleport>
</template>

<style scoped>
.desk-pet {
  position: fixed;
  z-index: 45;
  pointer-events: auto;
  cursor: grab;
  touch-action: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  transform-origin: center bottom;
}
.desk-pet.dragging {
  cursor: grabbing;
  transition: none;
}

.pet-character {
  width: 100%;
  height: 100%;
}

/* ── 用户图片生成的精灵图：整图级动效（无骨骼，因此只做呼吸/摇摆/影子） ── */
.pet-sprite-wrap {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.pet-sprite {
  max-width: 100%;
  max-height: 100%;
  transform-origin: 50% 100%;
  animation: sprite-breathe 3.8s ease-in-out infinite;
  filter: drop-shadow(0 6px 10px rgba(0, 0, 0, 0.14));
  pointer-events: none;
}

.pet-sprite-shadow {
  position: absolute;
  bottom: 0;
  width: 52%;
  height: 9px;
  border-radius: 50%;
  background: radial-gradient(closest-side, rgba(0, 0, 0, 0.22), transparent);
  animation: sprite-shadow 3.8s ease-in-out infinite;
  pointer-events: none;
}

.pet-sprite-wrap.sleeping .pet-sprite {
  animation-duration: 6.4s;
  opacity: 0.92;
}

@keyframes sprite-breathe {
  0%, 100% { transform: scale(1, 1) rotate(-1.1deg); }
  50% { transform: scale(1.02, 0.985) rotate(1.1deg); }
}

@keyframes sprite-shadow {
  0%, 100% { transform: scaleX(1); opacity: 0.85; }
  50% { transform: scaleX(0.88); opacity: 0.55; }
}

.pet-bubble {
  position: absolute;
  right: 6px;
  bottom: calc(100% - 6px);
  width: 186px;
  padding: 8px 12px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.94);
  color: #2b3a30;
  font-size: 12px;
  line-height: 1.45;
  text-align: left;
  box-shadow: 0 8px 22px rgba(75, 100, 85, 0.18);
  backdrop-filter: blur(6px);
}
.dark .pet-bubble {
  background: rgba(38, 48, 42, 0.94);
  color: #eef3ee;
}

.pet-close {
  position: absolute;
  top: 2px;
  right: 0;
  width: 20px;
  height: 20px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.88);
  color: #6b7a70;
  display: grid;
  place-items: center;
  opacity: 0;
  transition: opacity 160ms ease;
}
.desk-pet:hover .pet-close {
  opacity: 1;
}
.pet-close .material-symbols-outlined {
  font-size: 13px;
}

.pet-heart {
  position: absolute;
  bottom: 42%;
  font-size: 13px;
  color: #ef8fa4;
  pointer-events: none;
  animation: pet-heart-rise 1.1s ease-out forwards;
}
@keyframes pet-heart-rise {
  0% { opacity: 0; transform: translateY(0) scale(0.6); }
  25% { opacity: 1; }
  100% { opacity: 0; transform: translateY(-38px) scale(1.05) rotate(8deg); }
}

.pet-pop-enter-active,
.pet-pop-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}
.pet-pop-enter-from,
.pet-pop-leave-to {
  opacity: 0;
  transform: translateY(6px) scale(0.96);
}
</style>
