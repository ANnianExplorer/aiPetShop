/**
 * 桌宠引擎：把「片段 + 状态机 + 物理 + 渲染」装成一台按帧推进的机器。
 *
 * 分工与参考实现 dsh-pet 一致：决策（pickers）与手感（physics）都是纯模块，
 * 引擎只做「谁在什么时候播什么、画完把画布移到哪」。这样既能被单测按住，
 * 也能把同一套规则换到别的壳里（React 插件 / Vue 组件之外）。
 *
 * 不变量：
 * - 拖拽与睡眠期间随机链停摆，播完判定只认前台片段；
 * - 换片段一律从头开始（elapsed 归零），否则「同一段重播」看不出变化；
 * - 每帧只画一次，DOM 只改 canvas 的 transform，不触发重排。
 */
import { BASE, CLIPS } from './clips'
import { CATALOG } from './catalog'
import { isWorkActive, decideEndedCue, decideNextClip, pick, rollKind, workClipFor } from './pickers'
import { createMotion, type Motion, type Viewport } from './physics'
import { createRenderer, type Renderer } from './renderer'
import type { Catalog, Clip, ClipMap, Facing, Pose, WorkState } from './types'

/** 盒子高宽比（角色比画布高一点，留出头顶气泡与脚下的空间）。 */
const BOX_ASPECT = 1.26
/** 默认盒宽（px）。 */
const DEFAULT_SIZE = 148
/** 走位距离基准宽度：配置里的像素按这个宽度折算。 */
const MOVE_REF_WIDTH = 462
/** 睡觉三段。 */
const SLEEP_PHASE = { start: 'start', loop: 'loop', end: 'end' } as const

/** 桌宠运行状态（只读快照，测试与调试用）。 */
export interface PetRuntime {
  clip: string
  elapsed: number
  repeat: boolean
  facing: Facing
  dragging: boolean
  airborne: boolean
  walking: boolean
  sleeping: 'start' | 'loop' | 'end' | null
  workState: WorkState | null
}

/** 引擎构造参数。 */
export interface DeskPetOptions {
  canvas: HTMLCanvasElement
  /** 跟随位移的元素；缺省移动 canvas。外壳用它在根节点上挂气泡。 */
  root?: HTMLElement
  /** 盒宽（px）；高度按 {@link BOX_ASPECT} 推出。 */
  size?: number
  /** 片段目录。 */
  catalog?: Catalog
  /** 片段库。 */
  clips?: ClipMap
  /** 设备像素比；缺省按 window.devicePixelRatio，再缺省 2。 */
  dpr?: number
  /** 地面离视口底部的距离（px）：让宠物站在底部标签栏上方。 */
  groundInset?: number
  /** 交互动效回调：说了什么由外壳决定文案，引擎只报事件。 */
  onSay?: (text: string, durationMs: number) => void
  /** 朝向变化（外壳可以用它翻转气泡尖角方向）。 */
  onFacing?: (facing: Facing) => void
  /** 拖拽结束后的归一化位置（相对视口中心，0..1）。 */
  onPosition?: (position: { rx: number; ry: number }) => void
  /** 单击（已判定为点击）：外壳用它决定说哪句话。 */
  onTap?: () => void
  /** 双击 / 主动点开对话。 */
  onActivate?: () => void
  /** 触感反馈（支持的浏览器上震一下）。 */
  onHaptic?: () => void
}

