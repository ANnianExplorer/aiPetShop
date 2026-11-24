<script setup lang="ts">
/**
 * 桌宠外壳：把引擎挂到页面上，负责文案、气泡、菜单与持久化。
 *
 * 动画/物理/状态机都在 `@/pet`（纯逻辑，可单测）；这里只做四件事：
 * 建引擎、把指针事件喂给它、把「该说什么」翻译成 i18n 文案、记住用户把它拖到哪了。
 *
 * 形象来源：用户在 `/pet-studio` 用自己的图生成过精灵图就用它；否则按当前宠物类型
 * 选内置形象（猫 / 柴犬 / 兔子），不再让所有用户都看同一个角色。
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import { derivePetMood } from '@/utils/petMood'
import { defaultSpriteForPetType, spriteKindForPetType } from '@/utils/petSprite'
import { loadSprite } from '@/utils/petSpriteStore'
import { createDeskPetEngine, subscribeWorkState, type DeskPetEngine } from '@/pet'
import type { WorkState } from '@/pet/types'

const HIDDEN_KEY = 'petlumina-deskpet-hidden'
const POS_KEY = 'petlumina-deskpet-pos-v2'
/** 盒宽上下限：手机上大约一屏宽的 1/3，桌面上封顶 160。 */
const MIN_SIZE = 112
const MAX_SIZE = 160
/** 长按判定（ms）。 */
const LONG_PRESS_MS = 520
/** 右键菜单尺寸：用于把菜单夹在视口内，别让最右边那只宠物把菜单顶出屏幕。 */
const MENU_WIDTH = 204
const MENU_HEIGHT = 232

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { currentPet, unreadNotifications } = storeToRefs(userStore)

/** 登录/注册页不挂桌宠：还没登录就没有「它的宠物」，飘个角色在上面很出戏。 */
const PUBLIC_PATHS = ['/login', '/sign-up', '/reset-password']

const rootEl = ref<HTMLElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
const menuEl = ref<HTMLElement | null>(null)
const hidden = ref(false)
const bubbleText = ref('')
const menuOpen = ref(false)
const menuPoint = ref<{ x: number; y: number } | null>(null)
const sleeping = ref(false)
const reduced = ref(false)
const engineRef = shallowRef<DeskPetEngine | null>(null)
let boxSize = MIN_SIZE

const isPublic = computed(() => PUBLIC_PATHS.includes(route.path))
const visible = computed(() => !hidden.value && !isPublic.value)
const spriteKind = computed(() => spriteKindForPetType(currentPet.value?.type))
const petAria = computed(() =>
  currentPet.value?.name
    ? t('pet.ariaNamed', { name: currentPet.value.name })
    : t('pet.aria'),
)

type PetMenuAction = 'eat' | 'dance' | 'spin' | 'stretch' | 'pat' | 'sleep' | 'wake' | 'chat' | 'hide'

interface PetMenuItem {
  id: PetMenuAction
  icon: string
  label: string
  disabled: boolean
}

/** 右键/长按菜单：动作全部走引擎已有的片段，不额外造动画。 */
const menuItems = computed<PetMenuItem[]>(() => {
  const locked = sleeping.value
  const items: PetMenuItem[] = [
    { id: 'eat', icon: 'restaurant', label: t('pet.menu.eat'), disabled: locked },
    { id: 'dance', icon: 'music_note', label: t('pet.menu.dance'), disabled: locked },
    { id: 'spin', icon: 'cycle', label: t('pet.menu.spin'), disabled: locked },
    { id: 'stretch', icon: 'accessibility_new', label: t('pet.menu.stretch'), disabled: locked },
    { id: 'pat', icon: 'pets', label: t('pet.menu.pat'), disabled: locked },
    locked
      ? { id: 'wake', icon: 'wb_sunny', label: t('pet.menu.wake'), disabled: false }
      : { id: 'sleep', icon: 'bedtime', label: t('pet.menu.sleep'), disabled: false },
    { id: 'chat', icon: 'chat', label: t('pet.menu.chat'), disabled: false },
    { id: 'hide', icon: 'visibility_off', label: t('pet.menu.hide'), disabled: false },
  ]
  return items
})

