<script setup lang="ts">
/**
 * Q 版角色本体（纯展示）。
 *
 * 分成 7 个可动部件（tail / body / arms / head / hair / ears / eyes），
 * 每个部件用自己的关键帧与相位，避免"整块一起动"的塑料感；
 * 视线与头部倾斜由父级传入的 gaze 驱动（CSS 变量），组件本身不监听事件。
 */
import { computed } from 'vue'
import type { PetMood } from '@/utils/petMood'

const props = withDefaults(
  defineProps<{
    mood?: PetMood
    gazeX?: number
    gazeY?: number
    sleeping?: boolean
    reducedMotion?: boolean
  }>(),
  { mood: 'idle', gazeX: 0, gazeY: 0, sleeping: false, reducedMotion: false },
)

const rootStyle = computed(() => ({
  '--gaze-x': `${props.gazeX}px`,
  '--gaze-y': `${props.gazeY}px`,
  '--tilt': `${(props.gazeX / 3) * 3}deg`,
}))
</script>

<template>
  <svg
    class="chibi"
    :class="[`mood-${mood}`, { sleeping, 'reduced-motion': reducedMotion }]"
    :style="rootStyle"
    viewBox="0 0 200 240"
    role="img"
    aria-hidden="true"
  >
    <ellipse class="shadow" cx="100" cy="232" rx="46" ry="7.5" />

    <!-- 尾巴：从身体右后方伸出，钟摆式摆动 -->
    <g data-part="tail" class="tail">
      <path
        d="M136 198 C168 198 186 176 180 154"
        fill="none"
        stroke="url(#tailGradient)"
        stroke-width="15"
        stroke-linecap="round"
      />
      <circle cx="180" cy="153" r="7.5" fill="#F7D9DE" />
    </g>

    <!-- 身体：呼吸 -->
    <g data-part="body" class="body">
      <path
        class="dress"
        d="M100 132 C78 132 66 152 62 178 L58 206 Q58 214 68 214 H132 Q142 214 142 206 L138 178 C134 152 122 132 100 132 Z"
        fill="#FBF7EE"
        stroke="#E6DECB"
        stroke-width="2"
      />
      <path d="M86 134 Q100 148 114 134" fill="none" stroke="#CFE3D6" stroke-width="3" />
      <circle cx="100" cy="150" r="4" fill="#8CBF9F" />
      <ellipse cx="86" cy="217" rx="9" ry="5.5" fill="#F3E7D8" />
      <ellipse cx="114" cy="217" rx="9" ry="5.5" fill="#F3E7D8" />
    </g>

    <!-- 手臂：左右不同相位，避免同步抖动 -->
    <g data-part="arms" class="arms">
      <rect class="arm arm-l" x="58" y="150" width="14" height="36" rx="7" fill="#FBF7EE" stroke="#E6DECB" stroke-width="2" />
      <rect class="arm arm-r" x="128" y="150" width="14" height="36" rx="7" fill="#FBF7EE" stroke="#E6DECB" stroke-width="2" />
    </g>

    <!-- 头部：后发 + 耳朵 + 脸 + 眼 + 刘海 + 侧发 -->
    <g data-part="head" class="head">
      <ellipse cx="100" cy="88" rx="63" ry="60" fill="#6FAE93" />
      <ellipse cx="100" cy="96" rx="60" ry="56" fill="#7BBA9D" opacity="0.55" />

      <g data-part="ears" class="ears">
        <path d="M56 48 L40 12 L86 32 Z" fill="#6FAE93" stroke="#5C9A81" stroke-width="2" stroke-linejoin="round" />
        <path d="M57 44 L47 20 L78 33 Z" fill="#F7C2CE" />
        <path d="M144 48 L160 12 L114 32 Z" fill="#6FAE93" stroke="#5C9A81" stroke-width="2" stroke-linejoin="round" />
        <path d="M143 44 L153 20 L122 33 Z" fill="#F7C2CE" />
      </g>

      <ellipse cx="100" cy="94" rx="51" ry="47" fill="#FFE9DC" />

      <g data-part="eyes" class="eyes">
        <g class="eye eye-l">
          <ellipse cx="78" cy="98" rx="15" ry="17" fill="#FFFFFF" stroke="#D8C7BB" stroke-width="1.5" />
          <g class="pupil">
            <circle cx="78" cy="99" r="11" fill="#2E8B7C" />
            <circle cx="78" cy="100" r="5.5" fill="#123B36" />
            <circle cx="74.5" cy="94" r="4" fill="#FFFFFF" opacity="0.95" />
            <circle cx="82" cy="104" r="1.8" fill="#FFFFFF" opacity="0.8" />
          </g>
          <rect class="lid" x="62" y="79" width="32" height="40" rx="10" fill="#FFE9DC" />
          <path d="M66 84 Q78 80 90 84" fill="none" stroke="#B98F7E" stroke-width="2.2" stroke-linecap="round" />
        </g>
        <g class="eye eye-r">
          <ellipse cx="122" cy="98" rx="15" ry="17" fill="#FFFFFF" stroke="#D8C7BB" stroke-width="1.5" />
          <g class="pupil">
            <circle cx="122" cy="99" r="11" fill="#2E8B7C" />
            <circle cx="122" cy="100" r="5.5" fill="#123B36" />
            <circle cx="118.5" cy="94" r="4" fill="#FFFFFF" opacity="0.95" />
            <circle cx="126" cy="104" r="1.8" fill="#FFFFFF" opacity="0.8" />
          </g>
          <rect class="lid" x="106" y="79" width="32" height="40" rx="10" fill="#FFE9DC" />
          <path d="M110 84 Q122 80 134 84" fill="none" stroke="#B98F7E" stroke-width="2.2" stroke-linecap="round" />
        </g>
      </g>

      <path class="mouth" d="M94 118 Q100 124 106 118" fill="none" stroke="#C98B7E" stroke-width="2.4" stroke-linecap="round" />
      <ellipse class="cheek cheek-l" cx="62" cy="112" rx="9" ry="5" fill="#F7B6B0" opacity="0.5" />
      <ellipse class="cheek cheek-r" cx="138" cy="112" rx="9" ry="5" fill="#F7B6B0" opacity="0.5" />

      <path
        class="bangs"
        d="M49 74 Q100 22 151 74 Q142 56 122 50 Q101 62 79 51 Q59 57 49 74 Z"
        fill="#6FAE93"
        stroke="#5C9A81"
        stroke-width="2"
        stroke-linejoin="round"
      />

      <g data-part="hair" class="hair">
        <path
          class="strand strand-l"
          d="M52 78 C44 106 44 134 52 156 C58 140 60 112 62 90 Z"
          fill="#6FAE93"
        />
        <path
          class="strand strand-r"
          d="M148 78 C156 106 156 134 148 156 C142 140 140 112 138 90 Z"
          fill="#6FAE93"
        />
      </g>

      <g class="zzz" aria-hidden="true">
        <text x="150" y="52" font-size="15" fill="#7BBA9D">z</text>
        <text x="160" y="38" font-size="19" fill="#6FAE93">z</text>
        <text x="172" y="22" font-size="23" fill="#5C9A81">z</text>
      </g>
    </g>

    <defs>
      <linearGradient id="tailGradient" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#7BBA9D" />
        <stop offset="100%" stop-color="#6FAE93" />
      </linearGradient>
    </defs>
  </svg>
