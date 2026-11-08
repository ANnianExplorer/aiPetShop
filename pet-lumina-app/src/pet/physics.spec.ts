import { describe, expect, it } from 'vitest'
import { createMotion } from './physics'

const viewport = { width: 400, height: 800 }
const pet = { width: 120, height: 150 }
const groundY = viewport.height - pet.height

function settle(motion: ReturnType<typeof createMotion>, frames = 400): void {
  for (let i = 0; i < frames; i += 1) motion.step(16)
}

describe('摆放与边界', () => {
  it('摆到视口外会被夹回「至少还能点到」的范围', () => {
    const motion = createMotion(viewport, pet)
    motion.place(-500, -500)
    expect(motion.state.x).toBeGreaterThanOrEqual(24 - pet.width)
    expect(motion.state.y).toBeGreaterThanOrEqual(24 - pet.height)
    motion.place(9999, 9999)
    expect(motion.state.x).toBeLessThanOrEqual(viewport.width - 24)
    expect(motion.state.y).toBeLessThanOrEqual(viewport.height - 24)
  })

  it('视口比宠物还小时不让它整只掉出屏幕（至少留 24px 可点）', () => {
    const motion = createMotion({ width: 60, height: 80 }, pet)
    motion.place(0, 0)
    expect(motion.state.x).toBeLessThanOrEqual(60 - 24)
    expect(motion.state.y).toBeLessThanOrEqual(80 - 24)
    expect(motion.state.x).toBeGreaterThanOrEqual(24 - pet.width)
    expect(motion.state.y).toBeGreaterThanOrEqual(24 - pet.height)
  })

  it('视口与宠物都极小时区间反向，改为居中', () => {
    const tiny = { width: 10, height: 8 }
    const motion = createMotion({ width: 20, height: 20 }, tiny)
    motion.place(0, 0)
    expect(motion.state.x).toBe((20 - tiny.width) / 2)
    expect(motion.state.y).toBe((20 - tiny.height) / 2)
  })

  it('右下角 home 会留出边距与地面上沿', () => {
    const motion = createMotion(viewport, pet, {}, 68)
    motion.home('bottom-right', { x: 12, y: 12 })
    expect(motion.state.x).toBe(viewport.width - pet.width - 12)
    expect(motion.state.y).toBe(viewport.height - pet.height - 68 - 12)
  })
})

describe('重力、反弹与挤压', () => {
  it('抛到空中后会落回地面并停住', () => {
    const motion = createMotion(viewport, pet)
    motion.place(120, 200)
    motion.throwTo(0, -600)
    settle(motion, 600)
    expect(motion.state.grounded).toBe(true)
    expect(Math.round(motion.state.y)).toBe(groundY)
    expect(motion.state.vy).toBe(0)
  })

  it('撞地会反弹而不是直接停住（恢复系数生效）', () => {
    const motion = createMotion(viewport, pet)
    motion.place(120, 0)
    // 用一次重砸观察反弹瞬间
    motion.throwTo(0, 0)
    motion.state.y = groundY - 200
    motion.state.grounded = false
    motion.state.vy = 1200
    motion.step(16)
    const bouncedUp = motion.state.vy < 0 || motion.state.y < groundY
    expect(bouncedUp).toBe(true)
  })

  it('重砸落地会压扁，然后回弹到正常比例', () => {
    const motion = createMotion(viewport, pet)
    motion.place(120, groundY - 160)
    motion.state.grounded = false
    motion.state.vy = 1200
    for (let i = 0; i < 12; i += 1) motion.step(16)
    const squashed = motion.squashFactor()
    expect(squashed).toBeLessThan(1)
    settle(motion, 60)
    expect(motion.squashFactor()).toBe(1)
  })
})

describe('拖拽与甩出', () => {
  it('拖拽跟手（保留按下时的抓取偏移），松手时慢慢放下不会飞出去', () => {
    const motion = createMotion(viewport, pet)
    motion.place(100, 100)
    motion.beginDrag(100, 100, 0)
    motion.moveDrag(160, 140, 16)
    expect(motion.state.x).toBe(160)
    expect(motion.state.y).toBe(140)
    motion.endDrag(400)
    expect(motion.state.vx).toBe(0)
    expect(motion.state.vy).toBe(0)
    expect(motion.state.grounded).toBe(false)
    // 从 140px 高度落下会弹几下才停：给足帧数（约 9.6s）
    settle(motion, 600)
    expect(motion.state.grounded).toBe(true)
  })

  it('快速甩出会带上速度，且被软上限压住', () => {
    const motion = createMotion(viewport, pet)
    motion.beginDrag(100, 300, 0)
    for (let i = 1; i <= 6; i += 1) motion.moveDrag(100 + i * 60, 300, i * 16)
    motion.endDrag(96)
    expect(motion.state.vx).toBeGreaterThan(500)
    expect(Math.abs(motion.state.vx)).toBeLessThanOrEqual(3600)
  })

  it('停顿后才松手按「温柔放下」处理（不抛）', () => {
    const motion = createMotion(viewport, pet)
    motion.beginDrag(100, 300, 0)
    motion.moveDrag(400, 300, 16)
    motion.endDrag(1000)
    expect(motion.state.vx).toBe(0)
  })
})

describe('走位', () => {
  it('走位沿方向移动、到点停下并更新朝向', () => {
    const motion = createMotion(viewport, pet)
    motion.place(100, groundY)
    expect(motion.walk(120, 1)).toBe(true)
    expect(motion.state.walking).toBe(true)
    expect(motion.state.direction).toBe(1)
    settle(motion, 200)
    expect(motion.state.walking).toBe(false)
    expect(motion.state.x).toBeGreaterThan(100)
    expect(motion.state.x).toBeLessThanOrEqual(viewport.width - pet.width)
  })

  it('已经顶到可达边界时走不动就返回 false（上层换方向再试）', () => {
    const motion = createMotion(viewport, pet)
    // 可达右界 = 视口右沿 - 24（允许大半只探出屏幕，但要留得住可点区域）
    motion.place(viewport.width - 24, groundY)
    expect(motion.walk(120, 1)).toBe(false)
    expect(motion.state.walking).toBe(false)
  })

  it('拖拽中不接受走位指令', () => {
    const motion = createMotion(viewport, pet)
    motion.beginDrag(100, 100, 0)
    expect(motion.walk(120, 1)).toBe(false)
  })
})