const menuStyle = computed(() =>
  menuPoint.value
    ? { left: `${menuPoint.value.x}px`, top: `${menuPoint.value.y}px` }
    : {},
)

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

const moodLine = computed(() =>
  t(mood.value.hintKey, { name: mood.value.name, count: unreadNotifications.value }),
)

let bubbleTimer: ReturnType<typeof setTimeout> | null = null
let ambientTimer: ReturnType<typeof setInterval> | null = null
let workResetTimer: ReturnType<typeof setTimeout> | null = null
let mediaQuery: MediaQueryList | null = null
let unsubscribe: (() => void) | null = null
let pressTimer: ReturnType<typeof setTimeout> | null = null
let pointerState = { down: false, moved: false, x: 0, y: 0, longPressed: false }

/** 说一句话；时长与动画互不绑定（气泡是独立槽位）。 */
function say(text: string, durationMs = 4200): void {
  bubbleText.value = text
  if (bubbleTimer) clearTimeout(bubbleTimer)
  bubbleTimer = setTimeout(() => {
    bubbleText.value = ''
  }, durationMs)
}

/** 点一下说什么：短句轮换，不要太啰嗦。 */
function tapLine(): string {
  const lines = [t('pet.say.tap1'), t('pet.say.tap2'), t('pet.say.tap3'), t('pet.say.tap4')]
  return lines[Math.floor(Math.random() * lines.length)]
}

function workLine(state: WorkState): string {
  return t(`pet.work.${state}`)
}

function openChat(): void {
  router.push({ name: 'chat' })
}

function hidePet(): void {
  hidden.value = true
  try {
    localStorage.setItem(HIDDEN_KEY, '1')
  } catch {
    // 隐私模式存不了就算了，下次刷新再出现
  }
}

function pickSize(): number {
  const width = typeof window === 'undefined' ? 390 : window.innerWidth
  return Math.min(MAX_SIZE, Math.max(MIN_SIZE, Math.round(width * 0.34)))
}

/** 把引擎当前尺寸写回根节点（气泡与命中区都按它定位）。 */
function syncBox(): void {
  const root = rootEl.value
  if (root === null) return
  root.style.width = `${boxSize}px`
  root.style.height = `${Math.round(boxSize * 1.26)}px`
}

function restorePosition(engine: DeskPetEngine): void {
  try {
    const raw = localStorage.getItem(POS_KEY)
    if (raw === null) {
      engine.home('bottom-right', { x: 16, y: 84 })
      return
    }
    const saved = JSON.parse(raw) as { rx?: number; ry?: number }
    if (typeof saved.rx !== 'number' || typeof saved.ry !== 'number') {
      engine.home('bottom-right', { x: 16, y: 84 })
      return
    }
    const x = saved.rx * window.innerWidth - boxSize / 2
    const y = saved.ry * window.innerHeight - (boxSize * 1.26) / 2
    engine.motion.place(x, y)
  } catch {
    engine.home('bottom-right', { x: 16, y: 84 })
  }
}

function persistPosition(position: { rx: number; ry: number }): void {
  try {
    localStorage.setItem(POS_KEY, JSON.stringify(position))
  } catch {
    // 存不了位置不影响使用
  }
}

function onReducedChange(event: MediaQueryListEvent | MediaQueryList): void {
  reduced.value = event.matches
  engineRef.value?.setReducedMotion(event.matches)
}

/** 指针：拖拽交给引擎，长按开菜单，短按由引擎自己判定为「点一下」。 */
function onPointerDown(event: PointerEvent): void {
  if (event.button !== undefined && event.button !== 0) return
  const engine = engineRef.value
  if (engine === null) return
  pointerState = { down: true, moved: false, x: event.clientX, y: event.clientY, longPressed: false }
  engine.beginDrag(event.clientX, event.clientY, performance.now())
  ;(event.currentTarget as HTMLElement).setPointerCapture?.(event.pointerId)
  if (pressTimer) clearTimeout(pressTimer)
  pressTimer = setTimeout(() => {
    if (!pointerState.moved) {
      pointerState.longPressed = true
      openPetMenu()
    }
  }, LONG_PRESS_MS)
}

