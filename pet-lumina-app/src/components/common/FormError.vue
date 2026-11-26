<script setup lang="ts">
defineProps<{
  id: string
  message: string
}>()
</script>

<template>
  <p
    v-if="message"
    :id="id"
    role="alert"
    data-testid="form-error"
    class="flex items-start gap-2 rounded-xl bg-error/10 px-3 py-2 text-sm text-error"
  >
    <span class="material-symbols-outlined text-base leading-5" aria-hidden="true">error</span>
    <span class="leading-5">{{ message }}</span>
  </p>
</template>
