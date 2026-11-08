/**
 * 缓动与轨道采样：把「关键帧 → 时间 → 数值」这段算术从片段定义里抽出来。
 *
 * 全部是纯函数：同一个 t 永远得到同一个值，片段才能被单测与回放。
 */

/** 缓动函数：定义域 [0,1]，值域 [0,1]。 */
export type Easing = (t: number) => number

export const linear: Easing = (t) => t

export const easeOut: Easing = (t) => 1 - (1 - t) ** 3

export const easeIn: Easing = (t) => t ** 3

export const easeInOut: Easing = (t) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2)

/** 回弹：越过终点再回来，用于落地、惊喜这类「有弹性」的动作。 */
export const easeBackOut: Easing = (t) => 1 + 2.2 * (t - 1) ** 3 + 1.2 * (t - 1) ** 2

/** 把 t 从 [0,1] 映射到 [from,to]。 */
export function tween(t: number, from: number, to: number, ease: Easing = easeInOut): number {
  return from + (to - from) * ease(clamp01(t))
}

/** 正弦波：周期 = 1，t=0 时值为 0（用于呼吸、摇摆）。 */
export function wave(t: number, amplitude = 1, phase = 0): number {
  return Math.sin((t + phase) * Math.PI * 2) * amplitude
}

/** 正半波：t ∈ [0,1] 时 0→1→0，用于「跳一下」。 */
export function pulse(t: number): number {
  return Math.sin(clamp01(t) * Math.PI)
}

/** 衰减振荡：t=0 时为 1，之后按 decay 衰减（抖动、落地回弹）。 */
export function bounce(t: number, decay = 6, frequency = 3): number {
  return Math.exp(-decay * clamp01(t)) * Math.cos(clamp01(t) * Math.PI * 2 * frequency)
}

export function clamp01(t: number): number {
  if (!Number.isFinite(t)) return 0
  return t < 0 ? 0 : t > 1 ? 1 : t
}

export function clamp(value: number, min: number, max: number): number {
  return value < min ? min : value > max ? max : value
}

/** 一个关键帧：到达 at（0..1）时的值。 */
export interface Keyframe {
  at: number
  value: number
  ease?: Easing
}

/**
 * 关键帧轨道采样。
 *
 * - 首帧之前 / 末帧之后都保持端点值（不外推）；
 * - 每段的缓动取**终点帧**上的 `ease`，这样「到这个点怎么过去」写在落点上，
 *   片段定义读起来就是一句句「0.2 到 -4 度」「0.6 回到 0 度」。
 *
 * @param keys - 至少一个关键帧；按 at 升序（调用方保证，片段都是人写的）
 * @param t - 归一化时间
 */
export function track(keys: readonly Keyframe[], t: number): number {
  if (keys.length === 0) return 0
  const time = clamp01(t)
  if (time <= keys[0].at) return keys[0].value
  for (let i = 1; i < keys.length; i += 1) {
    const prev = keys[i - 1]
    const next = keys[i]
    if (time > next.at) continue
    const span = next.at - prev.at
    const local = span <= 0 ? 1 : (time - prev.at) / span
    return tween(local, prev.value, next.value, next.ease ?? easeInOut)
  }
  return keys[keys.length - 1].value
}
