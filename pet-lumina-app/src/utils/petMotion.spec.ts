import { describe, expect, it } from 'vitest'
import {
  BLINK_MAX_MS,
  BLINK_MIN_MS,
  DRAG_THRESHOLD,
  GAZE_LIMIT,
  clamp,
  movedEnough,
  nextDelay,
  normalizeGaze,
  smooth,
} from './petMotion'

describe('petMotion', () => {
  it('clamp 夹住区间，NaN 归零', () => {
    expect(clamp(5, 0, 3)).toBe(3)
    expect(clamp(-1, 0, 3)).toBe(0)
    expect(clamp(Number.NaN, 0, 3)).toBe(0)
    expect(clamp(2, 0, 3)).toBe(2)
  })

  it('normalizeGaze：指针在右下 → 正偏移，且不超过上限', () => {
    const rect = { left: 100, top: 100, width: 100, height: 100 }
    const g = normalizeGaze(rect, 1000, 1000, GAZE_LIMIT)
    expect(g.x).toBe(GAZE_LIMIT)
    expect(g.y).toBe(GAZE_LIMIT)
  })

  it('normalizeGaze：正中心是原点，左上为负', () => {
    const rect = { left: 0, top: 0, width: 100, height: 100 }
    expect(normalizeGaze(rect, 50, 50)).toEqual({ x: 0, y: 0 })
    const g = normalizeGaze(rect, 0, 0, GAZE_LIMIT)
    expect(g.x).toBe(-GAZE_LIMIT)
    expect(g.y).toBe(-GAZE_LIMIT)
  })

  it('normalizeGaze：宽高为 0（未挂载/隐藏）时返回原点，不产生 Infinity', () => {
    expect(normalizeGaze({ left: 0, top: 0, width: 0, height: 0 }, 10, 10)).toEqual({ x: 0, y: 0 })
  })

  it('smooth 指数逼近且 k 被夹在 0..1', () => {
    expect(smooth(0, 10, 0.5)).toBe(5)
    expect(smooth(0, 10, 0)).toBe(0)
    expect(smooth(0, 10, 2)).toBe(10)
    expect(smooth(0, 10, 0.18)).toBeCloseTo(1.8, 2)
  })

  it('nextDelay 落在区间内，并按 random 注入可预测', () => {
    expect(nextDelay(BLINK_MIN_MS, BLINK_MAX_MS, () => 0)).toBe(BLINK_MIN_MS)
    expect(nextDelay(BLINK_MIN_MS, BLINK_MAX_MS, () => 1)).toBe(BLINK_MAX_MS)
    const mid = nextDelay(100, 200, () => 0.5)
    expect(mid).toBeGreaterThanOrEqual(100)
    expect(mid).toBeLessThanOrEqual(200)
  })

  it('movedEnough 以拖动阈值判定（点击 vs 拖拽）', () => {
    expect(movedEnough(1, 1)).toBe(false)
    expect(movedEnough(DRAG_THRESHOLD, 0)).toBe(true)
    expect(movedEnough(0, DRAG_THRESHOLD - 0.5)).toBe(false)
  })
})