function onPointerMove(event: PointerEvent): void {
  if (!pointerState.down) return
  const dx = event.clientX - pointerState.x
  const dy = event.clientY - pointerState.y
  if (!pointerState.moved && Math.hypot(dx, dy) > 6) pointerState.moved = true
  engineRef.value?.moveDrag(event.clientX, event.clientY, performance.now())
}

function onPointerUp(event: PointerEvent): void {
  if (!pointerState.down) return
  pointerState.down = false
  if (pressTimer) clearTimeout(pressTimer)
  engineRef.value?.endDrag(performance.now())
  if (menuOpen.value) event.stopPropagation()
}

function onWindowMove(event: PointerEvent): void {
  onPointerMove(event)
}

function onWindowUp(event: PointerEvent): void {
  onPointerUp(event)
}

function onWindowResize(): void {
  const next = pickSize()
  if (next !== boxSize) {
    boxSize = next
    syncBox()
    engineRef.value?.setSize(boxSize)
  }
  syncBox()
  engineRef.value?.resize()
}

/** 引擎不向外抛睡眠事件；每次开菜单前读一次运行时，菜单标签就不会停在旧状态。 */
function syncSleeping(): void {
  sleeping.value = engineRef.value?.runtime.sleeping !== null
}

function clampMenu(x: number, y: number): { x: number; y: number } {
  const maxX = Math.max(8, window.innerWidth - MENU_WIDTH - 8)
  const maxY = Math.max(8, window.innerHeight - MENU_HEIGHT - 8)
  return {
    x: Math.min(Math.max(8, x), maxX),
    y: Math.min(Math.max(8, y), maxY),
  }
}

/** 右键 / 长按 / 键盘统一贴着宠物上方展开，别把刚点的那只盖住。 */
function menuAnchor(): { x: number; y: number } {
  const rect = rootEl.value?.getBoundingClientRect()
  if (rect === undefined) {
    return clampMenu(window.innerWidth - MENU_WIDTH - 16, window.innerHeight - MENU_HEIGHT - 96)
  }
  return clampMenu(rect.right - MENU_WIDTH, rect.top - MENU_HEIGHT - 8)
}

function openPetMenu(): void {
  syncSleeping()
  bubbleText.value = ''
  menuPoint.value = menuAnchor()
  menuOpen.value = true
}

function openMenuFromKeyboard(): void {
  openPetMenu()
  void nextTick(() => {
    menuEl.value?.querySelector<HTMLButtonElement>('button:not(:disabled)')?.focus()
  })
}

function onPetKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Enter' && event.key !== 'ContextMenu' && !(event.shiftKey && event.key === 'F10')) return
  event.preventDefault()
  openMenuFromKeyboard()
}

function closeMenu(restoreFocus = false): void {
  menuOpen.value = false
  if (restoreFocus) rootEl.value?.focus()
}

function onDocumentPointerDown(event: PointerEvent): void {
  if (!menuOpen.value) return
  const target = event.target as Node | null
  if (target === null) return
  if (menuEl.value?.contains(target) || rootEl.value?.contains(target)) return
  closeMenu()
}

function onWindowKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Escape' || !menuOpen.value) return
  event.preventDefault()
  closeMenu(true)
}

/** 播一段动作；睡着时引擎会拒绝，菜单那边已经禁用了，这里再做一层兜底。 */
function playMenuClip(clipId: string, sayKey: string): void {
  if (engineRef.value?.playAction(clipId) !== true) return
  say(t(sayKey))
}

/** 菜单动作：吃饭 / 跳舞 / 转圈 / 伸懒腰 / 摸头 / 睡觉 / 醒来 / 聊天 / 收起。 */
function menuAction(action: PetMenuAction): void {
  closeMenu()
  if (action === 'chat') {
    openChat()
    return
  }
  if (action === 'hide') {
    hidePet()
    return
  }
  const engine = engineRef.value
  if (engine === null) return
  switch (action) {
    case 'eat':
      playMenuClip('act.eat', 'pet.say.eat')
      return
    case 'dance':
      playMenuClip('act.dance', 'pet.say.dance')
      return
    case 'spin':
      playMenuClip('act.spin', 'pet.say.spin')
      return
    case 'stretch':
      playMenuClip('act.stretch', 'pet.say.stretch')
      return
    case 'pat':
      playMenuClip('click.pat', 'pet.say.pat')
      return
    case 'sleep':
      engine.sleep()
      sleeping.value = true
      say(t('pet.say.sleep'))
      return
    case 'wake':
      engine.wake()
      sleeping.value = false
      say(t('pet.say.wake'))
      return
  }
}

