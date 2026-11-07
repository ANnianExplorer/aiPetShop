import { describe, expect, it } from 'vitest'
import { matchesCategory, normalizeCategory, POST_CATEGORY_TABS } from './postCategory'

describe('normalizeCategory', () => {
  it('新数据：英文 key 原样保留', () => {
    expect(normalizeCategory('cat')).toBe('cat')
    expect(normalizeCategory('daily')).toBe('daily')
  })

  it('历史中文展示名映射到 key', () => {
    expect(normalizeCategory('猫狗')).toBe('cat')
    expect(normalizeCategory('猫咪')).toBe('cat')
    expect(normalizeCategory('狗狗')).toBe('dog')
    expect(normalizeCategory('异宠')).toBe('exotic')
    expect(normalizeCategory('医疗健康')).toBe('medical')
    expect(normalizeCategory('医疗')).toBe('medical')
    expect(normalizeCategory('日常')).toBe('daily')
  })

  it('大小写与空白不敏感', () => {
    expect(normalizeCategory(' CAT ')).toBe('cat')
  })

  it('空值与未知值归到 other，不冒充任何一类', () => {
    expect(normalizeCategory('')).toBe('other')
    expect(normalizeCategory(null)).toBe('other')
    expect(normalizeCategory(undefined)).toBe('other')
    expect(normalizeCategory('随便写的')).toBe('other')
  })
})

describe('matchesCategory', () => {
  it('all 命中一切，包括未知分类', () => {
    expect(matchesCategory('随便写的', 'all')).toBe(true)
    expect(matchesCategory(null, 'all')).toBe(true)
  })

  it('按归一化后的 key 匹配（切语言不影响结果）', () => {
    expect(matchesCategory('猫狗', 'cat')).toBe(true)
    expect(matchesCategory('cat', 'cat')).toBe(true)
    expect(matchesCategory('猫狗', 'dog')).toBe(false)
  })

  it('未知分类只在 all 里出现', () => {
    expect(matchesCategory('随便写的', 'cat')).toBe(false)
  })

  it('每个 tab 都有稳定顺序，供 UI 直接渲染', () => {
    expect([...POST_CATEGORY_TABS]).toEqual(['all', 'daily', 'cat', 'dog', 'exotic', 'medical'])
  })
})
