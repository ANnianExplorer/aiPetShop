/**
 * 片段目录：随机链的权重、点击回应池、走位动作、工作状态槽与睡觉套组。
 *
 * 结构与参考实现 dsh-pet 的 `animations` 段一一对应（idle / turn / drag / clicks /
 * moves / categories / events / sleep），差别只在片段内容——那边是 109 段美术视频，
 * 这边是由 {@link CLIPS} 生成的关键帧。
 */
import type { Catalog } from './types'

/** 随机链权重：idle + turn + move 之外的份额自然归入分类动作（合计 100）。 */
export const CATALOG: Catalog = {
  idle: ['idle.breath'],
  turn: ['idle.look'],
  drag: ['drag.swing'],
  clicks: ['click.happy', 'click.surprised', 'click.angry', 'click.pat', 'click.wave'],
  moves: {
    default: { minDist: 60, maxDist: 240, margin: 20, leadSec: 2, tailSec: 2 },
    actions: [
      { clip: 'move.crab', params: { minDist: 40, maxDist: 120 } },
      { clip: 'move.run', params: { minDist: 120, maxDist: 320 } },
      { clip: 'move.float', params: { minDist: 40, maxDist: 120 } },
    ],
  },
  categories: [
    {
      id: '小动作',
      weight: 20,
      actions: ['act.stretch', 'act.hum', 'act.peek', 'act.shrug'],
    },
    {
      id: '玩耍',
      weight: 20,
      actions: ['act.dance', 'act.spin', 'act.peek', 'act.proud'],
    },
    {
      id: '吃什么',
      weight: 16,
      actions: ['act.eat', 'act.eatToken'],
    },
    {
      id: '心情',
      weight: 14,
      actions: ['act.proud', 'act.sleepy', 'act.hum'],
    },
    {
      id: '表情',
      weight: 10,
      noMirror: true,
      actions: ['act.shrug', 'act.sleepy'],
    },
  ],
  events: {
    workStatus: [
      ['work.thinking'],
      ['work.working'],
      ['work.result'],
      ['work.waiting'],
      ['work.success'],
      ['work.error'],
    ],
  },
  sleep: [{ start: 'sleep.start', loop: 'sleep.loop', end: 'sleep.end' }],
  weights: { idle: 10, turn: 5, move: 5 },
}
