import { describe, expect, it } from 'vitest'
import { derivePetMood, moodAnimation } from './petMood'

describe('derivePetMood', () => {
  it('深夜优先睡觉，即使今天还没喂食', () => {
    const result = derivePetMood({
      hour: 1,
      feedingCount: 0,
      feedingTotal: 3,
      unreadReminders: 2,
      healthScore: 50,
    })
    expect(result.mood).toBe('sleepy')
  })

  it('早上还没喂完就是饿', () => {
    const result = derivePetMood({ hour: 9, feedingCount: 1, feedingTotal: 3, healthScore: 90 })
    expect(result.mood).toBe('hungry')
    expect(result.hintKey).toBe('pet.hint.hungry')
  })

  it('健康分过低会担心，优先于提醒', () => {
    const result = derivePetMood({ hour: 12, healthScore: 42, unreadReminders: 3 })
    expect(result.mood).toBe('worried')
    expect(result.hintKey).toBe('pet.hint.worried')
  })

  it('有未读提醒会提醒你', () => {
    const result = derivePetMood({ hour: 12, healthScore: 92, unreadReminders: 1, feedingCount: 3, feedingTotal: 3 })
    expect(result.mood).toBe('worried')
    expect(result.hintKey).toBe('pet.hint.reminder')
  })

  it('喂食完成且健康达标就是开心', () => {
    const result = derivePetMood({
      hour: 15,
      healthScore: 92,
      feedingCount: 3,
      feedingTotal: 3,
      todaySteps: 4200,
    })
    expect(result.mood).toBe('happy')
  })

  it('数据都缺时退回普通状态，不编造心情', () => {
    const result = derivePetMood({ hour: 14 })
    expect(result.mood).toBe('idle')
    expect(result.hintKey).toBe('pet.hint.idle')
    expect(result.name).toBe('Lumina')
  })

  it('没有名字时用 Lumina 兜底，有名字时保留', () => {
    expect(derivePetMood({ hour: 14, petName: '   ' }).name).toBe('Lumina')
    expect(derivePetMood({ hour: 14, petName: '年糕' }).name).toBe('年糕')
  })

  it('喂食计划为 0 时不误判为饿', () => {
    const result = derivePetMood({ hour: 20, feedingCount: 0, feedingTotal: 0, healthScore: 80 })
    expect(result.mood).not.toBe('hungry')
  })
})

describe('moodAnimation', () => {
  it('减少动效时一律静态', () => {
    expect(moodAnimation('happy', true)).toBe('pet-static')
  })

  it('不同心情给不同动画类名', () => {
    expect(moodAnimation('happy', false)).toBe('pet-bounce')
    expect(moodAnimation('sleepy', false)).toBe('pet-breathe')
    expect(moodAnimation('hungry', false)).toBe('pet-wiggle')
    expect(moodAnimation('worried', false)).toBe('pet-shake')
    expect(moodAnimation('idle', false)).toBe('pet-blink')
  })
})
