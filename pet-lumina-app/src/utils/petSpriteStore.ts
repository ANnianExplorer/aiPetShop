/**
 * 桌宠精灵图的本地存储。
 *
 * 图片只在浏览器里：不经过 Agent、不上传对象存储。
 * 之所以用 localStorage 而不是 IndexedDB：单张 512px PNG 实测 < 300KB，
 * 同步读取能让 DeskPet 在挂载时立刻拿到图，不用等异步。
 *
 * 存储对象作为参数注入（默认走 localStorage）：测试传入会抛配额异常的实现，
 * 就不必去猴补 Storage.prototype。
 */

export interface PetSprite {
  /** PNG dataURL */
  dataUrl: string
  width: number
  height: number
  source: 'upload'
  createdAt: string
}

export const SPRITE_KEY = 'petlumina-deskpet-sprite'

export interface SpriteStorage {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

/** 部分浏览器隐私模式下 localStorage 会抛异常，读写都要兜底 */
export function resolveStorage(candidate?: SpriteStorage | null): SpriteStorage | null {
  if (candidate) return candidate
  try {
    const storage = localStorage
    const probe = '__pet_probe__'
    storage.setItem(probe, '1')
    storage.removeItem(probe)
    return storage
  } catch {
    return null
  }
}

export function isValidSprite(value: unknown): value is PetSprite {
  if (!value || typeof value !== 'object') return false
  const v = value as Record<string, unknown>
  return (
    typeof v.dataUrl === 'string' &&
    v.dataUrl.startsWith('data:image/') &&
    typeof v.width === 'number' &&
    v.width > 0 &&
    typeof v.height === 'number' &&
    v.height > 0
  )
}

export function loadSprite(storage?: SpriteStorage | null): PetSprite | null {
  const store = resolveStorage(storage)
  if (!store) return null
  const raw = store.getItem(SPRITE_KEY)
  if (!raw) return null
  try {
    const parsed: unknown = JSON.parse(raw)
    return isValidSprite(parsed) ? parsed : null
  } catch {
    // 坏数据不要反复报错，直接清掉
    store.removeItem(SPRITE_KEY)
    return null
  }
}

export type SaveResult = { ok: true } | { ok: false; reason: 'quota' | 'unavailable' | 'invalid' }

export function saveSprite(sprite: PetSprite, storage?: SpriteStorage | null): SaveResult {
  if (!isValidSprite(sprite)) return { ok: false, reason: 'invalid' }
  const store = resolveStorage(storage)
  if (!store) return { ok: false, reason: 'unavailable' }
  try {
    store.setItem(SPRITE_KEY, JSON.stringify(sprite))
    return { ok: true }
  } catch {
    // 配额满（Safari 隐私模式、或图过大）
    return { ok: false, reason: 'quota' }
  }
}

export function clearSprite(storage?: SpriteStorage | null): void {
  resolveStorage(storage)?.removeItem(SPRITE_KEY)
}