</template>

<style scoped>
.chibi {
  width: 100%;
  height: 100%;
  overflow: visible;
  filter: drop-shadow(0 6px 10px rgba(47, 79, 68, 0.16));
}

/* —— 呼吸 / 悬浮 —— */
.body {
  transform-box: fill-box;
  transform-origin: 50% 100%;
  animation: pet-breathe 3.6s ease-in-out infinite;
}
@keyframes pet-breathe {
  0%, 100% { transform: scale(1, 1); }
  50% { transform: scale(1.008, 1.018); }
}

.head {
  transform-box: fill-box;
  transform-origin: 50% 94%;
  transform: rotate(var(--tilt, 0deg));
  animation: pet-bob 3.6s ease-in-out infinite;
}
@keyframes pet-bob {
  0%, 100% { transform: rotate(var(--tilt, 0deg)) translateY(0); }
  50% { transform: rotate(var(--tilt, 0deg)) translateY(-1.6px); }
}

/* —— 尾巴：钟摆 —— */
.tail {
  transform-box: fill-box;
  transform-origin: 4% 88%;
  animation: pet-wag 3.2s ease-in-out infinite alternate;
}
@keyframes pet-wag {
  from { transform: rotate(-7deg); }
  to { transform: rotate(8deg); }
}

/* —— 手臂：轻微不同步 —— */
.arm-l { animation: pet-arm-l 4.4s ease-in-out infinite; transform-box: fill-box; transform-origin: 50% 4%; }
.arm-r { animation: pet-arm-r 5.1s ease-in-out infinite; transform-box: fill-box; transform-origin: 50% 4%; }
@keyframes pet-arm-l { 0%, 100% { transform: rotate(0deg); } 50% { transform: rotate(-2.5deg); } }
@keyframes pet-arm-r { 0%, 100% { transform: rotate(0deg); } 50% { transform: rotate(2.5deg); } }

