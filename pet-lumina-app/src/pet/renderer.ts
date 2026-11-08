/**
 * canvas 渲染：把一帧姿态画出来。
 *
 * 为什么不用 DOM/SVG：桌宠要「随手一甩就飞出去、落地还能 Q 弹」，整图每帧都要
 * 变形；canvas 一次 drawImage 就能带上缩放、旋转、镜像与挤压，SVG 那边
 * 每帧改 attr 会走一遍样式重算，反而更贵。
 *
 * 只画宠物盒内部：位置由外层容器的 transform 决定（与参考实现一致——
 * 视频/画布只负责「长什么样」，位移不参与布局重排）。
 */
import type { Pose, Prop } from './types'

/** 影子占盒高的比例（贴底）。 */
const SHADOW_PAD = 0.04

/** 渲染器。 */
export interface Renderer {
  resize(width: number, height: number): void
  draw(image: CanvasImageSource | null, pose: Pose): void
}

/** 造一个渲染器；拿不到 2D 上下文时返回空实现，让上层逻辑在 jsdom 里也能跑。 */
export function createRenderer(canvas: HTMLCanvasElement, dpr = 2): Renderer {
  const ctx = canvas.getContext('2d')
  let width = 0
  let height = 0
  let ratio = dpr

  const resize = (nextWidth: number, nextHeight: number): void => {
    width = nextWidth
    height = nextHeight
    ratio = Math.max(1, Math.min(3, dpr))
    canvas.width = Math.round(width * ratio)
    canvas.height = Math.round(height * ratio)
    canvas.style.width = `${width}px`
    canvas.style.height = `${height}px`
  }

  const draw = (image: CanvasImageSource | null, pose: Pose): void => {
    if (!ctx || width === 0 || height === 0) return
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
    ctx.clearRect(0, 0, width, height)

    drawShadow(ctx, width, height, pose)
    if (image !== null) drawSprite(ctx, image, width, height, pose)
    for (const prop of pose.props) drawProp(ctx, width, height, prop)
  }

  return { resize, draw }
}

/** 贴地椭圆影子；跳起时变小变淡。 */
function drawShadow(ctx: CanvasRenderingContext2D, width: number, height: number, pose: Pose): void {
  const rx = width * 0.3 * Math.max(0.2, pose.shadow)
  ctx.save()
  ctx.globalAlpha = Math.max(0.08, 0.32 * pose.shadow)
  ctx.fillStyle = '#2c3a32'
  ctx.beginPath()
  ctx.ellipse(width / 2 + pose.offsetX * width, height - 2, rx, Math.max(2, height * 0.016), 0, 0, Math.PI * 2)
  ctx.fill()
  ctx.restore()
}

/** 画宠物本体：等比装进盒内、贴底居中，再套姿态变换。 */
function drawSprite(
  ctx: CanvasRenderingContext2D,
  image: CanvasImageSource,
  width: number,
  height: number,
  pose: Pose,
): void {
  const source = image as CanvasImageSource & { width?: number; height?: number; naturalWidth?: number; naturalHeight?: number }
  const rawW = Number(source.naturalWidth ?? source.width ?? 0)
  const rawH = Number(source.naturalHeight ?? source.height ?? 0)
  if (rawW <= 0 || rawH <= 0) return
  const availableH = height * (1 - SHADOW_PAD)
  const scale = Math.min(width / rawW, availableH / rawH)
  const drawW = rawW * scale
  const drawH = rawH * scale

  ctx.save()
  ctx.globalAlpha = pose.alpha
  // 以脚底中心为原点：变形（缩放/挤压）围绕脚下，看起来才是「站在地上」
  ctx.translate(width / 2 + pose.offsetX * width, height - 2 + pose.offsetY * height)
  ctx.rotate((pose.rotate * Math.PI) / 180)
  ctx.scale(pose.scaleX * (pose.mirror ? -1 : 1), pose.scaleY)
  ctx.drawImage(image, -drawW / 2, -drawH, drawW, drawH)
  ctx.restore()
}

/** 归一化坐标 → 画布坐标。 */
function at(width: number, height: number, prop: Prop): { x: number; y: number } {
  return { x: prop.x * width, y: prop.y * height }
}

