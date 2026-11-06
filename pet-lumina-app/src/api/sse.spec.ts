import { describe, expect, it } from 'vitest'
import { SseDecoder } from './sse'

const decoder = () => new SseDecoder()

describe('SseDecoder', () => {
  it('把单条完整记录解析成 event/data/id', () => {
    const sse = decoder()
    const messages = sse.push('id: 3\nevent: delta\ndata: {"text":"你好"}\n\n')
    expect(messages).toEqual([{ id: 3, event: 'delta', data: '{"text":"你好"}' }])
  })

  it('一条记录跨多个 chunk 也能拼起来', () => {
    const sse = decoder()
    expect(sse.push('id: 1\nevent: del')).toEqual([])
    expect(sse.push('ta\ndata: {"text":"a"}\n\n')).toEqual([
      { id: 1, event: 'delta', data: '{"text":"a"}' },
    ])
  })

  it('多行 data 用换行拼接（SSE 规范）', () => {
    const sse = decoder()
    const [message] = sse.push('event: note\ndata: line1\ndata: line2\n\n')
    expect(message.data).toBe('line1\nline2')
  })

  it('忽略注释行与未知字段', () => {
    const sse = decoder()
    const [message] = sse.push(': keep-alive\nretry: 3000\nevent: ping\ndata: pong\n\n')
    expect(message).toEqual({ id: undefined, event: 'ping', data: 'pong' })
  })

  it('CRLF 换行等价于 LF', () => {
    const sse = decoder()
    const messages = sse.push('id: 9\r\nevent: done\r\ndata: {}\r\n\r\n')
    expect(messages).toEqual([{ id: 9, event: 'done', data: '{}' }])
  })

  it('一次 chunk 里的多条记录按顺序返回', () => {
    const sse = decoder()
    const messages = sse.push('event: a\ndata: 1\n\nevent: b\ndata: 2\n\n')
    expect(messages.map((m) => m.event)).toEqual(['a', 'b'])
  })

  it('缺失 event 时默认 message', () => {
    const sse = decoder()
    const [message] = sse.push('data: hi\n\n')
    expect(message.event).toBe('message')
  })

  it('flush 能吐出没有结尾空行的最后一条记录', () => {
    const sse = decoder()
    expect(sse.push('event: done\ndata: {"answer":"ok"}')).toEqual([])
    expect(sse.flush()).toEqual([{ id: undefined, event: 'done', data: '{"answer":"ok"}' }])
  })

  it('非数字 id 不转 number（避免 NaN 破坏续传游标）', () => {
    const sse = decoder()
    const [message] = sse.push('id: abc\nevent: x\ndata: 1\n\n')
    expect(message.id).toBeUndefined()
  })

  it('空行之间没有字段时忽略该记录', () => {
    const sse = decoder()
    expect(sse.push('\n\nevent: x\ndata: 1\n\n')).toEqual([
      { id: undefined, event: 'x', data: '1' },
    ])
  })
})
