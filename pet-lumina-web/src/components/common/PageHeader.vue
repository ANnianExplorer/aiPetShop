<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
  icon?: string
}>()
</script>

<template>
  <div class="flex justify-between items-end animate-float-up">
    <div>
      <h2 class="font-[Plus_Jakarta_Sans] text-[32px] font-bold text-primary mb-2 flex items-center gap-3">
        <span v-if="icon" class="material-symbols-outlined text-[36px]">{{ icon }}</span>
        {{ title }}
      </h2>
      <p v-if="subtitle" class="text-on-surface-variant">{{ subtitle }}</p>
    </div>
    <div class="flex items-center gap-3">
      <slot name="actions" />
    </div>
  </div>
</template>