/** 画一个道具；坐标是盒内的相对位置。 */
function drawProp(ctx: CanvasRenderingContext2D, width: number, height: number, prop: Prop): void {
  const { x, y } = at(width, height, prop)
  const scale = prop.scale ?? 1
  const size = Math.min(width, height) * 0.09 * scale
  if (size <= 0.5) return
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(((prop.rotate ?? 0) * Math.PI) / 180)
  ctx.globalAlpha = prop.alpha ?? 1
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  switch (prop.kind) {
    case 'heart':
      drawHeart(ctx, size)
      break
    case 'anger':
      drawAnger(ctx, size)
      break
    case 'exclaim':
      drawExclaim(ctx, size)
      break
    case 'question':
      drawQuestion(ctx, size)
      break
    case 'dots':
      drawDots(ctx, size)
      break
    case 'zzz':
      drawZzz(ctx, size)
      break
    case 'sweat':
      drawSweat(ctx, size)
      break
    case 'star':
      drawStar(ctx, size)
      break
    case 'note':
      drawNote(ctx, size)
      break
    case 'onigiri':
      drawOnigiri(ctx, size)
      break
    case 'token':
      drawToken(ctx, size)
      break
    case 'gear':
      drawGear(ctx, size)
      break
    case 'sparkle':
      drawSparkle(ctx, size)
      break
    default:
      break
  }
  ctx.restore()
}

function drawHeart(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#ef8fa4'
  ctx.beginPath()
  ctx.moveTo(0, size * 0.9)
  ctx.bezierCurveTo(-size * 1.2, size * 0.05, -size * 0.6, -size * 0.95, 0, -size * 0.35)
  ctx.bezierCurveTo(size * 0.6, -size * 0.95, size * 1.2, size * 0.05, 0, size * 0.9)
  ctx.fill()
}

function drawAnger(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.strokeStyle = '#e2574c'
  ctx.lineWidth = Math.max(1.5, size * 0.22)
  const arm = size * 0.75
  for (let i = 0; i < 4; i += 1) {
    const angle = (Math.PI / 2) * i + Math.PI / 4
    ctx.beginPath()
    ctx.moveTo(Math.cos(angle) * size * 0.28, Math.sin(angle) * size * 0.28)
    ctx.lineTo(Math.cos(angle) * arm, Math.sin(angle) * arm)
    ctx.stroke()
  }
}

function drawExclaim(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#f0a13c'
  // roundRect 在部分旧 WebView 上没有；没有就退回直角矩形，形状差一点不影响可读性
  ctx.beginPath()
  if (typeof ctx.roundRect === 'function') {
    ctx.roundRect(-size * 0.22, -size * 0.95, size * 0.44, size * 1.35, size * 0.22)
  } else {
    ctx.rect(-size * 0.22, -size * 0.95, size * 0.44, size * 1.35)
  }
  ctx.fill()
  ctx.beginPath()
  ctx.arc(0, size * 0.78, size * 0.24, 0, Math.PI * 2)
  ctx.fill()
}

function drawQuestion(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.strokeStyle = '#7b8f83'
  ctx.lineWidth = Math.max(2, size * 0.26)
  ctx.beginPath()
  ctx.arc(0, -size * 0.35, size * 0.55, Math.PI * 0.95, Math.PI * 2.15)
  ctx.lineTo(0, size * 0.25)
  ctx.stroke()
  ctx.fillStyle = '#7b8f83'
  ctx.beginPath()
  ctx.arc(0, size * 0.75, size * 0.2, 0, Math.PI * 2)
  ctx.fill()
}

function drawDots(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#9aa9a0'
  for (let i = 0; i < 1; i += 1) {
    ctx.beginPath()
    ctx.arc(0, 0, size * 0.34, 0, Math.PI * 2)
    ctx.fill()
  }
}

function drawZzz(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.strokeStyle = '#7b9f8b'
  ctx.lineWidth = Math.max(1.4, size * 0.18)
  ctx.lineJoin = 'miter'
  for (let i = 0; i < 3; i += 1) {
    const scale = size * (0.5 + i * 0.25)
    const dy = -i * size * 0.55
    ctx.beginPath()
    ctx.moveTo(-scale * 0.45, dy - scale * 0.45)
    ctx.lineTo(scale * 0.45, dy - scale * 0.45)
    ctx.lineTo(-scale * 0.45, dy + scale * 0.45)
    ctx.lineTo(scale * 0.45, dy + scale * 0.45)
    ctx.stroke()
  }
}

