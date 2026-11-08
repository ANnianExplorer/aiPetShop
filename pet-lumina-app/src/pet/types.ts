/**
 * 桌宠引擎的公共类型。
 *
 * 引擎是「片段 + 姿态」模型：一段 Clip 回答「第 t 秒长什么样」，引擎只负责
 * 按状态机挑片段、叠加物理位移、把姿态画到 canvas。片段与状态机都是纯函数，
 * 渲染与 DOM 不参与决策——这样动画逻辑可以被单测钉住。
 *
 * 参考实现 dsh-pet 用 109 段 VP9-alpha 视频 + A/B 双缓冲播放；我们没有美术素材，
 * 因此把「片段」定义成关键帧轨道，由 canvas 每帧采样绘制，换来同样的
 * 「多动作、可打断、按权重掷骰、事件驱动」的结构。
 */

/** 朝向：决定整图镜像与走位方向。 */
export type Facing = 'left' | 'right'

/** 工作状态档位（顺序即 events.workStatus 的索引，勿在中间插档）。 */
export const WORK_STATES = ['thinking', 'working', 'result', 'waiting', 'success', 'error'] as const
export type WorkState = (typeof WORK_STATES)[number]

/** 工作状态 → 档位索引。 */
export const WORK_STATE_INDEX: Record<WorkState, number> = {
  thinking: 0,
  working: 1,
  result: 2,
  waiting: 3,
  success: 4,
  error: 5,
}

/** 道具：画在宠物周围的矢量小符号（爱心、问号、饭碗、token 硬币……）。 */
export type PropKind =
  | 'heart'
  | 'anger'
  | 'exclaim'
  | 'question'
  | 'dots'
  | 'zzz'
  | 'sweat'
  | 'star'
  | 'note'
  | 'onigiri'
  | 'token'
  | 'gear'
  | 'sparkle'

/** 道具实例；坐标是相对宠物盒的归一化值（0..1，左上为原点）。 */
export interface Prop {
  kind: PropKind
  x: number
  y: number
  scale?: number
  alpha?: number
  rotate?: number
}

/** 一帧的渲染姿态；未给出的字段取基准姿态。 */
export interface Pose {
  /** 横向 / 纵向缩放（1 = 原样）。 */
  scaleX: number
  scaleY: number
  /** 旋转（度，正数顺时针）。 */
  rotate: number
  /** 相对宠物盒宽 / 高的平移（0.01 = 1%）。 */
  offsetX: number
  offsetY: number
  /** 透明度。 */
  alpha: number
  /** 影子相对宽度的比例。 */
  shadow: number
  /** 是否镜像（只翻角色本体，道具上的文字不跟着翻）。 */
  mirror: boolean
  props: Prop[]
}

/** 片段采样结果：只写需要变化的字段。 */
export type Sample = Partial<Omit<Pose, 'props'>> & { props?: Prop[] }

/** 一段动画。 */
export interface Clip {
  /** 片段名（catalog 与事件都用它引用）。 */
  id: string
  /** 时长（ms）。 */
  duration: number
  /** 循环播放；false = 播一次触发 ended。 */
  loop: boolean
  /** 采样：t ∈ [0,1)，返回该时刻的姿态增量。 */
  sample: (t: number) => Sample
}

/** 片段注册表。 */
export type ClipMap = Readonly<Record<string, Clip>>

/** 走位参数（像素按基准宽度 462px 折算，运行时按实际尺寸等比缩放）。 */
export interface MoveParams {
  minDist: number
  maxDist: number
  margin: number
  leadSec: number
  tailSec: number
}

/** 走位动作：片段 + 距离区间。 */
export interface MoveAction {
  clip: string
  params?: Partial<MoveParams>
}

/** 动作分类（权重掷骰的最小单位）。 */
export interface Category {
  id: string
  weight: number
  /** 朝右时排除（文字类动作镜像后不可读）。 */
  noMirror?: boolean
  actions: string[]
}

/** 睡觉三段：必须是同一套（否则会出现「趴着入睡、站着醒来」）。 */
export interface SleepSet {
  start: string
  loop: string
  end: string
}

/** 工作状态文案槽：每档若干句，播放时随机抽一句。 */
export type WorkTexts = string[][]

/** 片段目录：随机链、互动与事件动画的全部配置。 */
export interface Catalog {
  idle: string[]
  turn: string[]
  drag: string[]
  clicks: string[]
  moves: {
    default: MoveParams
    actions: MoveAction[]
  }
  categories: Category[]
  events: {
    workStatus: string[][]
  }
  sleep: SleepSet[]
  weights: {
    idle: number
    turn: number
    move: number
  }
}

/** 物理参数：手感常量，集中在一处。 */
export interface PhysicsParams {
  gravity: number
  restitution: number
  groundFriction: number
  /** 甩出速度软上限（px/s）：cap×(1-e^(-s/cap))。 */
  maxThrowSpeed: number
  /** 低于它不抛，原地放下。 */
  deadZoneSpeed: number
  /** 参考宽度：配置里的像素距离按它折算。 */
  refWidth: number
}
