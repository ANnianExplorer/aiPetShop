/**
 * 桌宠位移：拖拽跟手、甩出抛掷、落地回弹与走位。
 *
 * 手感参数照着手感参考实现 dsh-pet 的物理档位定：重力 1400、碰边恢复 0.78、
 * 落地摩擦 2.5、甩速软上限 3600、低于 500 不抛。差别是这里没有引力和多宠物碰撞，
 * 只保留「抓起来—甩出去—撞墙反弹—落地 Q 弹」这一段最小闭环。
 *
 * 纯计算：视口与尺寸由调用方传入，不读 window，方便单测。
 */
import { clamp } from './easing'
import type { PhysicsParams } from './types'

/** 视口尺寸。 */
export interface Viewport {
  width: number
  height: number
}

/** 宠物盒尺寸。 */
export interface PetSize {
  width: number
  height: number
}

/** 默认物理参数。 */
export const DEFAULT_PHYSICS: PhysicsParams = {
  gravity: 1400,
  restitution: 0.78,
  groundFriction: 2.5,
  maxThrowSpeed: 3600,
  deadZoneSpeed: 500,
  refWidth: 462,
}

/** 拖拽轨迹保留窗口（ms）。 */
const TRAIL_KEEP_MS = 200
/** 初速估算窗口（ms）。 */
const RELEASE_WINDOW_MS = 150
/** 松手前停顿超过它即温柔放下（ms）。 */
const RELEASE_STALE_MS = 150
/** 估算速度需要的最短时间跨度（ms）。 */
const MIN_SPAN_MS = 20
/** 单段采样的最小 dt（ms）：高回报率指针事件会把抖动放大成假峰值。 */
const SEG_MIN_DT_MS = 8
/** 单步最大位移（px）：一帧位移超过它就拆步，避免穿墙。 */
const SUBSTEP_PX = 8
/** 拆步上限。 */
const SUBSTEP_MAX = 32
/** 落地挤压时长（ms）。 */
const SQUASH_MS = 220
/** 轻微落地的冲击速度（px/s）。 */
const SQUASH_SOFT_SPEED = 300
/** 重砸的冲击速度（px/s）。 */
const SQUASH_HARD_SPEED = 1500
/** 最大压扁比例。 */
const SQUASH_MAX = 0.45
/** 贴地判定的法向速度阈值（px/s）。 */
const REST_NORMAL = 40
/** 贴地判定的切向速度阈值（px/s）。 */
const REST_TANGENT = 15
/** 越界摆放时至少留在视口内的像素。 */
const MIN_REACHABLE_PX = 24

/** 一次指针采样。 */
interface TrailPoint {
  x: number
  y: number
  t: number
}

/** 走位任务。 */
interface WalkTask {
  targetX: number
  speed: number
}

/** 位移状态（只读消费）。 */
export interface MotionState {
  /** 宠物盒左上角（px）。 */
  x: number
  y: number
  vx: number
  vy: number
  dragging: boolean
  grounded: boolean
  walking: boolean
  /** 朝向：-1 向左、1 向右（走位与镜像都由它决定）。 */
  direction: -1 | 1
}

