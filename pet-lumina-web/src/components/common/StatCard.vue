<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  icon: string
  color?: string
  trend?: string
  trendUp?: boolean
  delay?: number
}>()
</script>

<template>
  <div
    class="glass-panel rounded-2xl p-5 flex items-center justify-between depth-1 animate-float-up"
    :style="{ animationDelay: `${delay || 0}s` }"
  >
    <div>
      <p class="text-slate-500 text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-1">{{ label }}</p>
      <div class="flex items-baseline gap-2">
        <h3 class="font-[Plus_Jakarta_Sans] text-[36px] font-bold" :class="color || 'text-primary'">{{ value }}</h3>
        <span v-if="trend" class="text-xs font-bold flex items-center gap-1" :class="trendUp ? 'text-emerald-600' : 'text-error'">
          <span class="material-symbols-outlined text-base">{{ trendUp ? 'trending_up' : 'trending_down' }}</span>
          {{ trend }}
        </span>
      </div>
    </div>
    <div class="w-14 h-14 rounded-2xl flex items-center justify-center" :class="color === 'text-amber-500' ? 'bg-amber-100 text-amber-600' : color === 'text-error' ? 'bg-red-100 text-red-600' : 'bg-emerald-100 text-emerald-600'">
      <span class="material-symbols-outlined text-3xl">{{ icon }}</span>
    </div>
  </div>
</template>
