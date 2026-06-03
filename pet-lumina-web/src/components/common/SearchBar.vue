<script setup lang="ts">
defineProps<{
  placeholder?: string
  modelValue: string
}>()

defineEmits(['update:modelValue', 'search', 'reset'])
</script>

<template>
  <div class="glass-panel rounded-full px-6 py-4 flex items-center gap-4 flex-wrap">
    <div class="relative flex-1 min-w-[200px]">
      <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant text-lg">search</span>
      <input
        :value="modelValue"
        @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
        type="text"
        :placeholder="placeholder || '搜索...'"
        class="w-full bg-white/15 backdrop-blur-[10px] border border-white/30 rounded-full pl-11 pr-4 py-3 text-on-surface placeholder-on-surface-variant/60 focus:ring-2 focus:ring-primary-container/30 focus:border-primary-container/50 outline-none transition-all text-sm"
        @keyup.enter="$emit('search')"
      />
    </div>
    <slot />
    <button
      class="bg-primary-container text-white rounded-2xl px-6 py-3 font-bold shadow-[0_10px_25px_-5px_rgba(109,175,146,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-200 text-sm"
      @click="$emit('search')"
    >
      搜索
    </button>
    <button
      class="glass-panel rounded-2xl px-6 py-3 text-on-surface-variant hover:bg-white/20 transition-all text-sm"
      @click="$emit('reset')"
    >
      重置
    </button>
  </div>
</template>
