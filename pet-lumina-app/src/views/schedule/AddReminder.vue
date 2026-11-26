<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'
import { useFormA11y } from '@/composables/useFormA11y'
import { useUserStore } from '@/stores/user'
import { reminderApi } from '@/api/reminder'
import FormError from '@/components/common/FormError.vue'
import type { Reminder } from '@/types'

const { t } = useI18n()
const router = useRouter()
const { showToast } = useToast()
const userStore = useUserStore()
const loading = ref(false)
const titleInput = ref<HTMLInputElement | null>(null)
const attempted = ref(false)
const { errorMessage, errorId, announce, clear } = useFormA11y('add-reminder')

const form = ref({
  title: '',
  date: '',
  time: '',
  location: '',
  type: 'daily' as Reminder['type'],
  repeat: 'none',
  notes: ''
})

const titleMissing = computed(() => attempted.value && !form.value.title.trim())

watch(() => form.value.title, (value) => {
  if (value.trim()) {
    attempted.value = false
    clear()
  }
})

const typeOptions = computed(() => [
  { value: 'daily', label: t('reminder.dailyCare'), icon: 'water_drop', color: 'bg-secondary-fixed text-secondary' },
  { value: 'medical', label: t('reminder.medicalHealth'), icon: 'medical_services', color: 'bg-primary-fixed text-primary' },
  { value: 'activity', label: t('reminder.exercise'), icon: 'pets', color: 'bg-tertiary-container text-tertiary' }
])

const repeatOptions = computed(() => [
  { value: 'none', label: t('reminder.none') },
  { value: 'daily', label: t('reminder.daily') },
  { value: 'weekly', label: t('reminder.weekly') },
  { value: 'monthly', label: t('reminder.monthly') }
])

const goBack = () => {
  router.back()
}

const submitForm = async () => {
  if (!form.value.title.trim()) {
    attempted.value = true
    await announce(t('reminder.enterTitle'))
    titleInput.value?.focus()
    return
  }

  loading.value = true
  try {
    await reminderApi.add({
      petId: userStore.currentPet?.id,
      title: form.value.title,
      type: form.value.type,
      remindTime: form.value.date && form.value.time ? `${form.value.date} ${form.value.time}` : undefined,
      location: form.value.location || undefined,
      repeatType: form.value.repeat as Reminder['repeatType'],
      notes: form.value.notes || undefined
    })
    showToast(t('reminder.createSuccess'), 'success')
    setTimeout(() => {
      router.back()
    }, 800)
  } catch (error) {
    showToast(t('reminder.createFailed'), 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <div class="flex items-center justify-between py-md mb-md">
        <button type="button" @click="goBack" :aria-label="t('common.back')" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700" aria-hidden="true">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">{{ t('reminder.addReminder') }}</span>
        <button @click="submitForm" :disabled="loading" class="active:scale-95 transition-transform px-4 py-2 bg-primary text-white rounded-full font-label-bold text-label-bold disabled:opacity-50">
          {{ loading ? t('pet.saving') : t('common.save') }}
        </button>
      </div>
      <section class="space-y-md">
        <div>
          <label for="reminder-title" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('reminder.reminderTitle') }} *</label>
          <input
            ref="titleInput"
            id="reminder-title"
            v-model="form.title"
            type="text"
            :aria-invalid="titleMissing || undefined"
            :aria-describedby="errorMessage ? errorId : undefined"
            :placeholder="t('reminder.titlePlaceholder')"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <FormError :id="errorId" :message="errorMessage" class="mt-2" />
        </div>

        <div>
          <label id="reminder-type-label" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('reminder.reminderType') }}</label>
          <div class="grid grid-cols-3 gap-sm" role="group" aria-labelledby="reminder-type-label">
            <button
              v-for="option in typeOptions"
              :key="option.value"
              type="button"
              :aria-pressed="form.type === option.value"
              @click="form.type = option.value as Reminder['type']"
              class="flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all"
              :class="form.type === option.value ? 'border-primary bg-primary-container' : 'border-surface-variant bg-surface-container'"
            >
              <span class="material-symbols-outlined" :class="option.color" aria-hidden="true">{{ option.icon }}</span>
              <span class="font-label-bold text-xs">{{ option.label }}</span>
            </button>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-md">
          <div>
            <label for="reminder-date" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('reminder.date') }}</label>
            <input
              id="reminder-date"
              v-model="form.date"
              type="date"
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
          <div>
            <label for="reminder-time" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('reminder.time') }}</label>
            <input
              id="reminder-time"
              v-model="form.time"
              type="time"
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <div>
          <label for="reminder-location" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('reminder.location') }}</label>
          <div class="relative">
            <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" aria-hidden="true">location_on</span>
            <input
              id="reminder-location"
              v-model="form.location"
              type="text"
              :placeholder="t('reminder.locationPlaceholder')"
              class="w-full bg-surface-container rounded-xl pl-10 pr-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>

        <div>
          <label id="reminder-repeat-label" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('reminder.repeat') }}</label>
          <div class="flex gap-sm flex-wrap" role="group" aria-labelledby="reminder-repeat-label">
            <button
              v-for="option in repeatOptions"
              :key="option.value"
              type="button"
              :aria-pressed="form.repeat === option.value"
              @click="form.repeat = option.value"
              class="px-4 py-2 rounded-full font-label-bold transition-colors"
              :class="form.repeat === option.value ? 'bg-primary text-white' : 'bg-surface-container-high text-on-surface-variant'"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <div>
          <label for="reminder-notes" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('reminder.notes') }}</label>
          <textarea
            id="reminder-notes"
            v-model="form.notes"
            rows="3"
            :placeholder="t('reminder.notesPlaceholder')"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          ></textarea>
        </div>
      </section>
    </main>
  </div>
</template>