/* —— 耳朵：偶发抖动 —— */
.ears {
  transform-box: fill-box;
  transform-origin: 50% 100%;
  animation: pet-ear-twitch 7.3s ease-in-out infinite;
}
@keyframes pet-ear-twitch {
  0%, 86%, 100% { transform: rotate(0deg); }
  88% { transform: rotate(-3deg); }
  91% { transform: rotate(2.4deg); }
  94% { transform: rotate(0deg); }
}

/* —— 发丝：滞后摆动（"软"的来源）—— */
.strand {
  transform-box: fill-box;
  transform-origin: 50% 0%;
}
.strand-l { animation: pet-strand-l 4.2s ease-in-out infinite alternate; animation-delay: 0.35s; }
.strand-r { animation: pet-strand-r 4.8s ease-in-out infinite alternate; animation-delay: 0.6s; }
@keyframes pet-strand-l { from { transform: rotate(-2.6deg); } to { transform: rotate(1.8deg); } }
@keyframes pet-strand-r { from { transform: rotate(2.6deg); } to { transform: rotate(-1.8deg); } }

/* —— 眼睛：眨眼 + 视线 —— */
.pupil {
  transform: translate(var(--gaze-x, 0px), var(--gaze-y, 0px));
  transition: transform 90ms linear;
}
.lid {
  transform-box: fill-box;
  transform-origin: 50% 0%;
  transform: scaleY(0);
  animation: pet-blink 5.7s ease-in-out infinite;
}
@keyframes pet-blink {
  0%, 91%, 100% { transform: scaleY(0); }
  93%, 95% { transform: scaleY(1); }
}
.cheek { animation: pet-cheek 3.6s ease-in-out infinite; }
@keyframes pet-cheek { 0%, 100% { opacity: 0.42; } 50% { opacity: 0.62; } }

/* —— 睡觉 —— */
.sleeping .lid { animation: none; transform: scaleY(1); }
.sleeping .body { animation-duration: 5.2s; }
.sleeping .head { animation-duration: 5.2s; }
.sleeping .tail { animation-duration: 4.6s; }
.sleeping .eye-r { transform: translateY(1px); }
.zzz { opacity: 0; transition: opacity 240ms ease; }
.sleeping .zzz { opacity: 1; }
.sleeping .zzz text { animation: pet-zzz 2.6s ease-in-out infinite; }
.sleeping .zzz text:nth-child(2) { animation-delay: 0.5s; }
.sleeping .zzz text:nth-child(3) { animation-delay: 1s; }
@keyframes pet-zzz {
  0% { opacity: 0; transform: translate(0, 4px); }
  40% { opacity: 1; }
  100% { opacity: 0; transform: translate(6px, -8px); }
}

/* —— 情绪：只调呼吸节奏与嘴角，不换脸 —— */
.mood-happy .mouth { transform: translateY(0.5px) scaleX(1.08); transform-box: fill-box; transform-origin: 50% 50%; }
.mood-hungry .cheek { opacity: 0.3; }
.mood-worried .mouth { transform: rotate(180deg) translateY(3px); transform-box: fill-box; transform-origin: 50% 50%; }

/* —— 降级：只剩点击反馈 —— */
.reduced-motion .body,
.reduced-motion .head,
.reduced-motion .tail,
.reduced-motion .arm-l,
.reduced-motion .arm-r,
.reduced-motion .ears,
.reduced-motion .strand,
.reduced-motion .lid,
.reduced-motion .cheek {
  animation: none;
}
.reduced-motion .lid { transform: scaleY(0); }
.reduced-motion .sleeping .lid { transform: scaleY(1); }
</style>