function mountPet(): void {
  if (engineRef.value !== null) return
  if (typeof window !== 'undefined' && window.matchMedia) {
    mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    onReducedChange(mediaQuery)
    mediaQuery.addEventListener('change', onReducedChange)
  }
  const canvas = canvasEl.value
  const root = rootEl.value
  if (canvas === null || root === null) return
  boxSize = pickSize()
  syncBox()
  const engine = createDeskPetEngine({
    canvas,
    root,
    size: boxSize,
    onSay: (text, durationMs) => say(text, durationMs),
    onTap: () => say(tapLine()),
    onActivate: () => openChat(),
    onPosition: persistPosition,
    onHaptic: () => {
      if (typeof navigator !== 'undefined' && typeof navigator.vibrate === 'function') {
        navigator.vibrate(8)
      }
    },
  })
  engineRef.value = engine
  engine.setReducedMotion(reduced.value)
  const sprite = loadSprite()
  engine.setSprite(sprite?.dataUrl ?? defaultSpriteForPetType(currentPet.value?.type))
  restorePosition(engine)
  engine.start()
  window.addEventListener('pointermove', onWindowMove, { passive: true })
  window.addEventListener('pointerup', onWindowUp)
  window.addEventListener('pointercancel', onWindowUp)
  window.addEventListener('resize', onWindowResize)
  window.addEventListener('keydown', onWindowKeydown)
  document.addEventListener('pointerdown', onDocumentPointerDown, true)
  unsubscribe = subscribeWorkState((state) => {
    engine.setWorkState(state)
    if (state !== null) {
      say(workLine(state), 5200)
      if (workResetTimer) clearTimeout(workResetTimer)
      if (state === 'success' || state === 'error') {
        // 终态亮两秒再收：只闪一下等于没反馈
        workResetTimer = setTimeout(() => engine.setWorkState(null), 2600)
      }
    }
  })
  // 进页面先打个招呼
  say(moodLine.value, 5200)
  // 碎碎念：不点也知道它活着；睡着时 speak 只弹气泡不动画
  ambientTimer = setInterval(() => {
    if (pointerState.down || menuOpen.value) return
    engine.speak(moodLine.value, 4600)
  }, 28_000)
}

function unmountPet(): void {
  if (bubbleTimer) clearTimeout(bubbleTimer)
  if (ambientTimer) clearInterval(ambientTimer)
  if (workResetTimer) clearTimeout(workResetTimer)
  if (pressTimer) clearTimeout(pressTimer)
  bubbleTimer = null
  ambientTimer = null
  workResetTimer = null
  pressTimer = null
  mediaQuery?.removeEventListener('change', onReducedChange)
  mediaQuery = null
  unsubscribe?.()
  unsubscribe = null
  engineRef.value?.destroy()
  engineRef.value = null
  window.removeEventListener('pointermove', onWindowMove)
  window.removeEventListener('pointerup', onWindowUp)
  window.removeEventListener('pointercancel', onWindowUp)
  window.removeEventListener('resize', onWindowResize)
  window.removeEventListener('keydown', onWindowKeydown)
  document.removeEventListener('pointerdown', onDocumentPointerDown, true)
  bubbleText.value = ''
  menuOpen.value = false
  menuPoint.value = null
}

onMounted(() => {
  try {
    hidden.value = localStorage.getItem(HIDDEN_KEY) === '1'
  } catch {
    hidden.value = false
  }
  if (visible.value) mountPet()
})

// 登录页 ↔ 应用内切换时重建/销毁：桌宠跟着「有没有登录进来看」走
watch(isPublic, async (pub) => {
  if (pub) {
    unmountPet()
    return
  }
  await nextTick()
  mountPet()
})

