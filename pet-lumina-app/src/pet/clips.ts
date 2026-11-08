/**
 * 片段库：桌宠全部动作的定义。
 *
 * 每一段都回答「t（0..1）时长什么样」，不读 DOM、不看时间源；引擎负责推进 t。
 * 动作范围对齐参考实现 dsh-pet 的配置结构：待机 / 转向 / 拖拽 / 点击回应 /
 * 分类动作 / 工作状态 / 睡觉三段 / 走位。
 */
import { clamp01, easeInOut, easeOut, pulse, track, wave } from './easing'
import type { Clip, ClipMap, Prop } from './types'

/** 基准姿态：站立、居中、实心、有影子。 */
const BASE = {
  scaleX: 1,
  scaleY: 1,
  rotate: 0,
  offsetX: 0,
  offsetY: 0,
  alpha: 1,
  shadow: 0.52,
} as const

/** 定义一段片段；`loop` 缺省为 false（播一次）。 */
function define(id: string, duration: number, loop: boolean, sample: Clip['sample']): Clip {
  return { id, duration, loop, sample }
}

/** 一组道具。 */
function props(...items: Prop[]): Prop[] {
  return items
}

/** 三颗爱心，随时间上浮；`spread` 控制横向散开。 */
function hearts(t: number, spread = 0.16): Prop[] {
  return [0, 0.33, 0.66].map((phase, index) => {
    const local = (t + phase) % 1
    return {
      kind: 'heart' as const,
      x: 0.5 + (index - 1) * spread + wave(local, 0.02),
      y: 0.42 - local * 0.26,
      scale: 0.7 + local * 0.4,
      alpha: local < 0.15 ? local / 0.15 : 1 - (local - 0.15) / 0.85,
    }
  })
}

/** 三个浮现的 z，循环上浮。 */
function zzz(t: number): Prop[] {
  return [0, 0.33, 0.66].map((phase, index) => {
    const local = (t + phase) % 1
    return {
      kind: 'zzz' as const,
      x: 0.62 + index * 0.09 + local * 0.05,
      y: 0.3 - local * 0.16,
      scale: 0.6 + index * 0.2,
      alpha: local < 0.2 ? local / 0.2 : 1 - (local - 0.2) / 0.8,
      rotate: wave(local, 8),
    }
  })
}

/** 三颗思考点，逐个亮起。 */
function dots(t: number): Prop[] {
  return [0, 0.33, 0.66].map((phase, index) => {
    const local = (t + phase) % 1
    return {
      kind: 'dots' as const,
      x: 0.55 + index * 0.06,
      y: 0.34,
      scale: 0.7,
      alpha: 0.25 + 0.75 * Math.max(0, Math.sin(local * Math.PI)),
    }
  })
}

const DRAG = define('drag.swing', 900, true, (t) => ({
  scaleX: 0.95,
  scaleY: 1.07,
  rotate: wave(t, 3.5),
  offsetY: -0.01,
}))

const IDLE = define('idle.breath', 3800, true, (t) => {
  const breath = wave(t)
  return {
    scaleX: 1 - 0.01 * breath,
    scaleY: 1 + 0.014 * breath,
    offsetY: -0.012 * breath,
    shadow: 0.54 - 0.02 * breath,
  }
})

const LOOK = define('idle.look', 2400, false, (t) => ({
  rotate: track(
    [
      { at: 0, value: 0 },
      { at: 0.18, value: 0 },
      { at: 0.32, value: -4, ease: easeOut },
      { at: 0.46, value: -4 },
      { at: 0.62, value: 5, ease: easeInOut },
      { at: 0.76, value: 5 },
      { at: 0.92, value: 0, ease: easeInOut },
      { at: 1, value: 0 },
    ],
    t,
  ),
  offsetX: track(
    [
      { at: 0, value: 0 },
      { at: 0.32, value: -0.02 },
      { at: 0.62, value: 0.03 },
      { at: 0.92, value: 0 },
      { at: 1, value: 0 },
    ],
    t,
  ),
}))

const CLICK_HAPPY = define('click.happy', 1100, false, (t) => {
  const hop = Math.abs(Math.sin(t * Math.PI * 2))
  return {
    offsetY: -0.09 * hop,
    scaleY: 1 + 0.03 * hop,
    scaleX: 1 - 0.02 * hop,
    shadow: 0.52 - 0.16 * hop,
    props: hearts(t),
  }
})

