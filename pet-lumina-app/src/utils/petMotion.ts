/**
 * 桌宠运动相关的纯函数。
 *
 * 单独抽出来的原因：视线跟随/平滑/随机间隔这些逻辑最容易出错，但它们和 DOM 无关，
 * 放在组件里就没法单测；抽成纯函数后可以钉死边界（越界、除零、NaN）。
 */

export interface GazeOffset {
  x: number
  y: number
}

export const GAZE_LIMIT = 3
export const BLINK_CLOSED_MS = 110
export const BLINK_MIN_MS = 2600
export const BLINK_MAX_MS = 6200
export const EAR_TWITCH_MIN_MS = 5000
export const EAR_TWITCH_MAX_MS = 9000

export function clamp(value: number, min: number, max: number): number {
  if (Number.isNaN(value)) return 0
  if (value < min) return min
  if (value > max) return max
  return value
}

/**
 * 把屏幕坐标换算成以元素中心为原点的归一化方向（-1..1），再乘以最大位移。
 * 元素宽高为 0（未挂载/隐藏）时返回原点，避免除零得到 Infinity。
 */
export function normalizeGaze(
  rect: { left: number; top: number; width: number; height: number },
  pointerX: number,
  pointerY: number,
  limit = GAZE_LIMIT,
): GazeOffset {
  if (rect.width <= 0 || rect.height <= 0) return { x: 0, y: 0 }
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  const nx = clamp((pointerX - cx) / (rect.width / 2), -1, 1)
  const ny = clamp((pointerY - cy) / (rect.height / 2), -1, 1)
  return { x: round2(nx * limit), y: round2(ny * limit) }
}

/** 指数平滑：k 越大越"跟手"，越小越"软"。k 会被夹到 0..1。 */
export function smooth(current: number, target: number, k: number): number {
  const ratio = clamp(k, 0, 1)
  const next = current + (target - current) * ratio
  return round2(next)
}

/** 随机间隔（毫秒），random 可注入以便测试。 */
export function nextDelay(min: number, max: number, random: () => number = Math.random): number {
  if (!Number.isFinite(min) || !Number.isFinite(max)) return min
  const lo = Math.min(min, max)
  const hi = Math.max(min, max)
  return Math.round(lo + (hi - lo) * clamp(random(), 0, 1))
}

/** 拖动阈值：超过这个距离才算拖动，否则算点击。 */
export const DRAG_THRESHOLD = 6

export function movedEnough(dx: number, dy: number, threshold = DRAG_THRESHOLD): boolean {
  return Math.hypot(dx, dy) >= threshold
}

function round2(value: number): number {
  return Math.round(value * 100) / 100
}
