import { describe, expect, it } from 'vitest'
import { CLIPS } from './clips'
import { CATALOG } from './catalog'
import type { Sample } from './types'

/** 所有被目录引用到的片段名。 */
function referencedClips(): string[] {
  const ids = new Set<string>()
  for (const clip of CATALOG.idle) ids.add(clip)
  for (const clip of CATALOG.turn) ids.add(clip)
  for (const clip of CATALOG.drag) ids.add(clip)
  for (const clip of CATALOG.clicks) ids.add(clip)
  for (const action of CATALOG.moves.actions) ids.add(action.clip)
  for (const category of CATALOG.categories) for (const clip of category.actions) ids.add(clip)
  for (const slot of CATALOG.events.workStatus) for (const clip of slot) ids.add(clip)
  for (const set of CATALOG.sleep) {
    ids.add(set.start)
    ids.add(set.loop)
    ids.add(set.end)
  }
  return [...ids]
}

function numbers(sample: Sample): number[] {
  const { props: _props, ...rest } = sample
  return Object.entries(rest)
    .filter(([, value]) => typeof value === 'number')
    .map(([, value]) => value as number)
}

describe('片段目录', () => {
  it('目录里引用的每一段都真的存在', () => {
    const missing = referencedClips().filter((id) => CLIPS[id] === undefined)
    expect(missing).toEqual([])
  })

  it('片段 id 与键名一致、时长与循环标记合法', () => {
    for (const [key, clip] of Object.entries(CLIPS)) {
      expect(clip.id).toBe(key)
      expect(clip.duration).toBeGreaterThan(0)
      expect(typeof clip.loop).toBe('boolean')
    }
  })

  it('随机链权重合计 100，且每档都有可播动作', () => {
    const categoryTotal = CATALOG.categories.reduce((sum, category) => sum + category.weight, 0)
    const weightTotal =
      CATALOG.weights.idle + CATALOG.weights.turn + CATALOG.weights.move + categoryTotal
    expect(weightTotal).toBe(100)
    for (const category of CATALOG.categories) {
      expect(category.actions.length).toBeGreaterThan(0)
    }
  })

  it('工作状态六个档位都有片段，且顺序就是索引', () => {
    expect(CATALOG.events.workStatus).toHaveLength(6)
    expect(CATALOG.events.workStatus[0]).toEqual(['work.thinking'])
    expect(CATALOG.events.workStatus[5]).toEqual(['work.error'])
  })

  it('每段在任何时刻采样都给得出有限数值，姿态不越界', () => {
    for (const clip of Object.values(CLIPS)) {
      for (const t of [0, 0.25, 0.5, 0.75, 0.999]) {
        const sample = clip.sample(t)
        for (const value of numbers(sample)) {
          expect(Number.isFinite(value)).toBe(true)
        }
        if (sample.scaleX !== undefined) expect(sample.scaleX).toBeGreaterThan(0.5)
        if (sample.scaleY !== undefined) expect(sample.scaleY).toBeGreaterThan(0.5)
        if (sample.alpha !== undefined) {
          expect(sample.alpha).toBeGreaterThanOrEqual(0)
          expect(sample.alpha).toBeLessThanOrEqual(1)
        }
        if (sample.shadow !== undefined) {
          expect(sample.shadow).toBeGreaterThan(0)
          expect(sample.shadow).toBeLessThanOrEqual(1)
        }
        for (const prop of sample.props ?? []) {
          expect(prop.x).toBeGreaterThanOrEqual(-0.2)
          expect(prop.x).toBeLessThanOrEqual(1.2)
          expect(prop.y).toBeGreaterThanOrEqual(-0.2)
          expect(prop.y).toBeLessThanOrEqual(1.2)
        }
      }
    }
  })

  it('睡觉三段的角色姿势一致（躺下的角度在 start / loop 之间不跳）', () => {
    const startEnd = CLIPS['sleep.start'].sample(1)
    const loop = CLIPS['sleep.loop'].sample(0)
    expect(Math.abs((startEnd.rotate ?? 0) - (loop.rotate ?? 0))).toBeLessThan(0.001)
  })
})