const CLICK_SURPRISED = define('click.surprised', 900, false, (t) => ({
  scaleX: 1 + 0.07 * pulse(t * 2),
  scaleY: 1 + 0.09 * pulse(t * 2),
  rotate: wave(t, 2),
  offsetY: -0.02 * pulse(t * 2),
  props: props({
    kind: 'exclaim',
    x: 0.74,
    y: 0.14,
    scale: 0.8 + 0.35 * pulse(t),
    alpha: t < 0.1 ? t / 0.1 : t > 0.85 ? (1 - t) / 0.15 : 1,
  }),
}))

const CLICK_ANGRY = define('click.angry', 1200, false, (t) => ({
  offsetX: wave(t * 5, 0.018),
  rotate: wave(t * 5, 3),
  scaleX: 1 + 0.03 * pulse(t),
  scaleY: 1 - 0.02 * pulse(t),
  props: props({
    kind: 'anger',
    x: 0.72,
    y: 0.16,
    scale: 0.9 + 0.2 * Math.abs(wave(t * 2)),
    alpha: t < 0.1 ? t / 0.1 : t > 0.85 ? (1 - t) / 0.15 : 1,
  }),
}))

const CLICK_PAT = define('click.pat', 1000, false, (t) => ({
  scaleX: 1 + 0.05 * pulse(t),
  scaleY: 1 - 0.06 * pulse(t),
  offsetY: 0.01 * pulse(t),
  props: hearts(t, 0.1),
}))

const CLICK_WAVE = define('click.wave', 1400, false, (t) => ({
  rotate: wave(t * 2, 6),
  scaleX: 1 + 0.02 * pulse(t),
  props: props({
    kind: 'note',
    x: 0.68,
    y: 0.34 - 0.1 * t,
    scale: 0.9,
    alpha: t < 0.15 ? t / 0.15 : 1 - (t - 0.15) / 0.85,
    rotate: wave(t * 2, 12),
  }),
}))

const ACT_DANCE = define('act.dance', 2400, false, (t) => {
  const beat = wave(t * 3)
  return {
    rotate: beat * 7,
    offsetY: -0.05 * Math.abs(beat),
    scaleY: 1 + 0.02 * beat,
    shadow: 0.52 - 0.08 * Math.abs(beat),
    props: props(
      {
        kind: 'note',
        x: 0.28 + 0.05 * wave(t * 2, 1),
        y: 0.4 - 0.1 * t,
        scale: 0.8,
        alpha: 1 - t,
      },
      {
        kind: 'note',
        x: 0.7 + 0.05 * wave(t * 2 + 0.3, 1),
        y: 0.36 - 0.08 * t,
        scale: 0.7,
        alpha: 1 - t,
        rotate: 10,
      },
    ),
  }
})

const ACT_STRETCH = define('act.stretch', 1900, false, (t) => {
  const reach = track(
    [
      { at: 0, value: 0 },
      { at: 0.35, value: 1, ease: easeOut },
      { at: 0.62, value: 0.35 },
      { at: 1, value: 0 },
    ],
    t,
  )
  return {
    scaleY: 1 + 0.1 * reach,
    scaleX: 1 - 0.05 * reach,
    offsetY: -0.02 * reach,
    rotate: wave(t, 1.5),
    props: props({
      kind: 'sparkle',
      x: 0.76,
      y: 0.2,
      scale: 0.6 + 0.5 * reach,
      alpha: reach,
    }),
  }
})

const ACT_HUM = define('act.hum', 2200, false, (t) => ({
  rotate: wave(t * 2, 2.5),
  scaleY: 1 + 0.01 * wave(t * 2),
  props: props({
    kind: 'note',
    x: 0.66,
    y: 0.36 - 0.12 * t,
    scale: 0.8,
    alpha: t < 0.2 ? t / 0.2 : 1 - (t - 0.2) / 0.8,
    rotate: wave(t * 3, 10),
  }),
}))

const ACT_SPIN = define('act.spin', 1500, false, (t) => ({
  rotate: 360 * easeInOut(t),
  offsetY: -0.03 * pulse(t),
  scaleY: 1 + 0.03 * pulse(t),
}))

const ACT_PEEK = define('act.peek', 1800, false, (t) => ({
  rotate: track(
    [
      { at: 0, value: 0 },
      { at: 0.25, value: -7, ease: easeOut },
      { at: 0.6, value: 7, ease: easeInOut },
      { at: 1, value: 0 },
    ],
    t,
  ),
  offsetX: track(
    [
      { at: 0, value: 0 },
      { at: 0.25, value: -0.04 },
      { at: 0.6, value: 0.04 },
      { at: 1, value: 0 },
    ],
    t,
  ),
  scaleY: 0.98,
  props: dots(t),
}))