function drawSweat(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#8ec4e0'
  ctx.beginPath()
  ctx.moveTo(0, -size * 0.9)
  ctx.bezierCurveTo(size * 0.65, -size * 0.1, size * 0.5, size * 0.75, 0, size * 0.75)
  ctx.bezierCurveTo(-size * 0.5, size * 0.75, -size * 0.65, -size * 0.1, 0, -size * 0.9)
  ctx.fill()
}

function drawStar(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#f3c96b'
  ctx.beginPath()
  for (let i = 0; i < 10; i += 1) {
    const radius = i % 2 === 0 ? size : size * 0.45
    const angle = (Math.PI / 5) * i - Math.PI / 2
    const px = Math.cos(angle) * radius
    const py = Math.sin(angle) * radius
    if (i === 0) ctx.moveTo(px, py)
    else ctx.lineTo(px, py)
  }
  ctx.closePath()
  ctx.fill()
}

function drawNote(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#7fb9a1'
  ctx.beginPath()
  ctx.ellipse(-size * 0.35, size * 0.55, size * 0.42, size * 0.3, -0.4, 0, Math.PI * 2)
  ctx.fill()
  ctx.strokeStyle = '#7fb9a1'
  ctx.lineWidth = Math.max(1.4, size * 0.18)
  ctx.beginPath()
  ctx.moveTo(size * 0.02, size * 0.42)
  ctx.lineTo(size * 0.02, -size * 0.8)
  ctx.quadraticCurveTo(size * 0.6, -size * 0.7, size * 0.5, -size * 0.25)
  ctx.stroke()
}

function drawOnigiri(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#fbf7ee'
  ctx.strokeStyle = '#dfd4c0'
  ctx.lineWidth = Math.max(1, size * 0.1)
  ctx.beginPath()
  ctx.moveTo(0, -size)
  ctx.lineTo(size * 0.95, size * 0.75)
  ctx.lineTo(-size * 0.95, size * 0.75)
  ctx.closePath()
  ctx.fill()
  ctx.stroke()
  ctx.fillStyle = '#3f5b4d'
  ctx.fillRect(-size * 0.35, size * 0.18, size * 0.7, size * 0.55)
}

function drawToken(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#e9c76a'
  ctx.beginPath()
  ctx.arc(0, 0, size * 0.9, 0, Math.PI * 2)
  ctx.fill()
  ctx.strokeStyle = '#c9a348'
  ctx.lineWidth = Math.max(1, size * 0.12)
  ctx.beginPath()
  ctx.arc(0, 0, size * 0.62, 0, Math.PI * 2)
  ctx.stroke()
  ctx.fillStyle = '#c9a348'
  ctx.font = `bold ${Math.max(6, size * 0.9)}px sans-serif`
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('T', 0, size * 0.06)
}

function drawGear(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.fillStyle = '#93a89b'
  const teeth = 6
  ctx.beginPath()
  for (let i = 0; i < teeth * 2; i += 1) {
    const radius = i % 2 === 0 ? size * 0.9 : size * 0.62
    const angle = (Math.PI / teeth) * i
    const px = Math.cos(angle) * radius
    const py = Math.sin(angle) * radius
    if (i === 0) ctx.moveTo(px, py)
    else ctx.lineTo(px, py)
  }
  ctx.closePath()
  ctx.fill()
  ctx.fillStyle = '#f7f3ea'
  ctx.beginPath()
  ctx.arc(0, 0, size * 0.3, 0, Math.PI * 2)
  ctx.fill()
}

function drawSparkle(ctx: CanvasRenderingContext2D, size: number): void {
  ctx.strokeStyle = '#f3c96b'
  ctx.lineWidth = Math.max(1.4, size * 0.16)
  const arm = size * 0.85
  for (let i = 0; i < 4; i += 1) {
    const angle = (Math.PI / 2) * i
    ctx.beginPath()
    ctx.moveTo(Math.cos(angle) * arm * 0.35, Math.sin(angle) * arm * 0.35)
    ctx.lineTo(Math.cos(angle) * arm, Math.sin(angle) * arm)
    ctx.stroke()
  }
}
