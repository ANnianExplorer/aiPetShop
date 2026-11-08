import { describe, expect, it } from 'vitest'
import {
  alphaBounds,
  buildSprite,
  cartoonify,
  createImage,
  cropImage,
  outlineImage,
  removeBackground,
  scaleDown,
  type RgbaImage,
} from './petImage'

function px(img: RgbaImage, x: number, y: number): [number, number, number, number] {
  const i = (y * img.width + x) * 4
  return [img.data[i], img.data[i + 1], img.data[i + 2], img.data[i + 3]]
}

function setPx(img: RgbaImage, x: number, y: number, rgba: [number, number, number, number]): void {
  const i = (y * img.width + x) * 4
  img.data[i] = rgba[0]
  img.data[i + 1] = rgba[1]
  img.data[i + 2] = rgba[2]
  img.data[i + 3] = rgba[3]
}

/** 白底 + 中间一块红色方块 */
function whiteWithSquare(size = 10): RgbaImage {
  const img = createImage(size, size, [255, 255, 255, 255])
  for (let y = 2; y < size - 2; y++) {
    for (let x = 2; x < size - 2; x++) setPx(img, x, y, [220, 20, 60, 255])
  }
  return img
}

describe('removeBackground', () => {
  it('把白底抠成透明，保留中间的方块', () => {
    const out = removeBackground(whiteWithSquare(), 32)
    expect(px(out, 0, 0)[3]).toBe(0)
    expect(px(out, out.width - 1, out.height - 1)[3]).toBe(0)
    expect(px(out, 4, 4)[3]).toBe(255)
    expect(px(out, 4, 4).slice(0, 3)).toEqual([220, 20, 60])
  })

  it('只删与边缘连通的部分（内部同色不误删）', () => {
    const img = createImage(9, 9, [255, 255, 255, 255])
    // 外圈白、里面一圈红、正中心一块白：中心白不与边缘连通，必须保留
    for (let y = 1; y < 8; y++) for (let x = 1; x < 8; x++) setPx(img, x, y, [220, 20, 60, 255])
    setPx(img, 4, 4, [255, 255, 255, 255])

    const out = removeBackground(img, 32)
    expect(px(out, 0, 0)[3]).toBe(0) // 外圈被删
    expect(px(out, 1, 1)[3]).toBe(255) // 红圈还在
    expect(px(out, 4, 4)[3]).toBe(255) // 内部白点还在（关键）
  })

  it('容差为 0 时几乎不删（背景色轻微不同就保留）', () => {
    const img = createImage(4, 4, [250, 250, 250, 255])
    setPx(img, 0, 0, [255, 255, 255, 255])
    const out = removeBackground(img, 0)
    // 阈值 0 只允许完全同色，四角均值 251 与 255 有差距 → 不删
    expect(px(out, 0, 0)[3]).toBe(255)
  })

  it('空图不崩', () => {
    const out = removeBackground({ data: new Uint8ClampedArray(0), width: 0, height: 0 }, 32)
    expect(out.data.length).toBe(0)
  })
})

describe('alphaBounds / cropImage', () => {
  it('包围盒紧贴实体像素', () => {
    const img = removeBackground(whiteWithSquare(10), 32)
    const rect = alphaBounds(img)
    expect(rect).toEqual({ x: 2, y: 2, width: 6, height: 6 })
  })

  it('全透明返回 null', () => {
    expect(alphaBounds(createImage(4, 4, [0, 0, 0, 0]))).toBeNull()
  })

  it('裁切带透明 padding，且不越界', () => {
    const img = removeBackground(whiteWithSquare(10), 32)
    const rect = alphaBounds(img)!
    const cropped = cropImage(img, rect, 2)
    expect(cropped.width).toBe(10)
    expect(cropped.height).toBe(10)
    const edge = cropImage(img, { x: 0, y: 0, width: 10, height: 10 }, 5)
    expect(edge.width).toBe(10) // 夹紧到原图尺寸
  })
})

describe('cartoonify', () => {
  it('量化到 6 阶后颜色数变少且仍不透明', () => {
    const img = createImage(8, 8, [0, 0, 0, 255])
    for (let x = 0; x < 8; x++) setPx(img, x, 0, [x * 30, 100, 150, 255])
    const out = cartoonify(img, { levels: 6, simplify: 1, saturation: 1 })
    const values = new Set<number>()
    for (let x = 0; x < 8; x++) values.add(px(out, x, 0)[0])
    expect(values.size).toBeLessThanOrEqual(6)
    expect(px(out, 3, 3)[3]).toBe(255)
  })

  it('simplify=0 时保持原色（只做平滑）', () => {
    const img = createImage(3, 3, [10, 20, 30, 255])
    const out = cartoonify(img, { levels: 4, simplify: 0, saturation: 1 })
    expect(px(out, 1, 1)).toEqual([10, 20, 30, 255])
  })

  it('透明像素保持透明', () => {
    const img = createImage(2, 2, [0, 0, 0, 0])
    const out = cartoonify(img, {})
    expect(px(out, 0, 0)[3]).toBe(0)
  })
})

describe('outlineImage', () => {
  it('strength=0 原样返回', () => {
    const img = whiteWithSquare()
    expect(outlineImage(img, 0).data).toEqual(img.data)
  })

  it('在明暗交界处压暗（描边）', () => {
    const img = createImage(5, 5, [255, 255, 255, 255])
    for (let y = 0; y < 5; y++) for (let x = 2; x < 5; x++) setPx(img, x, y, [10, 10, 10, 255])
    const out = outlineImage(img, 0.8, 40)
    const boundaryDarkened = px(out, 1, 2)[0] < 255 || px(out, 2, 2)[0] < 10
    expect(boundaryDarkened).toBe(true)
  })
})

describe('scaleDown', () => {
  it('长边超限时按比例缩小', () => {
    const img = createImage(100, 50, [1, 2, 3, 255])
    const out = scaleDown(img, 40)
    expect(out.width).toBe(40)
    expect(out.height).toBe(20)
    expect(px(out, 0, 0)).toEqual([1, 2, 3, 255])
  })

  it('不超限时原样返回（同一引用）', () => {
    const img = createImage(10, 10, [1, 2, 3, 255])
    expect(scaleDown(img, 512)).toBe(img)
  })
})

describe('buildSprite', () => {
  it('端到端：白底方块 → 透明底精灵图', () => {
    const out = buildSprite(whiteWithSquare(40), { tolerance: 32, levels: 6, maxSide: 64, padding: 2 })
    expect(out.width).toBeGreaterThan(0)
    expect(out.width).toBeLessThanOrEqual(64)
    expect(px(out, 0, 0)[3]).toBe(0)
    const center = Math.floor(out.width / 2)
    expect(px(out, center, center)[3]).toBe(255)
  })

  it('全透明输入返回 0 尺寸（调用方据此报错）', () => {
    const out = buildSprite(createImage(8, 8, [0, 0, 0, 0]))
    expect(out.width).toBe(0)
    expect(out.height).toBe(0)
  })
})
