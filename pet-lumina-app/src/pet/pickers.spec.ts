import { describe, expect, it } from 'vitest'
import { CATALOG } from './catalog'
import {
  decideEndedCue,
  decideNextClip,
  isWorkActive,
  isWorkClip,
  pickWeightedCategory,
  rollKind,
  workClipFor,
} from './pickers'

const weights = { idle: 10, turn: 5, move: 5 }

describe('权重掷骰', () => {
  it('四档边界按 /100 切分', () => {
    expect(rollKind(0, weights)).toBe('idle')
    expect(rollKind(0.0999, weights)).toBe('idle')
    expect(rollKind(0.1, weights)).toBe('turn')
    expect(rollKind(0.1499, weights)).toBe('turn')
    expect(rollKind(0.15, weights)).toBe('move')
    expect(rollKind(0.1999, weights)).toBe('move')
    expect(rollKind(0.2, weights)).toBe('action')
    expect(rollKind(0.9999, weights)).toBe('action')
  })

  it('被钉住（fixed）时不再转向也不走位，份额落进动作池', () => {
    expect(rollKind(0.12, weights, { fixed: true })).toBe('action')
    expect(rollKind(0.18, weights, { fixed: true })).toBe('action')
    // 钉住不影响 idle 档
    expect(rollKind(0.05, weights, { fixed: true })).toBe('idle')
  })
})

describe('分类选择', () => {
  it('朝右时排除 noMirror 分类', () => {
    const categories = [
      { id: 'text', weight: 50, noMirror: true, actions: ['a'] },
      { id: 'move', weight: 50, actions: ['b'] },
    ]
    const picked = new Set<string>()
    for (let i = 0; i < 50; i += 1) {
      const category = pickWeightedCategory(categories, 'right')
      if (category) picked.add(category.id)
    }
    expect([...picked]).toEqual(['move'])
    expect(pickWeightedCategory(categories, 'left')?.id).toBeDefined()
  })

  it('全部分类都不可用时退回 null（上层回待机）', () => {
    expect(pickWeightedCategory([], 'left')).toBeNull()
    expect(pickWeightedCategory([{ id: 'x', weight: 1, actions: [] }], 'left')).toBeNull()
  })
})

describe('下一段决策', () => {
  it('走位已接管时不再切片段，避免原地抽搐', () => {
    const decision = decideNextClip({
      kind: 'move',
      catalog: CATALOG,
      facing: 'left',
      current: 'idle.breath',
      move: 'move.walk',
    })
    expect(decision).toEqual({ kind: 'move', clip: null, play: false })
  })

  it('走不动时退回动作池，且不会返回当前片段', () => {
    for (let i = 0; i < 20; i += 1) {
      const decision = decideNextClip({
        kind: 'move',
        catalog: CATALOG,
        facing: 'left',
        current: 'idle.breath',
        move: false,
      })
      expect(decision.play).toBe(true)
      expect(decision.clip).not.toBeNull()
      expect(decision.clip).not.toBe('idle.breath')
    }
  })

  it('idle / turn 决策只会给出各自池里的片段', () => {
    expect(CATALOG.idle).toContain(decideNextClip({ kind: 'idle', catalog: CATALOG, facing: 'left', current: 'x' }).clip)
    expect(CATALOG.turn).toContain(decideNextClip({ kind: 'turn', catalog: CATALOG, facing: 'left', current: 'x' }).clip)
  })
})

describe('播完判定', () => {
  it('工作动画且仍在进行：换一段或原地重播，绝不丢状态', () => {
    const cue = decideEndedCue({ catalog: CATALOG, current: 'work.working', workState: 'working' })
    expect(['work-replay', 'work-rotate']).toContain(cue.kind)
  })

  it('success / error 是终态：播完回随机链', () => {
    expect(decideEndedCue({ catalog: CATALOG, current: 'work.success', workState: 'success' })).toEqual({
      kind: 'event-done',
    })
    expect(decideEndedCue({ catalog: CATALOG, current: 'work.error', workState: 'error' })).toEqual({
      kind: 'event-done',
    })
  })

  it('转向段播完要求翻转朝向，互动段播完算一次互动结束', () => {
    expect(decideEndedCue({ catalog: CATALOG, current: CATALOG.turn[0], workState: null }).kind).toBe('turn')
    expect(decideEndedCue({ catalog: CATALOG, current: CATALOG.clicks[0], workState: null }).kind).toBe(
      'interaction-done',
    )
    expect(decideEndedCue({ catalog: CATALOG, current: 'act.eat', workState: null }).kind).toBe('random')
  })

  it('工作状态以 success / error 为终态判定', () => {
    expect(isWorkActive('thinking')).toBe(true)
    expect(isWorkActive('waiting')).toBe(true)
    expect(isWorkActive('success')).toBe(false)
    expect(isWorkActive('error')).toBe(false)
    expect(isWorkActive(null)).toBe(false)
  })

  it('工作档位到片段的映射与索引一致', () => {
    for (const state of ['thinking', 'working', 'result', 'waiting', 'success', 'error'] as const) {
      const clip = workClipFor(CATALOG, state)
      expect(clip).not.toBeNull()
      expect(isWorkClip(CATALOG, clip as string)).toBe(true)
    }
  })
})
