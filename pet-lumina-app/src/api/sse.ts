/**
 * Server-Sent Events 增量解析器。
 *
 * 为什么不直接用 `EventSource`：
 * 1. 它不带自定义请求头，而我们的接口要 `satoken`；
 * 2. 它不接受 POST 请求体（对话需要把 message 发过去）；
 * 3. 断线续传要自己带 `Last-Event-ID`，EventSource 只会重连同一个 URL。
 *
 * 这里只做纯文本 → 事件的解析，不碰网络，方便单测逐块喂数据。
 */

export interface SseMessage {
  /** 事件序号，服务端保证同一 run 内递增 */
  id?: number
  /** 事件名，如 route / tool / delta / done / error */
  event: string
  /** 原始 data 文本（未做 JSON 解析） */
  data: string
}

const NEXT_LINE = '\n'

/** 按 SSE 规范解析：空行分隔记录，`field: value` 组装，data 多行以换行拼接。 */
export class SseDecoder {
  private buffer = ''

  /** 喂入一个网络分片，返回其中已完整的记录（可能为空数组） */
  push(chunk: string): SseMessage[] {
    // 统一换行：CDN/代理可能把 \n 改写成 \r\n
    this.buffer += chunk.replace(/\r\n?/g, NEXT_LINE)
    const messages: SseMessage[] = []

    let index = this.buffer.indexOf(NEXT_LINE + NEXT_LINE)
    while (index !== -1) {
      const raw = this.buffer.slice(0, index)
      this.buffer = this.buffer.slice(index + 2)
      const message = parseRecord(raw)
      if (message) {
        messages.push(message)
      }
      index = this.buffer.indexOf(NEXT_LINE + NEXT_LINE)
    }
    return messages
  }

  /** 流结束时调用：把残留的不带空行结尾的记录也解析出来 */
  flush(): SseMessage[] {
    const rest = this.buffer
    this.buffer = ''
    const message = rest.trim() ? parseRecord(rest) : null
    return message ? [message] : []
  }
}

function parseRecord(raw: string): SseMessage | null {
  let id: number | undefined
  let event = 'message'
  const dataLines: string[] = []

  for (const line of raw.split(NEXT_LINE)) {
    if (!line || line.startsWith(':')) {
      continue // 注释行（心跳）直接跳过
    }
    const colon = line.indexOf(':')
    const field = colon === -1 ? line : line.slice(0, colon)
    const value = colon === -1 ? '' : line.slice(colon + 1).replace(/^ /, '')

    if (field === 'id') {
      const parsed = Number(value)
      id = Number.isFinite(parsed) ? parsed : undefined
    } else if (field === 'event') {
      event = value || 'message'
    } else if (field === 'data') {
      dataLines.push(value)
    }
  }

  if (dataLines.length === 0) {
    return null
  }
  return { id, event, data: dataLines.join(NEXT_LINE) }
}
