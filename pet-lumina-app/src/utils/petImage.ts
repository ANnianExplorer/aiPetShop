/**
 * 图片 → 桌宠精灵图：全部是纯函数，只吃 `{ data, width, height }`，
 * 不碰 DOM canvas —— 这样 jsdom 里也能测（真实解码/编码在 PetStudio.vue 里做）。
 */

export interface RgbaImage {
  /** 长度必须是 width * height * 4，RGBA，非预乘 */
  data: Uint8ClampedArray
  width: number
  height: number
}

export interface Rect {
  x: number
  y: number
  width: number
  height: number
}

export interface CartoonOptions {
  /** 每个通道量化成几阶（2–12），越小越"卡通" */
  levels?: number
  /** 0 = 原图，1 = 完全量化 */
  simplify?: number
  /** 饱和度倍数，1 为不变 */
  saturation?: number
}

export interface SpriteOptions extends CartoonOptions {
  /** 背景色距离容差（0–255），越大抠得越狠 */
  tolerance?: number
  /** 描边强度 0–1，0 表示不描边 */
  outline?: number
  /** 长边上限像素 */
  maxSide?: number
  /** 裁边时保留的透明边距 */
  padding?: number
}

export const SPRITE_DEFAULTS = {
  tolerance: 32,
  levels: 6,
  simplify: 0.85,
  saturation: 1.12,
  outline: 0.6,
  maxSide: 512,
  padding: 8,
}

const clamp255 = (v: number): number => (v < 0 ? 0 : v > 255 ? 255 : v)

export function createImage(width: number, height: number, rgba: [number, number, number, number] = [0, 0, 0, 0]): RgbaImage {
  const data = new Uint8ClampedArray(width * height * 4)
  for (let i = 0; i < data.length; i += 4) {
    data[i] = rgba[0]
    data[i + 1] = rgba[1]
    data[i + 2] = rgba[2]
    data[i + 3] = rgba[3]
  }
  return { data, width, height }
}

function colorDistance(r1: number, g1: number, b1: number, r2: number, g2: number, b2: number): number {
  // 欧氏距离再按 sqrt(3) 归一，量纲仍落在 0–255
  return Math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) / Math.sqrt(3)
}

/**
 * 从四角取背景色，再做**边缘连通**的 flood fill：
 * 画面内部与背景同色的区域（比如白色衣服）不会被误删——这是"只删外面"的关键。
 */
export function removeBackground(img: RgbaImage, tolerance = SPRITE_DEFAULTS.tolerance): RgbaImage {
  const { data, width, height } = img
  const out = new Uint8ClampedArray(data)
  if (width === 0 || height === 0) return { data: out, width, height }

  const corners = [
    0,
    (width - 1) * 4,
    (width * (height - 1)) * 4,
    (width * height - 1) * 4,
  ]
  // 用四角均值当背景色，比只用左上角稳（渐变背景也不至于一刀切）
  let br = 0
  let bg = 0
  let bb = 0
  for (const c of corners) {
    br += data[c]
    bg += data[c + 1]
    bb += data[c + 2]
  }
  br /= corners.length
  bg /= corners.length
  bb /= corners.length

  const visited = new Uint8Array(width * height)
  const stack: number[] = []
  const push = (x: number, y: number) => {
    const p = y * width + x
    if (visited[p]) return
    visited[p] = 1
    stack.push(p)
  }
  for (let x = 0; x < width; x++) {
    push(x, 0)
    push(x, height - 1)
  }
  for (let y = 0; y < height; y++) {
    push(0, y)
    push(width - 1, y)
  }

  while (stack.length > 0) {
    const p = stack.pop() as number
    const i = p * 4
    const dist = colorDistance(data[i], data[i + 1], data[i + 2], br, bg, bb)
    if (dist > tolerance) continue // 不是背景：不继续扩散，也不擦除
    out[i + 3] = 0
    const x = p % width
    const y = (p - x) / width
    if (x > 0) push(x - 1, y)
    if (x + 1 < width) push(x + 1, y)
    if (y > 0) push(x, y - 1)
    if (y + 1 < height) push(x, y + 1)
  }
  return { data: out, width, height }
}

