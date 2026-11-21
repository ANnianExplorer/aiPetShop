/**
 * 对话流 → 气泡状态 的纯函数归约器。
 *
 * 抽出来单独放，是为了让「事件如何改变界面」可以被单测覆盖：
 * 组件只负责调用它并把结果渲染出来，不掺业务判断。
 */

import {
  isDeltaEvent,
  isDoneEvent,
  isErrorEvent,
  isRouteEvent,
  isToolEvent,
} from '@/api/agent'
import type { AgentEvent } from '@/api/agent'
import type { ChatBubble } from '@/types/agent'

export interface ReduceResult {
  /** 服务端分配/确认的会话 id（route 与 done 都会带） */
  sessionId?: string
  /** 服务端原始错误文案；仅用于未知 code 的兜底展示 */
  error?: string
  /** 稳定错误码；界面按它映射三语文案 */
  errorCode?: string
  /** 限流 / 熔断时服务端建议的重试等待秒数 */
  retryAfterS?: number
  /** true 表示这条气泡应该被丢弃（还没输出内容就失败了） */
  dropBubble?: boolean
}

export function applyAgentEvent(bubble: ChatBubble, event: AgentEvent): ReduceResult {
  const { data } = event

  if (event.event === 'route' && isRouteEvent(data)) {
    return { sessionId: data.session_id }
  }

  if (event.event === 'tool' && isToolEvent(data)) {
    bubble.tools = [...bubble.tools, data]
    return {}
  }

  if (event.event === 'delta' && isDeltaEvent(data)) {
    bubble.content += data.text
    return {}
  }

  if (event.event === 'done' && isDoneEvent(data)) {
    bubble.content = data.answer
    bubble.citations = data.citations ?? []
    bubble.streaming = false
    return { sessionId: data.session_id }
  }

  if (event.event === 'error' && isErrorEvent(data)) {
    bubble.streaming = false
    const retryAfterS = data.detail?.retry_after_s
    return {
      error: data.message,
      errorCode: data.code,
      retryAfterS:
        typeof retryAfterS === 'number' && Number.isFinite(retryAfterS) ? retryAfterS : undefined,
      dropBubble: bubble.content.length === 0,
    }
  }

  return {}
}

/** 历史接口返回的消息 → 气泡（只保留 user/assistant，工具痕迹不回溯） */
export function historyToBubbles(
  messages: ReadonlyArray<{ id: string; role: string; content: string; citations?: ChatBubble['citations'] }>,
): ChatBubble[] {
  return messages
    .filter((message) => message.role === 'user' || message.role === 'assistant')
    .map((message) => ({
      id: message.id,
      role: message.role === 'user' ? ('user' as const) : ('assistant' as const),
      content: message.content,
      citations: message.citations ?? [],
      tools: [],
    }))
}
