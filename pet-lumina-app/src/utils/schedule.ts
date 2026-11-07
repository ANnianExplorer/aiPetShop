/**
 * 提醒筛选的日期工具。
 *
 * 原来的"今日提醒"用 `remindTime.includes('今天')` 判断，但后端存的是
 * `yyyy-MM-dd HH:mm:ss`，永远不含"今天"二字 —— 于是今日列表长期为空。
 * 这里只做两件事：解析成时间戳（兼容 `yyyy-MM-dd HH:mm:ss` 与 ISO），
 * 以及按"本地自然日"比较；不引入 dayjs 之类的依赖，逻辑简单到能被单测钉死。
 */

/** 宽松解析：`2026-11-07 09:00:00`、`2026-11-07T09:00:00`、带毫秒/时区都能读 */
export function parseRemindTime(value: string | null | undefined): Date | null {
  if (!value) return null
  const text = value.trim()
  if (!text) return null
  // 空格分隔的本地时间在部分引擎里解析不稳定，统一成 ISO 风格
  const normalized = text.includes('T') ? text : text.replace(' ', 'T')
  const parsed = new Date(normalized)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

export function isSameLocalDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

export function isToday(value: string | null | undefined, now: Date = new Date()): boolean {
  const parsed = parseRemindTime(value)
  return parsed !== null && isSameLocalDay(parsed, now)
}

/** [今天 00:00, 今天+days 00:00) 左闭右开，避免"第 7 天"被算进来 */
export function isWithinNextDays(
  value: string | null | undefined,
  days: number,
  now: Date = new Date()
): boolean {
  const parsed = parseRemindTime(value)
  if (parsed === null) return false
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const end = new Date(start.getTime())
  end.setDate(end.getDate() + days)
  return parsed >= start && parsed < end
}
