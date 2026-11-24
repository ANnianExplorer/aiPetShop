/**
 * 内置桌宠形象：按用户当前宠物的类型挑一只，而不是所有宠物都套同一个角色。
 *
 * - cat → 橘猫
 * - dog → 柴犬
 * - other → 奶油兔
 *
 * 用户自己在 `/pet-studio` 生成过精灵图时，调用方仍然优先用那张图；
 * 这里只负责「没有自定义图时该显示什么」。
 */
import type { Pet } from '@/types'
import catUrl from '@/assets/pet/lumina-cat.svg?url'
import dogUrl from '@/assets/pet/lumina-dog.svg?url'
import bunnyUrl from '@/assets/pet/lumina-bunny.svg?url'

export type PetSpriteKind = 'cat' | 'dog' | 'bunny'

const DEFAULT_SPRITES: Record<PetSpriteKind, string> = {
  cat: catUrl,
  dog: dogUrl,
  bunny: bunnyUrl,
}

/** 宠物类型 → 内置形象；未知/未登录时用猫，至少不是空画布。 */
export function spriteKindForPetType(type: Pet['type'] | null | undefined): PetSpriteKind {
  if (type === 'dog') return 'dog'
  if (type === 'other') return 'bunny'
  return 'cat'
}

/** 宠物类型 → 内置精灵图资源地址。 */
export function defaultSpriteForPetType(type: Pet['type'] | null | undefined): string {
  return DEFAULT_SPRITES[spriteKindForPetType(type)]
}
