import { describe, expect, it } from 'vitest'
import type { AgentMemoryFact } from '@/types/agent'
import {
  buildMemoryExport,
  confidenceLevel,
  filterMemoryRows,
  memoryExportFilename,
  mergeMemoryFacts,
} from './memoryScope'

function fact(overrides: Partial<AgentMemoryFact> = {}): AgentMemoryFact {
  return {
    id: '1',
    key: 'pet.name',
    label: '宠物名字',
    value: '豆豆',
    confidence: 0.9,
    update_time: '2026-11-17T08:00:00',
    ...overrides,
  }
}

describe('mergeMemoryFacts', () => {
  it('通用 + 两只宠物的事实合并后按置信度倒序', () => {
    const rows = mergeMemoryFacts([
      {
        scope: { petId: null, petName: '通用' },
        facts: [
          fact({
            id: '1',
            key: 'user.city',
            label: '城市',
            value: '杭州',
            confidence: 0.72,
            update_time: '2026-11-16T08:00:00',
          }),
        ],
      },
      {
        scope: { petId: '5001', petName: '豆豆' },
        facts: [
          fact({ id: '2', key: 'pet.name', confidence: 0.95 }),
          fact({
            id: '3',
            key: 'pet.allergy',
            label: '过敏',
            value: '牛奶',
            confidence: 0.8,
            update_time: '2026-11-17T09:00:00',
          }),
        ],
      },
      {
        scope: { petId: '5002', petName: '花花' },
        facts: [fact({ id: '4', key: 'pet.name', value: '花花', confidence: 0.88 })],
      },
    ])

    expect(rows.map(row => `${row.petName}:${row.key}`)).toEqual([
      '豆豆:pet.name',
      '花花:pet.name',
      '豆豆:pet.allergy',
      '通用:user.city',
    ])
    // 范围信息必须带在行上，删除时原样回传 pet_id
    expect(rows[0].petId).toBe('5001')
    expect(rows[3].petId).toBeNull()
  })

  it('同一范围同一 key 只留置信度更高的一条', () => {
    const rows = mergeMemoryFacts([
      {
        scope: { petId: '5001', petName: '豆豆' },
        facts: [fact({ value: '旧值', confidence: 0.6 }), fact({ value: '新值', confidence: 0.9 })],
      },
    ])

    expect(rows).toHaveLength(1)
    expect(rows[0].value).toBe('新值')
  })

  it('置信度相同按更新时间倒序，空时间排最后', () => {
    const rows = mergeMemoryFacts([
      {
        scope: { petId: null, petName: '通用' },
        facts: [
          fact({ key: 'a', confidence: 0.8, update_time: null }),
          fact({ key: 'b', confidence: 0.8, update_time: '2026-11-10T00:00:00' }),
          fact({ key: 'c', confidence: 0.8, update_time: '2026-11-17T00:00:00' }),
        ],
      },
    ])

    expect(rows.map(row => row.key)).toEqual(['c', 'b', 'a'])
  })
})

describe('filterMemoryRows', () => {
  const rows = mergeMemoryFacts([
    { scope: { petId: null, petName: '通用' }, facts: [fact({ key: 'user.city' })] },
    { scope: { petId: '5001', petName: '豆豆' }, facts: [fact({ key: 'pet.name' })] },
  ])

  it('all 返回全部，null 只返回通用，字符串只返回该宠物', () => {
    expect(filterMemoryRows(rows, 'all')).toHaveLength(2)
    expect(filterMemoryRows(rows, null).map(row => row.key)).toEqual(['user.city'])
    expect(filterMemoryRows(rows, '5001').map(row => row.key)).toEqual(['pet.name'])
    expect(filterMemoryRows(rows, '9999')).toEqual([])
  })
})

describe('confidenceLevel', () => {
  it('0.85 起算高，0.70 起算中，边界值不越档', () => {
    expect(confidenceLevel(0.85)).toBe('high')
    expect(confidenceLevel(0.849)).toBe('medium')
    expect(confidenceLevel(0.7)).toBe('medium')
    expect(confidenceLevel(0.699)).toBe('low')
  })
})

describe('buildMemoryExport / memoryExportFilename', () => {
  it('文件名带本机时间戳到分钟', () => {
    expect(memoryExportFilename(new Date(2026, 10, 17, 22, 5))).toBe(
      'petlumina-memory-20261117-2205.json',
    )
  })

  it('各范围的服务端导出原样装进 scopes，不改事实内容', () => {
    const now = new Date('2026-11-17T14:05:00.000Z')
    const file = buildMemoryExport(
      [
        {
          scope: { petId: null, petName: '通用' },
          payload: { version: 1, exported_at: '2026-11-17T14:00:00Z', pet_id: null, facts: [fact()] },
        },
        {
          scope: { petId: '5001', petName: '豆豆' },
          payload: {
            version: 1,
            exported_at: '2026-11-17T14:00:00Z',
            pet_id: '5001',
            facts: [],
          },
        },
      ],
      now,
    )

    expect(file).toEqual({
      version: 1,
      exported_at: '2026-11-17T14:05:00.000Z',
      scopes: [
        { pet_id: null, pet_name: '通用', facts: [fact()] },
        { pet_id: '5001', pet_name: '豆豆', facts: [] },
      ],
    })
  })
})
