import { describe, expect, it } from 'vitest'
import { defaultSpriteForPetType, spriteKindForPetType } from './petSprite'

describe('petSprite', () => {
  it('按宠物类型映射到猫 / 狗 / 兔', () => {
    expect(spriteKindForPetType('cat')).toBe('cat')
    expect(spriteKindForPetType('dog')).toBe('dog')
    expect(spriteKindForPetType('other')).toBe('bunny')
  })

  it('未知或未选宠物时回退到猫，不返回空图', () => {
    expect(spriteKindForPetType(null)).toBe('cat')
    expect(spriteKindForPetType(undefined)).toBe('cat')
  })

  it('三种内置形象是各自独立的 SVG 资源', () => {
    const cat = defaultSpriteForPetType('cat')
    const dog = defaultSpriteForPetType('dog')
    const bunny = defaultSpriteForPetType('other')

    // Vite 可能把 SVG 内联成 data URI，也可能给资源路径；两种都接受，但要能区分
    const describes = (url: string, file: string, label: string) => {
      const decoded = decodeURIComponent(url)
      return decoded.includes(file) || decoded.includes(label)
    }
    expect(describes(cat, 'lumina-cat', 'chubby orange cat')).toBe(true)
    expect(describes(dog, 'lumina-dog', 'happy shiba dog')).toBe(true)
    expect(describes(bunny, 'lumina-bunny', 'fluffy cream rabbit')).toBe(true)
    expect(new Set([cat, dog, bunny]).size).toBe(3)
  })
})
