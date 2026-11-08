/**
 * 工作状态信号：把「Agent 正在想 / 正在调工具 / 完成了」广播给桌宠。
 *
 * 用极简的订阅器而不是 Pinia store：桌宠是全局浮层，可能在任何页面挂着；
 * 信号只往一个方向流（业务 → 桌宠），没有反向写回，用 store 反而多一层映射。
 * 没有订阅者时发布也不报错，未挂桌宠的页面照常跑。
 */
import type { WorkState } from './types'

type Listener = (state: WorkState | null) => void

const listeners = new Set<Listener>()

/** 发布工作状态；null = 空闲。 */
export function publishWorkState(state: WorkState | null): void {
  for (const listener of listeners) {
    try {
      listener(state)
    } catch {
      // 单个订阅者出错不能影响其它页面
    }
  }
}

/** 订阅工作状态；返回取消函数。 */
export function subscribeWorkState(listener: Listener): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}
