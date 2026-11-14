import { describe, expect, it } from 'vitest'
import { citationRoute } from './citationRoute'

describe('citationRoute', () => {
  it('后端给了路由就用它，健康引用带着日期一起带走', () => {
    expect(
      citationRoute({
        kind: 'health',
        id: '5001',
        locator: '/weekly-health-detail?petId=5001&date=2026-11-09',
      })
    ).toBe('/weekly-health-detail?petId=5001&date=2026-11-09')
  })

  it('帖子与记录引用跳详情页', () => {
    expect(citationRoute({ kind: 'post', id: '9001', locator: '/post/9001' })).toBe('/post/9001')
    expect(citationRoute({ kind: 'log', id: '7001', locator: '/log/7001' })).toBe('/log/7001')
  })

  it('老数据没有 locator：按 kind 兜底，不让旧会话失效', () => {
    expect(citationRoute({ kind: 'log', id: '7001' })).toBe('/log/7001')
    expect(citationRoute({ kind: 'post', id: '9001' })).toBe('/post/9001')
    expect(citationRoute({ kind: 'pet', id: '5001' })).toBe('/pet-detail/5001')
  })

  it('老的「给人看的」locator 不算路由，仍然走兜底或不可点', () => {
    expect(citationRoute({ kind: 'pet', id: '5001', locator: '宠物档案' })).toBe('/pet-detail/5001')
    expect(citationRoute({ kind: 'health', id: '5001', locator: 'petId=5001' })).toBeNull()
  })

  it('未知 kind 且没有路由时不可点，交给界面显示 label', () => {
    expect(citationRoute({ kind: 'doc', id: 'doc-1' })).toBeNull()
    expect(citationRoute({ kind: 'log', id: '', locator: '' })).toBeNull()
  })
})