/** 按 alpha 求实体包围盒；全透明返回 null */
export function alphaBounds(img: RgbaImage, alphaThreshold = 8): Rect | null {
  const { data, width, height } = img
  let minX = width
  let minY = height
  let maxX = -1
  let maxY = -1
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      if (data[(y * width + x) * 4 + 3] > alphaThreshold) {
        if (x < minX) minX = x
        if (x > maxX) maxX = x
        if (y < minY) minY = y
        if (y > maxY) maxY = y
      }
    }
  }
  if (maxX < 0 || maxY < 0) return null
  return { x: minX, y: minY, width: maxX - minX + 1, height: maxY - minY + 1 }
}

/** 裁切（越界自动夹紧；padding 用透明补齐） */
export function cropImage(img: RgbaImage, rect: Rect, padding = 0): RgbaImage {
  const x0 = Math.max(0, Math.floor(rect.x) - padding)
  const y0 = Math.max(0, Math.floor(rect.y) - padding)
  const x1 = Math.min(img.width, Math.ceil(rect.x + rect.width) + padding)
  const y1 = Math.min(img.height, Math.ceil(rect.y + rect.height) + padding)
  const w = Math.max(1, x1 - x0)
  const h = Math.max(1, y1 - y0)
  const out = new Uint8ClampedArray(w * h * 4)
  for (let y = 0; y < h; y++) {
    const srcY = y0 + y
    if (srcY < 0 || srcY >= img.height) continue
    for (let x = 0; x < w; x++) {
      const srcX = x0 + x
      if (srcX < 0 || srcX >= img.width) continue
      const si = (srcY * img.width + srcX) * 4
      const di = (y * w + x) * 4
      out[di] = img.data[si]
      out[di + 1] = img.data[si + 1]
      out[di + 2] = img.data[si + 2]
      out[di + 3] = img.data[si + 3]
    }
  }
  return { data: out, width: w, height: h }
}

function boxBlur(img: RgbaImage, radius: number): RgbaImage {
  if (radius <= 0) return { data: new Uint8ClampedArray(img.data), width: img.width, height: img.height }
  const { data, width, height } = img
  const out = new Uint8ClampedArray(data.length)
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      let r = 0
      let g = 0
      let b = 0
      let a = 0
      let n = 0
      for (let dy = -radius; dy <= radius; dy++) {
        const yy = y + dy
        if (yy < 0 || yy >= height) continue
        for (let dx = -radius; dx <= radius; dx++) {
          const xx = x + dx
          if (xx < 0 || xx >= width) continue
          const i = (yy * width + xx) * 4
          r += data[i]
          g += data[i + 1]
          b += data[i + 2]
          a += data[i + 3]
          n++
        }
      }
      const di = (y * width + x) * 4
      out[di] = r / n
      out[di + 1] = g / n
      out[di + 2] = b / n
      out[di + 3] = a / n
    }
  }
  return { data: out, width, height }
}

const quantize = (v: number, levels: number): number => {
  const step = 255 / (levels - 1)
  return Math.round(Math.round(v / step) * step)
}

function adjustSaturation(r: number, g: number, b: number, factor: number): [number, number, number] {
  const luma = 0.299 * r + 0.587 * g + 0.114 * b
  return [clamp255(luma + (r - luma) * factor), clamp255(luma + (g - luma) * factor), clamp255(luma + (b - luma) * factor)]
}

/** 保边平滑 + 色阶量化 + 饱和度：先把噪点抹掉，再压成色块 */
export function cartoonify(img: RgbaImage, options: CartoonOptions = {}): RgbaImage {
  const levels = Math.max(2, Math.min(12, Math.round(options.levels ?? SPRITE_DEFAULTS.levels)))
  const simplify = Math.max(0, Math.min(1, options.simplify ?? SPRITE_DEFAULTS.simplify))
  const saturation = Math.max(0, options.saturation ?? SPRITE_DEFAULTS.saturation)
  const blurred = boxBlur(img, 1)
  const out = new Uint8ClampedArray(img.data.length)
  for (let i = 0; i < out.length; i += 4) {
    if (img.data[i + 3] === 0) {
      out[i + 3] = 0
      continue
    }
    const [r, g, b] = adjustSaturation(blurred.data[i], blurred.data[i + 1], blurred.data[i + 2], saturation)
    out[i] = clamp255(img.data[i] + (quantize(r, levels) - img.data[i]) * simplify)
    out[i + 1] = clamp255(img.data[i + 1] + (quantize(g, levels) - img.data[i + 1]) * simplify)
    out[i + 2] = clamp255(img.data[i + 2] + (quantize(b, levels) - img.data[i + 2]) * simplify)
    out[i + 3] = img.data[i + 3]
  }
  return { data: out, width: img.width, height: img.height }
}

