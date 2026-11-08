import { beforeEach, describe, expect, it } from 'vitest'
import {
  clearSprite,
  isValidSprite,
  loadSprite,
  saveSprite,
  SPRITE_KEY,
  type PetSprite,
  type SpriteStorage,
} from './petSpriteStore'

const sprite: PetSprite = {
  dataUrl: 'data:image/png;base64,iVBORw0KGgo=',
  width: 128,
  height: 160,
  source: 'upload',
  createdAt: '2026-11-08T10:00:00.000Z',
}

/** 极简可注入存储：配额满只在写 SPRITE_KEY 时抛 */
class FakeStorage implements SpriteStorage {
  private map = new Map<string, string>()
  constructor(private readonly failKey?: string) {}

  getItem(key: string): string | null {
    return this.map.get(key) ?? null
  }

  setItem(key: string, value: string): void {
    if (key === this.failKey) throw new Error('QuotaExceededError')
    this.map.set(key, value)
  }

  removeItem(key: string): void {
    this.map.delete(key)
  }
}

beforeEach(() => {
  localStorage.clear()
})

describe('isValidSprite', () => {
  it('合法精灵图通过', () => {
    expect(isValidSprite(sprite)).toBe(true)
  })

  it('拒绝非图片、缺尺寸、非对象', () => {
    expect(isValidSprite({ ...sprite, dataUrl: 'https://x/y.png' })).toBe(false)
    expect(isValidSprite({ ...sprite, width: 0 })).toBe(false)
    expect(isValidSprite(null)).toBe(false)
    expect(isValidSprite('nope')).toBe(false)
  })
})

describe('save / load / clear', () => {
  it('存进去能原样读出来', () => {
    const store = new FakeStorage()
    expect(saveSprite(sprite, store)).toEqual({ ok: true })
    expect(loadSprite(store)).toEqual(sprite)
  })

  it('没存过返回 null', () => {
    expect(loadSprite(new FakeStorage())).toBeNull()
  })

  it('坏 JSON 返回 null 并清掉键（不反复报错）', () => {
    const store = new FakeStorage()
    store.setItem(SPRITE_KEY, '{not json')
    expect(loadSprite(store)).toBeNull()
    expect(store.getItem(SPRITE_KEY)).toBeNull()
  })

  it('结构不对也返回 null', () => {
    const store = new FakeStorage()
    store.setItem(SPRITE_KEY, JSON.stringify({ dataUrl: 'data:image/png;base64,AA', width: 0, height: 1 }))
    expect(loadSprite(store)).toBeNull()
  })

  it('clear 之后读不到', () => {
    const store = new FakeStorage()
    saveSprite(sprite, store)
    clearSprite(store)
    expect(loadSprite(store)).toBeNull()
  })

  it('配额不足时返回 quota 而不是抛异常', () => {
    const result = saveSprite(sprite, new FakeStorage(SPRITE_KEY))
    expect(result).toEqual({ ok: false, reason: 'quota' })
  })

  it('非法结构直接拒绝，不触碰存储', () => {
    expect(saveSprite({ ...sprite, width: -1 }, new FakeStorage())).toEqual({ ok: false, reason: 'invalid' })
  })

  it('默认走 localStorage（真实环境路径）', () => {
    expect(saveSprite(sprite)).toEqual({ ok: true })
    expect(loadSprite()).toEqual(sprite)
  })
})
