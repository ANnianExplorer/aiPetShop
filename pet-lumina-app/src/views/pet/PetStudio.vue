<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'
import { buildSprite, SPRITE_DEFAULTS, type RgbaImage } from '@/utils/petImage'
import { clearSprite, loadSprite, saveSprite, type PetSprite } from '@/utils/petSpriteStore'

const router = useRouter()
const { t } = useI18n()
const { showToast } = useToast()

const sourceName = ref('')
const sourceSize = ref('')
const busy = ref(false)
const spriteUrl = ref('')
const spriteSize = ref({ width: 0, height: 0 })
const saved = ref<PetSprite | null>(loadSprite())
const hasSprite = computed(() => Boolean(saved.value?.dataUrl) || Boolean(spriteUrl.value))

const tolerance = ref<number>(SPRITE_DEFAULTS.tolerance)
const levels = ref<number>(SPRITE_DEFAULTS.levels)
const outline = ref<number>(SPRITE_DEFAULTS.outline)
const simplify = ref<number>(SPRITE_DEFAULTS.simplify)

/** 原图只解码一次：每次调参只重跑像素管线，不重新读文件 */
let original: RgbaImage | null = null
let originalCanvas: HTMLCanvasElement | null = null

const previewUrl = computed(() => spriteUrl.value || saved.value?.dataUrl || '')

function decodeFile(file: File): Promise<{ img: RgbaImage; url: string }> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file)
    const image = new Image()
    image.onload = () => {
      const canvas = document.createElement('canvas')
      // 先缩到 1024 以内再处理：手机拍的大图逐像素跑 4 遍会卡死主线程
      const ratio = Math.min(1, 1024 / Math.max(image.width, image.height))
      canvas.width = Math.max(1, Math.round(image.width * ratio))
      canvas.height = Math.max(1, Math.round(image.height * ratio))
      const ctx = canvas.getContext('2d', { willReadFrequently: true })
      if (!ctx) {
        URL.revokeObjectURL(url)
        reject(new Error('canvas-unavailable'))
        return
      }
      ctx.drawImage(image, 0, 0, canvas.width, canvas.height)
      const data = ctx.getImageData(0, 0, canvas.width, canvas.height)
      originalCanvas = canvas
      resolve({ img: { data: data.data, width: data.width, height: data.height }, url })
    }
    image.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('decode-failed'))
    }
    image.src = url
  })
}

function toDataUrl(img: RgbaImage): string {
  const canvas = originalCanvas ?? document.createElement('canvas')
  canvas.width = img.width
  canvas.height = img.height
  const ctx = canvas.getContext('2d')
  if (!ctx) return ''
  const imageData = ctx.createImageData(img.width, img.height)
  imageData.data.set(img.data)
  ctx.putImageData(imageData, 0, 0)
  return canvas.toDataURL('image/png')
}

function render(): void {
  if (!original) return
  // 每次都从原图数据出发，避免在已卡通化的结果上反复叠滤镜
  const out = buildSprite(original, {
    tolerance: tolerance.value,
    levels: levels.value,
    simplify: simplify.value,
    outline: outline.value,
    maxSide: SPRITE_DEFAULTS.maxSide,
    padding: SPRITE_DEFAULTS.padding,
  })
  if (out.width === 0) {
    spriteUrl.value = ''
    spriteSize.value = { width: 0, height: 0 }
    showToast(t('petStudio.emptyResult'), 'error')
    return
  }
  spriteUrl.value = toDataUrl(out)
  spriteSize.value = { width: out.width, height: out.height }
}

async function onFilePicked(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  busy.value = true
  sourceName.value = file.name
  sourceSize.value = `${Math.round(file.size / 1024)} KB`
  try {
    const { img, url } = await decodeFile(file)
    URL.revokeObjectURL(url)
    original = img
    render()
  } catch {
    showToast(t('petStudio.decodeFailed'), 'error')
  } finally {
    busy.value = false
  }
}

function save(): void {
  if (!spriteUrl.value) return
  const sprite: PetSprite = {
    dataUrl: spriteUrl.value,
    width: spriteSize.value.width,
    height: spriteSize.value.height,
    source: 'upload',
    createdAt: new Date().toISOString(),
  }
  const result = saveSprite(sprite)
  if (!result.ok) {
    showToast(result.reason === 'quota' ? t('petStudio.quota') : t('petStudio.saveFailed'), 'error')
    return
  }
  saved.value = sprite
  showToast(t('petStudio.saved'), 'success')
}

function restoreDefault(): void {
  clearSprite()
  saved.value = null
  showToast(t('petStudio.restored'), 'success')
}

function goHome(): void {
  router.push({ name: 'home' })
}

onBeforeUnmount(() => {
  original = null
  originalCanvas = null
})
</script>