const ACT_EAT = define('act.eat', 2600, false, (t) => ({
  rotate: -4 + wave(t * 6, 1.5),
  offsetY: 0.012,
  scaleY: 1 - 0.01 * Math.abs(wave(t * 6)),
  props: props(
    {
      kind: 'onigiri',
      x: 0.5,
      y: 0.84,
      scale: 0.9,
      alpha: t < 0.12 ? t / 0.12 : t > 0.9 ? (1 - t) / 0.1 : 1,
    },
    {
      kind: 'sparkle',
      x: 0.62,
      y: 0.6 - 0.12 * t,
      scale: 0.5,
      alpha: t < 0.2 ? t / 0.2 : 1 - (t - 0.2) / 0.8,
    },
  ),
}))

const ACT_EAT_TOKEN = define('act.eatToken', 2800, false, (t) => ({
  rotate: -3 + wave(t * 5, 2),
  offsetY: -0.01 * Math.abs(wave(t * 5)),
  props: props(
    {
      kind: 'token',
      x: 0.5 + wave(t * 3, 0.03),
      y: 0.5,
      scale: 0.8 + 0.3 * Math.abs(wave(t * 5)),
      alpha: t < 0.1 ? t / 0.1 : t > 0.9 ? (1 - t) / 0.1 : 1,
      rotate: wave(t * 4, 20),
    },
    {
      kind: 'star',
      x: 0.66,
      y: 0.32 - 0.08 * t,
      scale: 0.5,
      alpha: 1 - t,
    },
  ),
}))

const ACT_SLEEPY = define('act.sleepy', 2000, false, (t) => ({
  rotate: 5 + wave(t, 1),
  scaleY: 1 - 0.01 * pulse(t),
  props: props({
    kind: 'zzz',
    x: 0.7,
    y: 0.26 - 0.1 * t,
    scale: 0.7,
    alpha: 1 - t,
  }),
}))

const ACT_PROUD = define('act.proud', 1800, false, (t) => ({
  scaleX: 1 + 0.03 * pulse(t * 1.2),
  scaleY: 1 + 0.02 * pulse(t * 1.2),
  offsetY: -0.01 * pulse(t * 1.2),
  props: props({
    kind: 'star',
    x: 0.7,
    y: 0.24,
    scale: 0.5 + 0.4 * pulse(t),
    alpha: t < 0.15 ? t / 0.15 : t > 0.85 ? (1 - t) / 0.15 : 1,
    rotate: wave(t * 2, 15),
  }),
}))

const ACT_SHRUG = define('act.shrug', 1600, false, (t) => ({
  rotate: track(
    [
      { at: 0, value: 0 },
      { at: 0.3, value: -6, ease: easeOut },
      { at: 0.7, value: -6 },
      { at: 1, value: 0 },
    ],
    t,
  ),
  offsetY: 0.008,
  props: props({ kind: 'question', x: 0.68, y: 0.26, scale: 0.8, alpha: pulse(t) }),
}))

const WHISPER = define('whisper.talk', 1200, false, (t) => ({
  offsetY: -0.004 * Math.abs(wave(t * 4)),
  rotate: wave(t * 2, 1.2),
}))

const WORK_THINKING = define('work.thinking', 1600, true, (t) => ({
  rotate: -3 + wave(t, 1.2),
  offsetY: -0.006 * Math.abs(wave(t)),
  props: dots(t),
}))

const WORK_WORKING = define('work.working', 900, true, (t) => {
  const hop = Math.abs(Math.sin(t * Math.PI * 2))
  return {
    offsetY: -0.025 * hop,
    scaleY: 1 + 0.015 * hop,
    rotate: wave(t * 2, 1.4),
    props: props({
      kind: 'gear',
      x: 0.72,
      y: 0.3,
      scale: 0.7,
      rotate: 360 * t,
    }),
  }
})

const WORK_RESULT = define('work.result', 900, false, (t) => ({
  rotate: wave(t * 2, 3),
  props: props({
    kind: 'sparkle',
    x: 0.7,
    y: 0.28,
    scale: 0.5 + 0.3 * pulse(t),
    alpha: t < 0.2 ? t / 0.2 : 1 - (t - 0.2) / 0.8,
  }),
}))

const WORK_WAITING = define('work.waiting', 1800, true, (t) => ({
  rotate: 3,
  offsetY: -0.004 * Math.abs(wave(t)),
  props: props({
    kind: 'question',
    x: 0.7,
    y: 0.26 + 0.02 * wave(t),
    scale: 0.8,
    alpha: 0.6 + 0.4 * Math.abs(wave(t)),
    rotate: wave(t, 8),
  }),
}))

