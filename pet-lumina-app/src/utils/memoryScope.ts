/**
 * 「我的记忆」的纯函数：合并多范围事实、过滤、置信度分档、导出文件拼装。
 *
 * 为什么要多范围合并：后端 `GET /agent/memory/me` 的 `pet_id` 为空表示
 * 「不带宠物维度」的事实，**不是**该用户全部事实。想看全部只能按范围各拉一次，
 * 这里负责去重、排序和拼导出文件，UI 不写业务规则。
 */

import type { AgentMemoryExport, AgentMemoryFact } from '@/types/agent'

/** 一个查询范围；`petId=null` 表示通用（无宠物维度） */
export interface MemoryScope {
  petId: string | null
  petName: string
}

export interface MemoryScopeFacts {
  scope: MemoryScope
  facts: AgentMemoryFact[]
}

/** 列表行：事实 + 它所属的范围，删除时要用 petId */
export interface MemoryRow extends AgentMemoryFact {
  petId: string | null
  petName: string
}

export type MemoryConfidence = 'high' | 'medium' | 'low'

/** 范围筛选：'all' 表示全部，null 表示通用，其余是宠物 id */
export type MemoryScopeFilter = string | null

export interface MemoryExportScope {
  pet_id: string | null
  pet_name: string
  facts: AgentMemoryFact[]
}

/** 下载文件形状：服务端单范围导出原样放进 scopes，App 端只做聚合 */
export interface MemoryExportFile {
  version: 1
  exported_at: string
  scopes: MemoryExportScope[]
}

const HIGH_CONFIDENCE = 0.85
const MEDIUM_CONFIDENCE = 0.7

export function confidenceLevel(confidence: number): MemoryConfidence {
  if (confidence >= HIGH_CONFIDENCE) return 'high'
  if (confidence >= MEDIUM_CONFIDENCE) return 'medium'
  return 'low'
}

/** 稳定排序：置信度 DESC → 更新时间 DESC（空值最后）→ key ASC */
function compareRows(a: MemoryRow, b: MemoryRow): number {
  if (a.confidence !== b.confidence) return b.confidence - a.confidence
  const aTime = a.update_time ?? ''
  const bTime = b.update_time ?? ''
  if (aTime !== bTime) return aTime < bTime ? 1 : -1
  if (a.key === b.key) return 0
  return a.key < b.key ? -1 : 1
}

/**
 * 合并多个范围的事实。
 *
 * 去重键是 `(petId, key)`：服务端同一范围理论上不会重复，客户端兜底只留置信度更高的一条；
 * 不同范围同 key（例如都叫 `pet.name`）是两件不同的事，都要保留。
 */
export function mergeMemoryFacts(results: MemoryScopeFacts[]): MemoryRow[] {
  const merged = new Map<string, MemoryRow>()
  for (const { scope, facts } of results) {
    for (const fact of facts) {
      const row: MemoryRow = { ...fact, petId: scope.petId, petName: scope.petName }
      const dedupeKey = `${scope.petId ?? 'general'}\u0000${fact.key}`
      const existing = merged.get(dedupeKey)
      if (!existing || row.confidence > existing.confidence) {
        merged.set(dedupeKey, row)
      }
    }
  }
  return [...merged.values()].sort(compareRows)
}

export function filterMemoryRows(rows: MemoryRow[], filter: MemoryScopeFilter): MemoryRow[] {
  if (filter === 'all') return rows
  return rows.filter(row => row.petId === filter)
}

function pad(value: number): string {
  return String(value).padStart(2, '0')
}

/** `petlumina-memory-20261117-2220.json`（本机时区，便于用户对时间） */
export function memoryExportFilename(now: Date): string {
  const date = `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}`
  const time = `${pad(now.getHours())}${pad(now.getMinutes())}`
  return `petlumina-memory-${date}-${time}.json`
}

/**
 * 把各范围的服务端导出拼成一个文件。
 *
 * 已知偏差：这不是服务端单一文件的逐字节结果，是客户端聚合；
 * 事实内容仍来自服务端 export 接口（limit=200），`pet_name` 只为可读性。
 */
export function buildMemoryExport(
  results: { scope: MemoryScope; payload: AgentMemoryExport }[],
  now: Date,
): MemoryExportFile {
  return {
    version: 1,
    exported_at: now.toISOString(),
    scopes: results.map(({ scope, payload }) => ({
      pet_id: scope.petId,
      pet_name: scope.petName,
      facts: payload.facts ?? [],
    })),
  }
}