// 切换宠物（猫/狗/其他）时换内置形象；自定义精灵图仍然优先。
watch(
  () => currentPet.value?.type,
  () => {
    const engine = engineRef.value
    if (engine === null) return
    const custom = loadSprite()
    engine.setSprite(custom?.dataUrl ?? defaultSpriteForPetType(currentPet.value?.type))
  },
)

onBeforeUnmount(() => {
  unmountPet()
})
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="desk-pet-wrap">
      <div
        ref="rootEl"
        class="desk-pet"
        role="complementary"
        tabindex="0"
        :aria-label="petAria"
        :title="t('pet.menu.hint')"
        :data-sprite-kind="spriteKind"
        @pointerdown="onPointerDown"
        @pointermove="onPointerMove"
        @pointerup="onPointerUp"
        @pointercancel="onPointerUp"
        @contextmenu.prevent.stop="openPetMenu"
        @keydown="onPetKeydown"
      >
        <canvas ref="canvasEl" class="desk-pet-canvas" aria-hidden="true" />

        <transition name="pet-pop">
          <button
            v-if="bubbleText"
            class="pet-bubble"
            type="button"
            @pointerdown.stop
            @click.stop="openChat"
          >
            {{ bubbleText }}
          </button>
        </transition>

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
    </div>

    <transition name="pet-pop">
      <div
        v-if="visible && menuOpen"
        ref="menuEl"
        class="pet-menu"
        role="group"
        :aria-label="t('pet.menu.title')"
        :style="menuStyle"
        @pointerdown.stop
        @contextmenu.prevent
      >
        <button
          v-for="item in menuItems"
          :key="item.id"
          type="button"
          :disabled="item.disabled"
          @click="menuAction(item.id)"
        >
          <span class="material-symbols-outlined" aria-hidden="true">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </button>
      </div>
    </transition>
  </Teleport>
</template>

<style scoped>
.desk-pet-wrap {
  position: fixed;
  left: 0;
  top: 0;
  z-index: 45;
  pointer-events: none;
}

.desk-pet {
  position: absolute;
  left: 0;
  top: 0;
  pointer-events: auto;
  cursor: grab;
  touch-action: none;
  user-select: none;
  -webkit-tap-highlight-color: transparent;
  will-change: transform;
}
.desk-pet:active {
  cursor: grabbing;
}

.desk-pet-canvas {
  display: block;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.pet-bubble {
  position: absolute;
  right: 0;
  bottom: calc(100% - 10px);
  width: 176px;
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

.pet-menu {
  position: fixed;
  z-index: 46;
  width: 204px;
  padding: 8px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 12px 30px rgba(60, 82, 70, 0.26);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px;
  backdrop-filter: blur(8px);
}
.dark .pet-menu {
  background: rgba(38, 48, 42, 0.97);
}
.pet-menu button {
  min-height: 48px;
  padding: 6px 4px;
  border-radius: 11px;
  font-size: 11px;
  line-height: 1.2;
  color: #35473c;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
}
.pet-menu button .material-symbols-outlined {
  font-size: 18px;
  max-width: 100%;
  overflow: hidden;
  white-space: nowrap;
}
.pet-menu button:hover:not(:disabled) {
  background: rgba(111, 174, 147, 0.16);
}
.pet-menu button:disabled {
  color: #a9b6ac;
  cursor: default;
}
.dark .pet-menu button {
  color: #e3ebe5;
}
.dark .pet-menu button:disabled {
  color: #6f7c73;
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

.pet-pop-enter-active,
.pet-pop-leave-active {
  transition: opacity 180ms ease, transform 180ms ease;
}
.pet-pop-enter-from,
.pet-pop-leave-to {
  opacity: 0;
  transform: translateY(6px) scale(0.96);
}

/* 减少动效：不关引擎，只把过场与光标反馈收掉（逻辑照跑，晕动症用户也不会被闪到） */
@media (prefers-reduced-motion: reduce) {
  .pet-bubble,
  .pet-menu {
    transition: none;
  }
}
</style>
