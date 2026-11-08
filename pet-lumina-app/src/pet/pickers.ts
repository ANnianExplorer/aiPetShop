/**
 * 随机链与播完判定：桌宠「下一步播什么」的全部决策。
 *
 * 全部纯函数（随机数从调用方传入），与渲染、物理、DOM 无关——
 * 这样「掷到 move 之后不该重播动作」「互动播完要回到工作状态」这类规则
 * 可以逐条钉在单测里，而不是靠肉眼观察。
 */
import type { Catalog, Category, Facing, WorkState } from './types'
import { WORK_STATE_INDEX } from './types'

/** 掷骰结果类别。 */
export type RollKind = 'idle' | 'turn' | 'move' | 'action'

/** 等概率抽取；`exclude` 用来避免连续重复。池被排空时退回原池（宁可重复也不返回 undefined）。 */
export function pick<T>(pool: readonly T[], exclude?: T): T {
  const filtered = exclude === undefined ? pool : pool.filter((item) => item !== exclude)
  const source = filtered.length > 0 ? filtered : pool
  return source[Math.floor(Math.random() * source.length)]
}

/**
 * 按权重掷骰：`roll ∈ [0,1)` → 下一段属于哪一类。
 *
 * idle / turn / move 的权重除以 100 是这三档的占比，剩余全部归入分类动作。
 * `fixed` 为真时（宠物被钉在角落）不转向也不走位，份额自然落进 action。
 */
export function rollKind(
  roll: number,
  weights: Catalog['weights'],
  options?: { fixed?: boolean },
): RollKind {
  const turn = options?.fixed ? 0 : weights.turn
  const move = options?.fixed ? 0 : weights.move
  const idleEnd = weights.idle / 100
  const turnEnd = (weights.idle + turn) / 100
  const moveEnd = (weights.idle + turn + move) / 100
  if (roll < idleEnd) return 'idle'
  if (roll < turnEnd) return 'turn'
  if (roll < moveEnd) return 'move'
  return 'action'
}

/** 按权重选分类；朝右时排除 `noMirror` 分类并归一化剩余权重。没有可用分类返回 null。 */
export function pickWeightedCategory(
  categories: readonly Category[],
  facing: Facing,
  random: () => number = Math.random,
): Category | null {
  const playable = categories.filter((category) => category.actions.length > 0)
  if (playable.length === 0) return null
  const mirrored = playable.filter((category) => !(category.noMirror && facing === 'right'))
  const eligible = mirrored.length > 0 ? mirrored : playable
  const total = eligible.reduce((sum, category) => sum + category.weight, 0) || 1
  let threshold = random() * total
  for (const category of eligible) {
    threshold -= category.weight
    if (threshold <= 0) return category
  }
  return eligible[eligible.length - 1]
}

/** 从分类池挑一段动作；分类为空时退回待机池。 */
export function pickCategoryAction(
  catalog: Catalog,
  facing: Facing,
  current: string,
  random: () => number = Math.random,
): { category: string; clip: string } {
  const category = pickWeightedCategory(catalog.categories, facing, random)
  if (category === null) {
    return { category: 'FALLBACK', clip: pick(catalog.idle, current) }
  }
  return { category: category.id, clip: pick(category.actions, current) }
}

/** 下一段的决策结果。 */
export interface NextDecision {
  /** 落在哪一档（idle / turn / move / 分类 id）。 */
  kind: string
  /** 要播的片段；`null` = 走位已经开始自己切动画，这里不要重播。 */
  clip: string | null
  /** 是否由本次决策切片段。 */
  play: boolean
}

/** 决策输入。 */
export interface NextInput {
  kind: RollKind
  catalog: Catalog
  facing: Facing
  /** 当前正在播的片段（避免连续重复）。 */
  current: string
  /** 走位结果：未尝试 = undefined；已在走 = 移动片段名；走不动 = false。 */
  move?: string | false
  random?: () => number
}

/**
 * 决定下一段自播动画。
 *
 * 走位成功时**不切片段**：走位那条链自己已经切到移动片段，
 * 这里再切一次会把刚开头的走路打断，表现为「原地抽搐」。
 */
export function decideNextClip(input: NextInput): NextDecision {
  const { kind, catalog, facing, current } = input
  if (kind === 'idle') {
    return { kind: 'idle', clip: pick(catalog.idle, current), play: true }
  }
  if (kind === 'turn') {
    return { kind: 'turn', clip: pick(catalog.turn, current), play: true }
  }
  if (kind === 'move' && typeof input.move === 'string') {
    return { kind: 'move', clip: null, play: false }
  }
  const action = pickCategoryAction(catalog, facing, current, input.random)
  return { kind: action.category, clip: action.clip, play: true }
}

/** 播完之后的去向。 */
export type EndedCue =
  | { kind: 'ignore' }
  | { kind: 'work-rotate'; clip: string }
  | { kind: 'work-replay' }
  | { kind: 'event-done' }
  | { kind: 'turn' }
  | { kind: 'interaction-done' }
  | { kind: 'random' }

/** 工作状态是否仍在进行（success / error 是终态，播完即回到随机链）。 */
export function isWorkActive(state: WorkState | null): boolean {
  return state !== null && state !== 'success' && state !== 'error'
}

/** 片段是否属于某个池。 */
function inPool(pool: readonly string[] | undefined, clip: string): boolean {
  return pool !== undefined && pool.includes(clip)
}

/** 片段是否属于工作状态槽。 */
export function isWorkClip(catalog: Catalog, clip: string): boolean {
  return catalog.events.workStatus.some((slot) => slot.includes(clip))
}

/** 当前工作状态档位里的片段；没有对应槽返回 null。 */
export function workClipFor(
  catalog: Catalog,
  state: WorkState,
  current?: string,
): string | null {
  const slot = catalog.events.workStatus[WORK_STATE_INDEX[state]]
  if (slot === undefined || slot.length === 0) return null
  return pick(slot, current)
}

/**
 * 播完判定。
 *
 * - 工作动画且状态仍在进行：档内有多段就换一段（长任务不会循环同一帧），单段原地重播；
 * - 其他工作动画（含 success / error）：事件结束，回待机或回到当前档位循环；
 * - 转向段播完：翻转朝向（调用方负责刷新掷骰用的朝向）；
 * - 拖拽 / 点击回应播完：算一次互动结束；
 * - 其余：继续掷骰。
 */
export function decideEndedCue(input: {
  catalog: Catalog
  current: string
  workState: WorkState | null
}): EndedCue {
  const { catalog, current, workState } = input
  if (isWorkClip(catalog, current)) {
    const slot = catalog.events.workStatus.find((items) => items.includes(current))
    if (slot !== undefined && isWorkActive(workState)) {
      const next = slot.filter((item) => item !== current)
      if (slot.length > 1 && next.length > 0) {
        return { kind: 'work-rotate', clip: pick(next) }
      }
      return { kind: 'work-replay' }
    }
    return { kind: 'event-done' }
  }
  if (inPool(catalog.turn, current)) return { kind: 'turn' }
  if (inPool(catalog.drag, current) || inPool(catalog.clicks, current)) {
    return { kind: 'interaction-done' }
  }
  return { kind: 'random' }
}