/** Sobel 勾边后压暗；只作用在实体像素上 */
export function outlineImage(img: RgbaImage, strength = SPRITE_DEFAULTS.outline, threshold = 56): RgbaImage {
  if (strength <= 0) return { data: new Uint8ClampedArray(img.data), width: img.width, height: img.height }
  const { data, width, height } = img
  const out = new Uint8ClampedArray(data)
  const gray = (i: number): number => 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]
  for (let y = 1; y < height - 1; y++) {
    for (let x = 1; x < width - 1; x++) {
      const idx = (y * width + x) * 4
      if (data[idx + 3] === 0) continue
      const gx =
        -gray(((y - 1) * width + (x - 1)) * 4) -
        2 * gray((y * width + (x - 1)) * 4) -
        gray(((y + 1) * width + (x - 1)) * 4) +
        gray(((y - 1) * width + (x + 1)) * 4) +
        2 * gray((y * width + (x + 1)) * 4) +
        gray(((y + 1) * width + (x + 1)) * 4)
      const gy =
        -gray(((y - 1) * width + (x - 1)) * 4) -
        2 * gray(((y - 1) * width + x) * 4) -
        gray(((y - 1) * width + (x + 1)) * 4) +
        gray(((y + 1) * width + (x - 1)) * 4) +
        2 * gray(((y + 1) * width + x) * 4) +
        gray(((y + 1) * width + (x + 1)) * 4)
      const mag = Math.sqrt(gx * gx + gy * gy)
      if (mag < threshold) continue
      const k = 1 - strength * Math.min(1, mag / 256)
      out[idx] = clamp255(data[idx] * k)
      out[idx + 1] = clamp255(data[idx + 1] * k)
      out[idx + 2] = clamp255(data[idx + 2] * k)
    }
  }
  return { data: out, width, height }
}

/** 面积平均缩放（只缩不放；放大交给 CSS） */
export function scaleDown(img: RgbaImage, maxSide: number): RgbaImage {
  const longest = Math.max(img.width, img.height)
  if (longest <= maxSide || longest === 0) return img
  const ratio = maxSide / longest
  const w = Math.max(1, Math.round(img.width * ratio))
  const h = Math.max(1, Math.round(img.height * ratio))
  const out = new Uint8ClampedArray(w * h * 4)
  const sx = img.width / w
  const sy = img.height / h
  for (let y = 0; y < h; y++) {
    const y0 = Math.floor(y * sy)
    const y1 = Math.max(y0 + 1, Math.floor((y + 1) * sy))
    for (let x = 0; x < w; x++) {
      const x0 = Math.floor(x * sx)
      const x1 = Math.max(x0 + 1, Math.floor((x + 1) * sx))
      let r = 0
      let g = 0
      let b = 0
      let a = 0
      let n = 0
      for (let yy = y0; yy < Math.min(y1, img.height); yy++) {
        for (let xx = x0; xx < Math.min(x1, img.width); xx++) {
          const i = (yy * img.width + xx) * 4
          r += img.data[i]
          g += img.data[i + 1]
          b += img.data[i + 2]
          a += img.data[i + 3]
          n++
        }
      }
      const di = (y * w + x) * 4
      out[di] = r / n
      out[di + 1] = g / n
      out[di + 2] = b / n
      out[di + 3] = a / n
    }
  }
  return { data: out, width: w, height: h }
}

/** 完整管线：抠背景 → 裁边 → 卡通化 → 描边 → 缩放 */
export function buildSprite(img: RgbaImage, options: SpriteOptions = {}): RgbaImage {
  const padding = options.padding ?? SPRITE_DEFAULTS.padding
  const cut = removeBackground(img, options.tolerance ?? SPRITE_DEFAULTS.tolerance)
  const bounds = alphaBounds(cut)
  if (!bounds) return { data: new Uint8ClampedArray(0), width: 0, height: 0 }
  const cropped = cropImage(cut, bounds, padding)
  const cartoon = cartoonify(cropped, options)
  const outlined = outlineImage(cartoon, options.outline ?? SPRITE_DEFAULTS.outline)
  return scaleDown(outlined, options.maxSide ?? SPRITE_DEFAULTS.maxSide)
}