/** 引擎对外面。 */
export interface DeskPetEngine {
  /** 开始按帧推进。 */
  start(): void
  /** 停止推进（保留状态，可再 start）。 */
  stop(): void
  /** 卸载：停帧、解绑、清空图片。 */
  destroy(): void
  /** 换形象（dataURL / 资源地址）；传 null 回到默认角色。 */
  setSprite(url: string | null): void
  /** 调整盒宽（响应式）。 */
  setSize(width: number): void
  /** 更新视口（窗口尺寸变化）。 */
  resize(): void
  setReducedMotion(on: boolean): void
  /** 工作状态联动；null = 空闲。 */
  setWorkState(state: WorkState | null): void
  /** 说一句：抽碎碎念动画并回调文案；睡着时只弹气泡不动。 */
  speak(text: string, durationMs?: number): void
  /** 点一下：睡着时叫醒，否则播一段点击回应。 */
  tap(): void
  /** 双击：交给外壳（打开对话）。 */
  activate(): void
  sleep(): void
  wake(): void
  /** 点播一段动作（菜单用）。 */
  playAction(clipId: string): boolean
  /** 手动推进（测试用）；正常由 start() 的 rAF 驱动。 */
  advance(dtMs: number): void
  /** 指针交互。 */
  beginDrag(pointerX: number, pointerY: number, now: number): void
  moveDrag(pointerX: number, pointerY: number, now: number): void
  endDrag(now: number): void
  /** 摆到角落（首次挂载用）。 */
  home(corner?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left', margin?: { x: number; y: number }): void
  readonly runtime: PetRuntime
  readonly motion: Motion
}

/** 姿态默认值（片段没写到的字段取这里）。 */
const BASE_POSE: Pose = {
  scaleX: BASE.scaleX,
  scaleY: BASE.scaleY,
  rotate: BASE.rotate,
  offsetX: BASE.offsetX,
  offsetY: BASE.offsetY,
  alpha: BASE.alpha,
  shadow: BASE.shadow,
  mirror: false,
  props: [],
}

/** 造一台引擎。 */
export function createDeskPetEngine(options: DeskPetOptions): DeskPetEngine {
  const catalog = options.catalog ?? CATALOG
  const clips = options.clips ?? CLIPS
  let size = options.size ?? DEFAULT_SIZE
  let viewport: Viewport = readViewport()
  let reduced = false
  let sprite: HTMLImageElement | null = null
  let spriteGeneration = 0
  let rafId: number | null = null
  let lastFrame = 0
  let elapsed = 0
  let current: Clip = clips['idle.breath'] ?? Object.values(clips)[0]
  let repeat = true
  let facing: Facing = 'left'
  let workState: WorkState | null = null
  let sleeping: 'start' | 'loop' | 'end' | null = null
  let frozen = false
  let gesture = { down: false, moved: false, startX: 0, startY: 0, lastTapAt: Number.NEGATIVE_INFINITY }

  let renderer: Renderer
  try {
    renderer = createRenderer(options.canvas, options.dpr ?? readDpr())
  } catch {
    // 没有 canvas 实现（jsdom 等）时退化为空渲染：动画逻辑照跑，测试只断言状态
    renderer = { resize: () => undefined, draw: () => undefined }
  }
  const motion = createMotion(viewport, { width: size, height: size * BOX_ASPECT }, {}, options.groundInset ?? 68)
  renderer.resize(size, size * BOX_ASPECT)

  function readViewport(): Viewport {
    if (typeof window === 'undefined') return { width: 390, height: 844 }
    return { width: window.innerWidth, height: window.innerHeight }
  }

  function readDpr(): number {
    if (typeof window === 'undefined') return 2
    return window.devicePixelRatio || 1
  }

  const runtime: PetRuntime = {
    get clip() {
      return current.id
    },
    get elapsed() {
      return elapsed
    },
    get repeat() {
      return repeat
    },
    get facing() {
      return facing
    },
    get dragging() {
      return motion.state.dragging
    },
    get airborne() {
      return !motion.state.grounded && !motion.state.walking
    },
    get walking() {
      return motion.state.walking
    },
    get sleeping() {
      return sleeping
    },
    get workState() {
      return workState
    },
  }

  /** 换片段：从头播；`loop` 为真时循环，为假时播完触发 ended。 */
  function play(clipId: string, loop: boolean): void {
    const clip = clips[clipId]
    if (clip === undefined) return
    current = clip
    elapsed = 0
    repeat = loop
  }

  /** 当前片段是否属于走位池。 */
  function isMoveClip(id: string): boolean {
    return catalog.moves.actions.some((action) => action.clip === id)
  }

  /** 工作状态能否接管动画（拖拽与睡眠期间不接管，醒来后再补）。 */
  function workBlocked(): boolean {
    return frozen || sleeping !== null
  }

  /** 回到工作状态循环；没有可恢复状态时返回 false。 */
  function resumeWork(): boolean {
    if (workBlocked()) return false
    if (workState === null) return false
    if (!isWorkActive(workState)) return false
    const clip = workClipFor(catalog, workState, current.id)
    if (clip === null) return false
    play(clip, true)
    return true
  }

  /** 掷骰选下一段。 */
  function rollNext(): void {
    if (workBlocked()) return
    if (isWorkActive(workState)) return
    if (motion.state.dragging || motion.state.walking) return
    if (!motion.state.grounded) return
    const kind = rollKind(Math.random(), catalog.weights)
    if (kind === 'move') {
      const started = tryWalk()
      const decision = decideNextClip({ kind, catalog, facing, current: current.id, move: started })
      if (decision.play && decision.clip !== null) play(decision.clip, false)
      return
    }
    const decision = decideNextClip({ kind, catalog, facing, current: current.id })
    if (decision.clip !== null) play(decision.clip, false)
  }

  /** 试走位：距离按实际尺寸折算，撞墙换方向再试一次。 */
  function tryWalk(): string | false {
    const action = pick(catalog.moves.actions)
    if (action === undefined) return false
    const params = { ...catalog.moves.default, ...action.params }
    const scale = size / MOVE_REF_WIDTH
    const distance = (params.minDist + Math.random() * (params.maxDist - params.minDist)) * scale
    const wanted = facing === 'left' ? -1 : 1
    if (motion.walk(distance, wanted)) {
      play(action.clip, true)
      return action.clip
    }
    if (motion.walk(distance, wanted === 1 ? -1 : 1)) {
      facing = wanted === 1 ? 'left' : 'right'
      options.onFacing?.(facing)
      play(action.clip, true)
      return action.clip
    }
    return false
  }

  /** 播完：按 cue 决定下一步。 */
  function handleEnded(): void {
    // 兜底：先转成循环。任何一条分支如果没能换片段（被冻结、被打断、无候选），
    // 下一帧都不会再撞进这里；否则会变成「每帧 ended」的忙循环。
    repeat = true
    if (sleeping === SLEEP_PHASE.start) {
      sleeping = SLEEP_PHASE.loop
      play(catalog.sleep[0].loop, true)
      return
    }
    if (sleeping === SLEEP_PHASE.end) {
      sleeping = null
      if (resumeWork()) return
      rollNext()
      return
    }
    if (sleeping === SLEEP_PHASE.loop) return
    if (frozen) return
    if (current.id === 'whisper.talk') {
      afterInteraction()
      return
    }
    const cue = decideEndedCue({ catalog, current: current.id, workState })
    switch (cue.kind) {
      case 'ignore':
        return
      case 'work-rotate':
        play(cue.clip, true)
        return
      case 'work-replay':
        play(current.id, true)
        return
      case 'event-done':
        if (resumeWork()) return
        workState = null
        rollNext()
        return
      case 'turn': {
        facing = facing === 'left' ? 'right' : 'left'
        options.onFacing?.(facing)
        rollNext()
        return
      }
      case 'interaction-done':
        afterInteraction()
        return
      default:
        rollNext()
    }
  }

  /** 互动结束：有进行中的任务就回到档位循环，否则继续掷骰。 */
  function afterInteraction(): void {
    if (resumeWork()) return
    if (!motion.state.grounded) return
    rollNext()
  }

  /** 一帧：推进物理与片段时间，再画。 */
  function frame(dtMs: number): void {
    motion.step(dtMs)
    const clipDuration = current.duration
    if (clipDuration <= 0) {
      handleEnded()
      return
    }
    elapsed += dtMs
    if (elapsed >= clipDuration) {
      if (repeat) {
        elapsed %= clipDuration
      } else {
        elapsed = clipDuration
        handleEnded()
        // ended 可能已经换了片段；新片段从 0 开始，这里不再补帧
      }
    }
    // 走位片段：脚停了就回待机，由待机播完再继续掷骰
    if (isMoveClip(current.id) && !motion.state.walking && !motion.state.dragging) {
      play(catalog.idle[0] ?? current.id, false)
    }
    draw()
  }

  /** 采样姿态并渲染。 */
  function draw(): void {
    const t = current.duration <= 0 ? 0 : Math.min(1, elapsed / current.duration)
    const sample = reduced ? {} : current.sample(t)
    const squash = motion.squashFactor()
    const pose: Pose = {
      ...BASE_POSE,
      ...sample,
      props: sample.props ?? [],
      mirror: facing === 'right',
      scaleY: (sample.scaleY ?? BASE_POSE.scaleY) * squash,
      scaleX: (sample.scaleX ?? BASE_POSE.scaleX) * (squash === 1 ? 1 : 2 - squash),
    }
    renderer.draw(sprite, pose)
    // 位移只改 transform：不触发重排，也不参与 Vue 的响应式；外壳给了根节点就移动它，气泡跟着走
    const mover = options.root ?? options.canvas
    mover.style.transform =
      `translate3d(${Math.round(motion.state.x)}px, ${Math.round(motion.state.y)}px, 0)`
  }

  function loop(now: number): void {
    const dt = lastFrame === 0 ? 16 : Math.min(64, now - lastFrame)
    lastFrame = now
    frame(dt)
    rafId = requestAnimationFrame(loop)
  }

  return {
    runtime,
    motion,
    start(): void {
      if (rafId !== null) return
      // 没有 rAF 的环境（jsdom / 老 WebView）不自动起帧，调用方用 advance() 手动推进
      if (typeof requestAnimationFrame !== 'function') return
      lastFrame = 0
      rafId = requestAnimationFrame(loop)
    },
    stop(): void {
      if (rafId !== null && typeof cancelAnimationFrame === 'function') cancelAnimationFrame(rafId)
      rafId = null
    },
    destroy(): void {
      this.stop()
      sprite = null
      spriteGeneration += 1
    },
    setSprite(url: string | null): void {
      if (url === null) {
        sprite = null
        spriteGeneration += 1
        draw()
        return
      }
      spriteGeneration += 1
      const generation = spriteGeneration
      const image = new Image()
      image.decoding = 'async'
      image.onload = () => {
        if (generation !== spriteGeneration) return
        sprite = image
        draw()
      }
      image.src = url
    },
    setSize(width: number): void {
      size = width
      motion.setSize({ width: size, height: size * BOX_ASPECT })
      renderer.resize(size, size * BOX_ASPECT)
      draw()
    },
    resize(): void {
      viewport = readViewport()
      motion.setViewport(viewport)
      draw()
    },
    setReducedMotion(on: boolean): void {
      reduced = on
      draw()
    },
    setWorkState(state: WorkState | null): void {
      workState = state
      if (workBlocked()) return
      if (state === null) {
        if (!motion.state.dragging) rollNext()
        return
      }
      const clip = workClipFor(catalog, state, current.id)
      if (clip === null) return
      play(clip, isWorkActive(state))
    },
    speak(text: string, durationMs = 4200): void {
      options.onSay?.(text, durationMs)
      if (sleeping === SLEEP_PHASE.loop || sleeping === SLEEP_PHASE.start) return
      if (motion.state.dragging) return
      play('whisper.talk', false)
    },
    tap(): void {
      options.onHaptic?.()
      options.onTap?.()
      if (sleeping !== null) {
        this.wake()
        return
      }
      if (motion.state.dragging) return
      if (!motion.state.grounded) return
      // 工作中点一下同样给回应——播完由 decideEndedCue 的 interaction-done
      // 把工作动画接回来（参考实现 dsh-pet 也是这个语义：互动可插播，状态不丢）。
      const clip = pick(catalog.clicks, current.id)
      play(clip, false)
    },
    activate(): void {
      options.onActivate?.()
    },
    sleep(): void {
      if (sleeping !== null) return
      sleeping = SLEEP_PHASE.start
      motion.state.vx = 0
      motion.state.vy = 0
      play(catalog.sleep[0].start, false)
    },
    wake(): void {
      if (sleeping === null) return
      // 入睡过渡里醒来：直接取消，不播「起来」——要不然会出现躺着起身的怪动作
      if (sleeping === SLEEP_PHASE.start) {
        sleeping = null
        play(catalog.idle[0] ?? current.id, false)
        return
      }
      sleeping = SLEEP_PHASE.end
      play(catalog.sleep[0].end, false)
    },
    playAction(clipId: string): boolean {
      if (clips[clipId] === undefined) return false
      if (sleeping !== null) return false
      play(clipId, false)
      return true
    },
    advance(dtMs: number): void {
      const steps = Math.max(1, Math.ceil(dtMs / 16))
      const step = dtMs / steps
      for (let i = 0; i < steps; i += 1) frame(step)
    },
    beginDrag(pointerX: number, pointerY: number, now: number): void {
      gesture = { down: true, moved: false, startX: pointerX, startY: pointerY, lastTapAt: gesture.lastTapAt }
      frozen = true
      motion.beginDrag(pointerX, pointerY, now)
      play(catalog.drag[0] ?? current.id, true)
    },
    moveDrag(pointerX: number, pointerY: number, now: number): void {
      if (!gesture.down) return
      if (!gesture.moved) {
        const dx = pointerX - gesture.startX
        const dy = pointerY - gesture.startY
        if (Math.hypot(dx, dy) > 5) gesture.moved = true
      }
      motion.moveDrag(pointerX, pointerY, now)
    },
    endDrag(now: number): void {
      if (!gesture.down) return
      const wasGesture = gesture.moved
      gesture.down = false
      frozen = false
      motion.endDrag(now)
      if (!wasGesture) {
        // 没拖动 = 点一下；两次快速点按 = 双击。
        // 注意「第一次点按」必须能和双击区分开：lastTapAt 初值是 -Infinity，
        // 不能拿 0 当哨兵——挂载后 280ms 内的第一次点击会被误判成双击。
        const isDouble = now - gesture.lastTapAt < 280
        gesture.lastTapAt = isDouble ? Number.NEGATIVE_INFINITY : now
        if (isDouble) this.activate()
        else this.tap()
        return
      }
      const rx = (motion.state.x + size / 2) / viewport.width
      const ry = (motion.state.y + size / 2) / viewport.height
      options.onPosition?.({ rx, ry })
      if (resumeWork()) return
      play(catalog.idle[0] ?? current.id, false)
    },
    home(corner = 'bottom-right', margin = { x: 18, y: 96 }): void {
      motion.home(corner, margin)
      draw()
    },
  }
}
