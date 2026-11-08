import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createDeskPetEngine, type DeskPetEngine } from './engine'
import { CATALOG } from './catalog'
import { CLIPS } from './clips'

/** jsdom 没有 canvas 实现：给引擎一个「拿得到 2D 上下文以外一切」的假画布。 */
function fakeCanvas(): HTMLCanvasElement {
  return {
    width: 0,
    height: 0,
    style: {} as CSSStyleDeclaration,
    getContext: () => null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    setPointerCapture: () => undefined,
  } as unknown as HTMLCanvasElement
}

function makeEngine(): { engine: DeskPetEngine; root: HTMLElement } {
  const root = document.createElement('div')
  const engine = createDeskPetEngine({ canvas: fakeCanvas(), root, size: 120, dpr: 1 })
  return { engine, root }
}

/** 推进到片段播完（片段最长 3.8s，按 16ms 步进）。 */
function playOut(engine: DeskPetEngine, ms = 4200): void {
  for (let t = 0; t < ms; t += 16) engine.advance(16)
}

beforeEach(() => {
  // 引擎的随机链吃 Math.random：固定成 0.99 让它稳定落在分类动作档
  vi.spyOn(Math, 'random').mockReturnValue(0.99)
})

describe('片段调度', () => {
  it('起步是待机呼吸，且能按帧推进', () => {
    const { engine } = makeEngine()
    expect(engine.runtime.clip).toBe('idle.breath')
    engine.advance(100)
    expect(engine.runtime.elapsed).toBeGreaterThan(0)
  })

  it('待机片段播完后换成目录里的另一段，而不是停在同一条', () => {
    const { engine } = makeEngine()
    playOut(engine)
    const allowed = new Set([...CATALOG.idle, ...CATALOG.turn, ...CATALOG.categories.flatMap((c) => c.actions)])
    expect(allowed.has(engine.runtime.clip)).toBe(true)
  })

  it('点一下会播点击回应，播完回到随机链', () => {
    const { engine } = makeEngine()
    engine.tap()
    expect(CATALOG.clicks).toContain(engine.runtime.clip)
    playOut(engine)
    expect(CATALOG.clicks).not.toContain(engine.runtime.clip)
  })

  it('工作状态接管动画，终态播完自动回到空闲', () => {
    const { engine } = makeEngine()
    engine.setWorkState('working')
    expect(engine.runtime.workState).toBe('working')
    expect(engine.runtime.clip).toBe('work.working')
    expect(engine.runtime.repeat).toBe(true)

    engine.setWorkState('success')
    expect(engine.runtime.clip).toBe('work.success')
    playOut(engine)
    expect(engine.runtime.workState).toBeNull()
    expect(engine.runtime.clip).not.toBe('work.success')
  })

  it('工作状态下点击只会插播互动，播完回到工作档位（不会被待机顶掉）', () => {
    const { engine } = makeEngine()
    engine.setWorkState('thinking')
    engine.tap()
    expect(CATALOG.clicks).toContain(engine.runtime.clip)
    playOut(engine)
    expect(engine.runtime.clip).toBe('work.thinking')
    expect(engine.runtime.workState).toBe('thinking')
  })
})

describe('睡觉', () => {
  it('入睡走 start → loop，叫醒走 end 后回到随机链', () => {
    const { engine } = makeEngine()
    engine.sleep()
    expect(engine.runtime.sleeping).toBe('start')
    expect(engine.runtime.clip).toBe('sleep.start')
    playOut(engine, 2000)
    expect(engine.runtime.sleeping).toBe('loop')
    expect(engine.runtime.clip).toBe('sleep.loop')

    engine.wake()
    expect(engine.runtime.sleeping).toBe('end')
    playOut(engine, 2000)
    expect(engine.runtime.sleeping).toBeNull()
  })

  it('睡着时点一下先叫醒，不播点击回应', () => {
    const { engine } = makeEngine()
    engine.sleep()
    playOut(engine, 2000)
    engine.tap()
    expect(engine.runtime.sleeping).toBe('end')
  })

  it('睡着时工作状态不打断睡觉，醒来后补上', () => {
    const { engine } = makeEngine()
    engine.sleep()
    playOut(engine, 2000)
    engine.setWorkState('working')
    expect(engine.runtime.clip).toBe('sleep.loop')
    engine.wake()
    playOut(engine, 2000)
    expect(engine.runtime.clip).toBe('work.working')
  })
})

describe('拖拽与位置', () => {
  it('拖拽计入状态，单击不会当成拖拽', () => {
    const { engine, root } = makeEngine()
    engine.beginDrag(100, 300, 0)
    engine.moveDrag(102, 302, 16)
    engine.endDrag(16)
    engine.advance(16)
    expect(engine.runtime.dragging).toBe(false)
    expect(root.style.transform).toContain('translate3d')

    const taps: number[] = []
    const tapped = createDeskPetEngine({
      canvas: fakeCanvas(),
      size: 120,
      dpr: 1,
      onTap: () => taps.push(1),
    })
    tapped.beginDrag(100, 300, 0)
    tapped.endDrag(16)
    expect(taps).toHaveLength(1)
  })

  it('拖到很远算拖拽而不是点击', () => {
    const taps: number[] = []
    const engine = createDeskPetEngine({
      canvas: fakeCanvas(),
      size: 120,
      dpr: 1,
      onTap: () => taps.push(1),
    })
    engine.beginDrag(100, 300, 0)
    engine.moveDrag(220, 320, 16)
    engine.endDrag(20)
    expect(taps).toHaveLength(0)
  })

  it('home 会把宠物摆到右下角', () => {
    const { engine } = makeEngine()
    engine.home('bottom-right', { x: 10, y: 10 })
    expect(engine.motion.state.x).toBe(window.innerWidth - 120 - 10)
  })
})

describe('点播与边界', () => {
  it('点播目录里的动作成功，未知片段返回 false 且不改当前片段', () => {
    const { engine } = makeEngine()
    expect(engine.playAction('act.eat')).toBe(true)
    expect(engine.runtime.clip).toBe('act.eat')
    expect(engine.playAction('nope.nope')).toBe(false)
    expect(engine.runtime.clip).toBe('act.eat')
  })

  it('null 形象不崩、可以重复 stop/start', () => {
    const { engine } = makeEngine()
    expect(() => engine.setSprite(null)).not.toThrow()
    engine.start()
    engine.stop()
    engine.stop()
  })

  it('每一段目录片段都能被播出来', () => {
    const { engine } = makeEngine()
    for (const id of Object.keys(CLIPS)) {
      expect(engine.playAction(id)).toBe(true)
      engine.advance(16)
    }
  })
})