/** 位移控制器。 */
export interface Motion {
  readonly state: MotionState
  setViewport(viewport: Viewport): void
  setSize(size: PetSize): void
  /** 直接摆放（不产生速度）。 */
  place(x: number, y: number): void
  /** 摆到某个角落（边距按像素）。 */
  home(corner: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left', margin: { x: number; y: number }): void
  beginDrag(pointerX: number, pointerY: number, now: number): void
  moveDrag(pointerX: number, pointerY: number, now: number): void
  /** 松手：按轨迹估速，够快就抛，否则原地放下。 */
  endDrag(now: number): void
  /** 甩出（测试与外部指令用）。 */
  throwTo(vx: number, vy: number): void
  /** 走位：向 `direction` 方向移动 `distance` 像素；返回实际开始与否。 */
  walk(distance: number, direction: -1 | 1): boolean
  /** 推进一帧；dt 单位 ms。 */
  step(dtMs: number): void
  /** 落地压扁系数：1 = 正常，< 1 = 被压扁。 */
  squashFactor(): number
  /** 落地区域的中心 x（渲染影子用）。 */
  readonly groundY: number
}

/**
 * 造一个位移控制器。
 *
 * @param viewport - 视口尺寸（窗口变化时用 setViewport 更新）
 * @param size - 宠物盒尺寸
 * @param physics - 覆盖默认物理参数
 * @param groundInset - 地面离视口底部的距离（px）：手机底部有标签栏时，宠物要站在它上面
 */
export function createMotion(
  viewport: Viewport,
  size: PetSize,
  physics: Partial<PhysicsParams> = {},
  groundInset = 0,
): Motion {
  const params: PhysicsParams = { ...DEFAULT_PHYSICS, ...physics }
  let vp = { ...viewport }
  let box = { ...size }
  let inset = Math.max(0, groundInset)
  let squashLeft = 0
  let squashAmount = 0
  let trail: TrailPoint[] = []
  let grab = { dx: 0, dy: 0 }
  let walkTask: WalkTask | null = null

  const state: MotionState = {
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    dragging: false,
    grounded: true,
    walking: false,
    direction: -1,
  }

  /** 夹到「还能点到」的范围：单轴区间反向（视口比宠物还小）时改为居中。 */
  function clampAxis(value: number, max: number, span: number): number {
    const lo = MIN_REACHABLE_PX - span
    const hi = max - MIN_REACHABLE_PX
    if (lo > hi) return (max - span) / 2
    return clamp(value, lo, hi)
  }

  function clampPosition(): void {
    state.x = clampAxis(state.x, vp.width, box.width)
    state.y = clampAxis(state.y, vp.height, box.height)
  }

  function stop(): void {
    state.vx = 0
    state.vy = 0
    state.walking = false
    walkTask = null
  }

  /** 落地冲击 → 挤压幅度。 */
  function land(impactSpeed: number): void {
    const amount = clamp(
      ((impactSpeed - SQUASH_SOFT_SPEED) / (SQUASH_HARD_SPEED - SQUASH_SOFT_SPEED)) * SQUASH_MAX,
      0.06,
      SQUASH_MAX,
    )
    squashAmount = amount
    squashLeft = SQUASH_MS
  }

  function integrate(dt: number): void {
    // 走位优先：走位时不叠加重力，脚一直贴地
    if (walkTask !== null) {
      const remaining = walkTask.targetX - state.x
      const stepPx = walkTask.speed * dt
      if (Math.abs(remaining) <= stepPx) {
        state.x = walkTask.targetX
        state.walking = false
        walkTask = null
      } else {
        state.x += Math.sign(remaining) * stepPx
      }
      state.y = clampPositionY(state.y)
      return
    }

    if (state.dragging) return

    const moving = Math.abs(state.vx) > 0.5 || Math.abs(state.vy) > 0.5 || !state.grounded
    if (!moving) return

    const steps = Math.min(
      SUBSTEP_MAX,
      Math.max(1, Math.ceil((Math.max(Math.abs(state.vx), Math.abs(state.vy)) * dt) / SUBSTEP_PX)),
    )
    const sub = dt / steps
    for (let i = 0; i < steps; i += 1) {
      state.vy += params.gravity * sub
      state.x += state.vx * sub
      state.y += state.vy * sub

      const maxX = vp.width - box.width
      const maxY = vp.height - box.height - inset

      if (state.x < 0) {
        state.x = 0
        if (state.vx < 0) {
          state.vx = -state.vx * params.restitution
          state.vy *= Math.exp(-params.groundFriction * sub)
        }
      } else if (state.x > maxX) {
        state.x = maxX
        if (state.vx > 0) {
          state.vx = -state.vx * params.restitution
          state.vy *= Math.exp(-params.groundFriction * sub)
        }
      }

      if (state.y < 0) {
        state.y = 0
        if (state.vy < 0) state.vy = -state.vy * params.restitution
      } else if (state.y > maxY) {
        const impact = state.vy
        state.y = maxY
        if (impact > SQUASH_SOFT_SPEED) land(impact)
        state.vy = impact > REST_NORMAL ? -impact * params.restitution : 0
        state.vx *= Math.exp(-params.groundFriction * sub)
      }

      // 贴地判定：法向已经压住、切向也慢下来，就彻底停下（否则每帧微弹会抖）
      if (
        Math.abs(state.y - maxY) < 0.5 &&
        Math.abs(state.vy) < REST_NORMAL &&
        Math.abs(state.vx) < REST_TANGENT
      ) {
        state.y = maxY
        state.vy = 0
        state.vx = 0
        state.grounded = true
        break
      }
      state.grounded = Math.abs(state.y - maxY) < 0.5;
      if (!state.grounded) state.vx *= Math.exp(-0.4 * sub)
    }
    clampPosition()
  }

  function clampPositionY(value: number): number {
    return clampAxis(value, vp.height - inset, box.height)
  }

  /** 松手估速：只取最近窗口内的采样，快甩用峰值补偿位移集中的低估。 */
  function releaseVelocity(now: number): { vx: number; vy: number } {
    const recent = trail.filter((point) => now - point.t <= RELEASE_WINDOW_MS)
    if (recent.length < 2) return { vx: 0, vy: 0 }
    const first = recent[0]
    const last = recent[recent.length - 1]
    const span = last.t - first.t
    if (span < MIN_SPAN_MS) return { vx: 0, vy: 0 }
    // 用相邻采样求分段速度，过滤掉低于 SEG_MIN_DT_MS 的抖动段
    let sumVx = 0
    let sumVy = 0
    let count = 0
    let peak = 0
    for (let i = 1; i < recent.length; i += 1) {
      const dt = recent[i].t - recent[i - 1].t
      if (dt < SEG_MIN_DT_MS) continue
      const vx = (recent[i].x - recent[i - 1].x) / (dt / 1000)
      const vy = (recent[i].y - recent[i - 1].y) / (dt / 1000)
      sumVx += vx
      sumVy += vy
      peak = Math.max(peak, Math.hypot(vx, vy))
      count += 1
    }
    if (count === 0) return { vx: 0, vy: 0 }
    let vx = sumVx / count
    let vy = sumVy / count
    const mean = Math.hypot(vx, vy)
    const blended = mean * 0.5 + peak * 0.5
    if (mean > 0) {
      const scale = blended / mean
      vx *= scale
      vy *= scale
    }
    return { vx, vy }
  }

  return {
    state,
    get groundY(): number {
      return vp.height
    },
    setViewport(next: Viewport): void {
      vp = { ...next }
      clampPosition()
    },
    setSize(next: PetSize): void {
      box = { ...next }
      clampPosition()
    },
    place(x: number, y: number): void {
      state.x = x
      state.y = y
      stop()
      state.grounded = true
      clampPosition()
    },
    home(corner, margin): void {
      const right = vp.width - box.width - margin.x
      const left = margin.x
      const top = margin.y
      const bottom = vp.height - box.height - inset - margin.y
      const x = corner.endsWith('right') ? right : left
      const y = corner.startsWith('bottom') ? bottom : top
      this.place(x, y)
    },
    beginDrag(pointerX: number, pointerY: number, now: number): void {
      state.dragging = true
      grab = { dx: state.x - pointerX, dy: state.y - pointerY }
      walkTask = null
      state.walking = false
      trail = [{ x: pointerX, y: pointerY, t: now }]
      state.vx = 0
      state.vy = 0
    },
    moveDrag(pointerX: number, pointerY: number, now: number): void {
      if (!state.dragging) return
      state.x = pointerX + grab.dx
      state.y = pointerY + grab.dy
      clampPosition()
      trail.push({ x: pointerX, y: pointerY, t: now })
      trail = trail.filter((point) => now - point.t <= TRAIL_KEEP_MS)
    },
    endDrag(now: number): void {
      if (!state.dragging) return
      state.dragging = false
      const last = trail[trail.length - 1]
      const stale = last === undefined || now - last.t > RELEASE_STALE_MS
      const velocity = stale ? { vx: 0, vy: 0 } : releaseVelocity(now)
      trail = []
      const speed = Math.hypot(velocity.vx, velocity.vy)
      if (speed < params.deadZoneSpeed) {
        state.vx = 0
        state.vy = 0
        state.grounded = false
        return
      }
      const capped = params.maxThrowSpeed * (1 - Math.exp(-speed / params.maxThrowSpeed))
      const scale = capped / speed
      state.vx = velocity.vx * scale
      state.vy = velocity.vy * scale
      state.grounded = false
      if (Math.abs(state.vx) > 40) {
        state.direction = state.vx > 0 ? 1 : -1
      }
    },
    throwTo(vx: number, vy: number): void {
      state.vx = vx
      state.vy = vy
      state.grounded = false
      state.walking = false
      walkTask = null
      if (Math.abs(vx) > 40) state.direction = vx > 0 ? 1 : -1
    },
    walk(distance: number, direction: -1 | 1): boolean {
      if (state.dragging) return false
      const target = state.x + distance * direction
      const clamped = clampAxis(target, vp.width, box.width)
      if (Math.abs(clamped - state.x) < 4) return false
      state.direction = direction
      state.vx = 0
      state.vy = 0
      state.grounded = true
      state.walking = true
      state.y = vp.height - box.height - inset
      walkTask = { targetX: clamped, speed: Math.max(60, distance * 0.35) }
      return true
    },
    step(dtMs: number): void {
      const dt = Math.min(dtMs, 50) / 1000
      integrate(dt)
      if (squashLeft > 0) {
        squashLeft = Math.max(0, squashLeft - dtMs)
      }
    },
    squashFactor(): number {
      if (squashLeft <= 0) return 1
      const progress = 1 - squashLeft / SQUASH_MS
      // 先猛地压扁、再用缓动弹回
      const amount = squashAmount * (1 - progress) ** 1.6
      return 1 - amount
    },
  }
}
