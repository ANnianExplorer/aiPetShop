import type { AgentCitation } from '@/types/agent'

/**
 * 引用 → App 内路由。
 *
 * 后端在 `locator` 里直接给相对路由（`/log/7001`、`/post/9001`、
 * `/weekly-health-detail?petId=5001&date=2026-11-09`），前端只判断「能不能跳」，
 * 不再按 kind 硬编码——新增一种引用来源不用改前端。
 *
 * 老数据（S1.25 之前落库的引用）没有路由形态的 `locator`，按 kind 兜底；
 * 兜不住就返回 `null`，由界面显示 label，而不是假装能跳、点出一片空白。
 */
const LEGACY_BY_KIND: Readonly<Record<string, (id: string) => string>> = {
  log: (id) => `/log/${id}`,
  post: (id) => `/post/${id}`,
  pet: (id) => `/pet-detail/${id}`,
}

export function citationRoute(
  citation: Pick<AgentCitation, 'kind' | 'id' | 'locator'>
): string | null {
  const locator = (citation.locator ?? '').trim()
  if (locator.startsWith('/')) return locator
  const fallback = LEGACY_BY_KIND[citation.kind]
  if (!fallback || !citation.id) return null
  return fallback(citation.id)
}