const WORK_SUCCESS = define('work.success', 1500, false, (t) => {
  const hop = Math.abs(Math.sin(t * Math.PI * 2))
  return {
    offsetY: -0.12 * hop,
    scaleY: 1 + 0.03 * hop,
    scaleX: 1 - 0.02 * hop,
    rotate: wave(t * 2, 3),
    shadow: 0.52 - 0.18 * hop,
    props: props(
      {
        kind: 'star',
        x: 0.3,
        y: 0.3 - 0.1 * t,
        scale: 0.6,
        alpha: 1 - t,
        rotate: wave(t * 2, 20),
      },
      {
        kind: 'star',
        x: 0.72,
        y: 0.26 - 0.08 * t,
        scale: 0.5,
        alpha: 1 - t,
        rotate: wave(t * 2 + 0.4, 20),
      },
    ),
  }
})

const WORK_ERROR = define('work.error', 1400, false, (t) => ({
  scaleY: 0.95 + 0.01 * wave(t),
  scaleX: 1.02,
  rotate: 5,
  offsetY: 0.012,
  props: props({
    kind: 'sweat',
    x: 0.72,
    y: 0.3 + 0.06 * t,
    scale: 0.8,
    alpha: t < 0.15 ? t / 0.15 : 1 - (t - 0.15) / 0.85,
  }),
}))

const SLEEP_START = define('sleep.start', 900, false, (t) => ({
  rotate: track(
    [
      { at: 0, value: 0 },
      { at: 0.7, value: 9, ease: easeInOut },
      { at: 1, value: 9 },
    ],
    t,
  ),
  offsetY: 0.02 * t,
  scaleY: 0.97,
  alpha: 1 - 0.08 * t,
}))

const SLEEP_LOOP = define('sleep.loop', 4200, true, (t) => {
  const breath = wave(t)
  return {
    rotate: 9,
    offsetY: 0.02,
    scaleX: 1 - 0.008 * breath,
    scaleY: 0.97 + 0.012 * breath,
    alpha: 0.92,
    shadow: 0.5,
    props: zzz(t),
  }
})

const SLEEP_END = define('sleep.end', 800, false, (t) => ({
  rotate: 9 - 9 * easeOut(t),
  offsetY: 0.02 * (1 - t),
  scaleY: 0.97 + 0.03 * pulse(t),
  alpha: 0.92 + 0.08 * t,
  props: props({
    kind: 'sparkle',
    x: 0.64,
    y: 0.3,
    scale: 0.4 + 0.3 * pulse(t),
    alpha: 1 - t,
  }),
}))

const MOVE_CRAB = define('move.crab', 700, true, (t) => ({
  offsetY: -0.018 * Math.abs(wave(t)),
  rotate: wave(t, 3),
  scaleX: 0.99,
  shadow: 0.52 - 0.05 * Math.abs(wave(t)),
}))

const MOVE_RUN = define('move.run', 520, true, (t) => ({
  offsetY: -0.04 * Math.abs(wave(t)),
  rotate: 4 + wave(t, 2),
  scaleY: 0.99,
  shadow: 0.52 - 0.1 * Math.abs(wave(t)),
}))

const MOVE_FLOAT = define('move.float', 900, true, (t) => ({
  offsetY: -0.02 + 0.015 * wave(t),
  rotate: wave(t, 2),
}))

/** 全部片段；键就是片段名。 */
export const CLIPS: ClipMap = {
  'idle.breath': IDLE,
  'idle.look': LOOK,
  'drag.swing': DRAG,
  'click.happy': CLICK_HAPPY,
  'click.surprised': CLICK_SURPRISED,
  'click.angry': CLICK_ANGRY,
  'click.pat': CLICK_PAT,
  'click.wave': CLICK_WAVE,
  'act.dance': ACT_DANCE,
  'act.stretch': ACT_STRETCH,
  'act.hum': ACT_HUM,
  'act.spin': ACT_SPIN,
  'act.peek': ACT_PEEK,
  'act.eat': ACT_EAT,
  'act.eatToken': ACT_EAT_TOKEN,
  'act.sleepy': ACT_SLEEPY,
  'act.proud': ACT_PROUD,
  'act.shrug': ACT_SHRUG,
  'whisper.talk': WHISPER,
  'work.thinking': WORK_THINKING,
  'work.working': WORK_WORKING,
  'work.result': WORK_RESULT,
  'work.waiting': WORK_WAITING,
  'work.success': WORK_SUCCESS,
  'work.error': WORK_ERROR,
  'sleep.start': SLEEP_START,
  'sleep.loop': SLEEP_LOOP,
  'sleep.end': SLEEP_END,
  'move.crab': MOVE_CRAB,
  'move.run': MOVE_RUN,
  'move.float': MOVE_FLOAT,
}

export { BASE }
