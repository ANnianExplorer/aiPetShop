import { describe, expect, it } from 'vitest'
import { isToday, isWithinNextDays, parseRemindTime } from './schedule'

// 固定"现在"：2026-11-07 14:00 本地时间，测试不受机器时区/时钟影响
const NOW = new Date(2026, 10, 7, 14, 0, 0)

describe('parseRemindTime', () => {
  it('解析后端格式 yyyy-MM-dd HH:mm:ss', () => {
    const parsed = parseRemindTime('2026-11-07 09:30:00')
    expect(parsed?.getFullYear()).toBe(2026)
    expect(parsed?.getMonth()).toBe(10)
    expect(parsed?.getDate()).toBe(7)
    expect(parsed?.getHours()).toBe(9)
    expect(parsed?.getMinutes()).toBe(30)
  })

  it('兼容 ISO 与毫秒', () => {
    expect(parseRemindTime('2026-11-07T09:30:00')?.getHours()).toBe(9)
    expect(parseRemindTime('2026-11-07T09:30:00.250')?.getMinutes()).toBe(30)
  })

  it('空值与垃圾值返回 null，不抛异常', () => {
    expect(parseRemindTime('')).toBeNull()
    expect(parseRemindTime(null)).toBeNull()
    expect(parseRemindTime(undefined)).toBeNull()
    expect(parseRemindTime('明天早上')).toBeNull()
  })
})

describe('isToday', () => {
  it('同一天的不同时刻都算今天', () => {
    expect(isToday('2026-11-07 00:00:01', NOW)).toBe(true)
    expect(isToday('2026-11-07 23:59:59', NOW)).toBe(true)
  })

  it('昨天/明天不算今天（跨天边界）', () => {
    expect(isToday('2026-11-06 23:59:59', NOW)).toBe(false)
    expect(isToday('2026-11-08 00:00:00', NOW)).toBe(false)
  })

  it('旧的 includes("今天") 写法在真实数据上永远为假', () => {
    expect('2026-11-07 09:30:00'.includes('今天')).toBe(false)
    expect(isToday('2026-11-07 09:30:00', NOW)).toBe(true)
  })

  it('无法解析的时间不算今天', () => {
    expect(isToday('明天', NOW)).toBe(false)
  })
})

describe('isWithinNextDays', () => {
  it('左闭右开：今天算，第 7 天 00:00 不算', () => {
    expect(isWithinNextDays('2026-11-07 00:00:00', 7, NOW)).toBe(true)
    expect(isWithinNextDays('2026-11-13 23:59:59', 7, NOW)).toBe(true)
    expect(isWithinNextDays('2026-11-14 00:00:00', 7, NOW)).toBe(false)
  })

  it('过去的时间不算未来一周', () => {
    expect(isWithinNextDays('2026-11-06 10:00:00', 7, NOW)).toBe(false)
  })
})
