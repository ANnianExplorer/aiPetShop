/**
 * 桌宠状态机（纯函数）。
 *
 * 设计约束：
 * - 只用真实数据（宠物名、健康分、步数、喂食进度、未读提醒、当前时间），
 *   不编造「亲密度」「心情值」这类库里没有的数字；
 * - 不做随机，输入一样输出一样，便于单测；
 * - 输出只描述「显示什么」，不碰 DOM / 定时器，组件只负责渲染。
 */

export type PetMood = 'happy' | 'hungry' | 'sleepy' | 'worried' | 'idle'

export interface PetMoodInput {
  readonly petName?: string | null
  readonly healthScore?: number | null
  readonly todaySteps?: number | null
  /** 今日喂食次数 / 计划次数 */
  readonly feedingCount?: number | null
  readonly feedingTotal?: number | null
  readonly unreadReminders?: number | null
  /** 0–23，默认取当前小时 */
  readonly hour?: number
}

export interface PetMoodResult {
  readonly mood: PetMood
  /** 状态说明的 i18n key（zh/en/ja 三语都有） */
  readonly hintKey: string
  /** 展示用的名字，没有宠物时回退到 Lumina */
  readonly name: string
}

const DEFAULT_NAME = 'Lumina'

export function derivePetMood(input: PetMoodInput): PetMoodResult {
  const hour = input.hour ?? new Date().getHours()
  const name = (input.petName || '').trim() || DEFAULT_NAME
  const feedingTotal = input.feedingTotal ?? 0
  const feedingCount = input.feedingCount ?? 0
  const health = input.healthScore ?? 0
  const steps = input.todaySteps ?? 0
  const unread = input.unreadReminders ?? 0

  // 深夜优先：不该因为「今天还没喂」把宠物叫醒提要求
  if (hour >= 23 || hour < 6) {
    return { mood: 'sleepy', hintKey: 'pet.hint.sleepy', name }
  }
  if (health > 0 && health < 60) {
    return { mood: 'worried', hintKey: 'pet.hint.worried', name }
  }
  if (unread > 0) {
    return { mood: 'worried', hintKey: 'pet.hint.reminder', name }
  }
  if (feedingTotal > 0 && feedingCount < feedingTotal) {
    return { mood: 'hungry', hintKey: 'pet.hint.hungry', name }
  }
  if (steps >= 3000 || health >= 85) {
    return { mood: 'happy', hintKey: 'pet.hint.happy', name }
  }
  return { mood: 'idle', hintKey: 'pet.hint.idle', name }
}

/** 组件用来决定动画类名；减少动效时统一降级为静态。 */
export function moodAnimation(mood: PetMood, reducedMotion: boolean): string {
  if (reducedMotion) return 'pet-static'
  switch (mood) {
    case 'happy':
      return 'pet-bounce'
    case 'sleepy':
      return 'pet-breathe'
    case 'hungry':
      return 'pet-wiggle'
    case 'worried':
      return 'pet-shake'
    default:
      return 'pet-blink'
  }
}