<template>
  <div class="min-h-screen bg-background pb-24">
    <header class="sticky top-0 z-20 bg-background/90 backdrop-blur-md px-5 pt-4 pb-3 flex items-center gap-3">
      <button
        class="w-10 h-10 rounded-full hover:bg-surface-container flex items-center justify-center"
        :aria-label="t('common.back')"
        @click="goHome"
      >
        <span class="material-symbols-outlined text-on-surface">arrow_back</span>
      </button>
      <div class="flex-1">
        <h1 class="font-headline-md text-[20px] text-on-surface">{{ t('petStudio.title') }}</h1>
        <p class="text-[12px] text-on-surface-variant">{{ t('petStudio.subtitle') }}</p>
      </div>
    </header>

    <main class="px-5 space-y-5">
      <section class="glass-card p-5 space-y-4">
        <p class="text-[13px] text-on-surface-variant leading-relaxed">{{ t('petStudio.intro') }}</p>
        <label
          class="flex items-center justify-center gap-2 w-full h-12 rounded-full bg-primary text-on-primary font-title-sm text-title-sm shadow-lg shadow-primary/25 active:scale-[0.98] transition-transform cursor-pointer"
        >
          <span class="material-symbols-outlined">add_photo_alternate</span>
          <span>{{ busy ? t('petStudio.processing') : t('petStudio.choose') }}</span>
          <input type="file" accept="image/*" class="hidden" :disabled="busy" @change="onFilePicked" />
        </label>
        <p v-if="sourceName" class="text-[12px] text-on-surface-variant">
          {{ sourceName }} · {{ sourceSize }}
        </p>
      </section>

      <section v-if="hasSprite" class="glass-card p-5 space-y-4">
        <h2 class="font-title-sm text-title-sm text-on-surface">{{ t('petStudio.preview') }}</h2>
        <div class="flex items-center justify-center h-44 rounded-2xl bg-surface-container-low overflow-hidden">
          <div class="pet-stage">
            <img :src="previewUrl" :alt="t('petStudio.preview')" class="pet-sprite" />
            <span class="pet-shadow" />
          </div>
        </div>
        <p class="text-[12px] text-on-surface-variant text-center">
          {{ t('petStudio.size', { w: spriteSize.width || saved?.width, h: spriteSize.height || saved?.height }) }}
        </p>
        <button
          class="w-full h-11 rounded-full bg-primary text-on-primary font-title-sm text-title-sm disabled:opacity-50"
          :disabled="!spriteUrl"
          @click="save"
        >
          {{ t('petStudio.useThis') }}
        </button>
      </section>

      <section class="glass-card p-5 space-y-5">
        <h2 class="font-title-sm text-title-sm text-on-surface">{{ t('petStudio.tuning') }}</h2>

        <label class="block space-y-2">
          <span class="flex justify-between text-[13px] text-on-surface">
            <span>{{ t('petStudio.tolerance') }}</span><span class="text-on-surface-variant">{{ tolerance }}</span>
          </span>
          <input v-model.number="tolerance" type="range" min="0" max="120" step="4" class="w-full" @change="render" />
          <span class="block text-[11px] text-on-surface-variant">{{ t('petStudio.toleranceHint') }}</span>
        </label>

        <label class="block space-y-2">
          <span class="flex justify-between text-[13px] text-on-surface">
            <span>{{ t('petStudio.levels') }}</span><span class="text-on-surface-variant">{{ levels }}</span>
          </span>
          <input v-model.number="levels" type="range" min="2" max="12" step="1" class="w-full" @change="render" />
        </label>

        <label class="block space-y-2">
          <span class="flex justify-between text-[13px] text-on-surface">
            <span>{{ t('petStudio.outline') }}</span><span class="text-on-surface-variant">{{ outline.toFixed(2) }}</span>
          </span>
          <input v-model.number="outline" type="range" min="0" max="1" step="0.1" class="w-full" @change="render" />
        </label>

        <button
          v-if="saved"
          class="w-full h-11 rounded-full border border-outline-variant text-on-surface-variant text-[13px]"
          @click="restoreDefault"
        >
          {{ t('petStudio.restore') }}
        </button>
      </section>

      <p class="text-[11px] text-on-surface-variant leading-relaxed px-2">
        {{ t('petStudio.privacy') }}
      </p>
    </main>
  </div>
</template>

<style scoped>
.pet-stage {
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  height: 150px;
  width: 160px;
}

.pet-sprite {
  max-height: 140px;
  max-width: 140px;
  animation: sprite-breathe 3.8s ease-in-out infinite;
  transform-origin: 50% 100%;
  filter: drop-shadow(0 6px 10px rgba(0, 0, 0, 0.12));
}

.pet-shadow {
  position: absolute;
  bottom: -2px;
  width: 74px;
  height: 12px;
  border-radius: 50%;
  background: radial-gradient(closest-side, rgba(0, 0, 0, 0.22), transparent);
  animation: sprite-shadow 3.8s ease-in-out infinite;
}

@keyframes sprite-breathe {
  0%, 100% { transform: scale(1, 1) rotate(-1.2deg); }
  50% { transform: scale(1.02, 0.985) rotate(1.2deg); }
}

@keyframes sprite-shadow {
  0%, 100% { transform: scaleX(1); opacity: 0.85; }
  50% { transform: scaleX(0.9); opacity: 0.6; }
}

@media (prefers-reduced-motion: reduce) {
  .pet-sprite,
  .pet-shadow {
    animation: none;
  }
}
</style>
