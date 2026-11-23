<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'

const { t } = useI18n()
const { toasts, removeToast } = useToast()

const getIcon = (type: string) => {
  const icons: Record<string, string> = {
    success: 'check_circle',
    error: 'error',
    warning: 'warning',
    info: 'info'
  }
  return icons[type]
}

const getColor = (type: string) => {
  const colors: Record<string, string> = {
    success: 'bg-emerald-500 text-white',
    error: 'bg-red-500 text-white',
    warning: 'bg-amber-500 text-white',
    info: 'bg-blue-500 text-white'
  }
  return colors[type]
}
</script>

<template>
  <Teleport to="body">
    <TransitionGroup 
      tag="div" 
      role="status"
      aria-live="polite"
      aria-atomic="true"
      class="fixed top-20 left-0 right-0 z-[100] flex flex-col items-center gap-2 px-4 pointer-events-none"
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 -translate-y-4 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 -translate-y-4 scale-95"
    >
      <div
        v-for="toast in toasts"
        :key="toast.id"
        :role="toast.type === 'error' ? 'alert' : undefined"
        class="pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl shadow-lg backdrop-blur-xl max-w-sm w-full"
        :class="getColor(toast.type)"
      >
        <span aria-hidden="true" class="material-symbols-outlined text-xl flex-shrink-0">{{ getIcon(toast.type) }}</span>
        <p class="font-body-md text-sm flex-1">{{ toast.message }}</p>
        <button
          type="button"
          :aria-label="t('common.close')"
          @click="removeToast(toast.id)"
          class="flex-shrink-0 opacity-80 hover:opacity-100 transition-opacity"
        >
          <span aria-hidden="true" class="material-symbols-outlined text-lg">close</span>
        </button>
      </div>
    </TransitionGroup>
  </Teleport>
</template>
