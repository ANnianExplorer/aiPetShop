<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'
import { useFormA11y } from '@/composables/useFormA11y'
import { useUserStore } from '@/stores/user'
import { fileApi } from '@/api/file'
import FormError from '@/components/common/FormError.vue'

const { t } = useI18n()
const router = useRouter()
const { showToast } = useToast()
const userStore = useUserStore()
const submitting = ref(false)

const petName = ref('')
const petType = ref('')
const petBreed = ref('')
const petAge = ref('')
const petAvatar = ref('')
const petNotes = ref('')
const avatarUploading = ref(false)
const nameInput = ref<HTMLInputElement | null>(null)
const breedInput = ref<HTMLInputElement | null>(null)
const typeGroup = ref<HTMLElement | null>(null)
const attempted = ref(false)
const { errorMessage, errorId, announce, clear } = useFormA11y('add-pet')

const nameMissing = computed(() => attempted.value && !petName.value.trim())
const typeMissing = computed(() => attempted.value && !petType.value)
const breedMissing = computed(() => attempted.value && !petBreed.value.trim())

watch([petName, petType, petBreed], () => {
  if (petName.value.trim() && petType.value && petBreed.value.trim()) {
    attempted.value = false
    clear()
  }
})

const petTypes = computed(() => [
  { id: 'dog', name: t('petForm.dog'), icon: 'pets' },
  { id: 'cat', name: t('petForm.cat'), icon: 'cat' },
  { id: 'other', name: t('petForm.other'), icon: 'paw' }
])

const typeLabel = computed(() => petTypes.value.find(p => p.id === petType.value)?.name || t('petForm.notSelected'))

const avatarInput = ref<HTMLInputElement | null>(null)
const handleAvatarClick = () => { avatarInput.value?.click() }

const handleFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { showToast(t('petForm.imageTooLarge'), 'error'); input.value = ''; return }
  petAvatar.value = URL.createObjectURL(file)
  avatarUploading.value = true
  try {
    petAvatar.value = await fileApi.uploadImage(file, 'pet/image')
    showToast(t('petForm.uploadSuccess'), 'success')
  } catch { petAvatar.value = ''; showToast(t('petForm.uploadFailed'), 'error') } finally { avatarUploading.value = false; input.value = '' }
}

const selectPetType = (type: string) => { petType.value = type }
const goBack = () => router.back()

const handleSubmit = async () => {
  if (!petName.value.trim() || !petType.value || !petBreed.value.trim()) {
    attempted.value = true
    await announce(t('petForm.fillRequired'))
    if (!petName.value.trim()) {
      nameInput.value?.focus()
    } else if (!petBreed.value.trim()) {
      breedInput.value?.focus()
    } else {
      typeGroup.value?.querySelector<HTMLButtonElement>('button')?.focus()
    }
    return
  }
  submitting.value = true
  try {
    await userStore.addPet({
      name: petName.value, type: petType.value, breed: petBreed.value,
      age: petAge.value || undefined, notes: petNotes.value || undefined, avatar: petAvatar.value || undefined,
    })
    showToast(t('petForm.addSuccess'), 'success')
    setTimeout(() => router.back(), 800)
  } catch { showToast(t('petForm.addFailed'), 'error') } finally { submitting.value = false }
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <!-- Header -->
      <div class="flex items-center justify-between py-md mb-lg animate-float-up">
        <button type="button" @click="goBack" :aria-label="t('common.back')" class="icon-btn p-2 rounded-full">
          <span class="material-symbols-outlined text-primary" aria-hidden="true">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">{{ t('petForm.addPet') }}</span>
        <div class="w-10"></div>
      </div>

      <!-- Preview Card -->
      <div class="glass-card rounded-2xl overflow-hidden mb-lg animate-float-up stagger-1">
        <div class="h-36 relative overflow-hidden">
          <img v-if="petAvatar" :src="petAvatar" class="w-full h-full object-cover" alt="" />
          <div v-else class="w-full h-full bg-gradient-to-br from-primary-container/30 to-primary/10 flex items-center justify-center">
            <span class="material-symbols-outlined text-white/30" style="font-size: 60px">pets</span>
          </div>
          <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
          <div class="absolute bottom-3 left-4 text-white">
            <h3 class="font-display-lg text-lg drop-shadow-lg">{{ petName || t('petForm.petName') }}</h3>
            <p class="text-white/80 text-xs">{{ petBreed || t('petForm.breed') }} · {{ typeLabel }}</p>
          </div>
        </div>
      </div>

      <!-- Avatar Upload -->
      <section class="mb-lg flex flex-col items-center animate-float-up stagger-2">
        <input ref="avatarInput" type="file" accept="image/jpeg,image/png,image/gif,image/webp" class="hidden" @change="handleFileChange" />
        <button
          type="button"
          class="relative group cursor-pointer disabled:opacity-60"
          :aria-label="t('petForm.uploadAvatar')"
          :disabled="avatarUploading"
          @click="handleAvatarClick"
        >
          <div class="w-28 h-28 rounded-full border-4 border-white shadow-xl overflow-hidden bg-surface-container flex items-center justify-center">
            <img v-if="petAvatar" class="w-full h-full object-cover" :src="petAvatar" alt="" />
            <span v-else class="material-symbols-outlined text-5xl text-on-surface-variant" aria-hidden="true">add_a_photo</span>
          </div>
          <div class="absolute bottom-0 right-0 bg-primary p-1.5 rounded-full text-white shadow-md">
            <span class="material-symbols-outlined text-[16px]" aria-hidden="true">{{ avatarUploading ? 'hourglass_top' : 'edit' }}</span>
          </div>
        </button>
        <p class="mt-2 text-sm text-tertiary">{{ avatarUploading ? t('petForm.uploading') : t('petForm.clickToUpload') }}</p>
      </section>

      <!-- Pet Type -->
      <section class="mb-lg animate-float-up stagger-3">
        <div class="flex items-center gap-2 mb-3">
          <span class="material-symbols-outlined text-primary text-lg" aria-hidden="true">category</span>
          <label id="add-pet-type-label" class="font-label-bold text-label-bold text-on-surface">{{ t('petForm.petType') }} *</label>
        </div>
        <div
          ref="typeGroup"
          class="grid grid-cols-3 gap-3"
          role="group"
          aria-labelledby="add-pet-type-label"
          :aria-invalid="typeMissing || undefined"
          :aria-describedby="errorMessage ? errorId : undefined"
        >
          <button v-for="type in petTypes" :key="type.id" type="button" @click="selectPetType(type.id)"
            :aria-pressed="petType === type.id"
            class="flex flex-col items-center gap-2 p-4 rounded-2xl transition-all btn-jelly"
            :class="petType === type.id ? 'bg-primary text-on-primary shadow-md' : 'glass-card text-on-surface-variant'">
            <span class="material-symbols-outlined text-2xl">{{ type.icon }}</span>
            <span class="text-xs font-label-bold">{{ type.name }}</span>
          </button>
        </div>
      </section>

      <!-- Basic Info -->
      <section class="mb-lg animate-float-up stagger-4">
        <div class="flex items-center gap-2 mb-3">
          <span class="material-symbols-outlined text-primary text-lg">pets</span>
          <label class="font-label-bold text-label-bold text-on-surface">{{ t('petForm.basicInfo') }}</label>
        </div>
        <div class="space-y-4">
          <div>
            <label for="add-pet-name" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('petForm.petName') }} *</label>
            <input
              ref="nameInput"
              id="add-pet-name"
              v-model="petName"
              :aria-invalid="nameMissing || undefined"
              :aria-describedby="errorMessage ? errorId : undefined"
              :placeholder="t('petForm.nameExample')"
              class="w-full glass-input rounded-xl px-4 py-3 font-body-sm text-on-surface"
            />
          </div>
          <div>
            <label for="add-pet-breed" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('petForm.breed') }} *</label>
            <input
              ref="breedInput"
              id="add-pet-breed"
              v-model="petBreed"
              :aria-invalid="breedMissing || undefined"
              :aria-describedby="errorMessage ? errorId : undefined"
              :placeholder="t('petForm.breedExample')"
              class="w-full glass-input rounded-xl px-4 py-3 font-body-sm text-on-surface"
            />
          </div>
          <div>
            <label for="add-pet-age" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('petForm.age') }}</label>
            <input id="add-pet-age" v-model="petAge" :placeholder="t('petForm.ageExample')" class="w-full glass-input rounded-xl px-4 py-3 font-body-sm text-on-surface" />
          </div>
        </div>
      </section>

      <!-- Health Notes -->
      <section class="mb-lg animate-float-up stagger-5">
        <div class="flex items-center gap-2 mb-3">
          <span class="material-symbols-outlined text-primary text-lg">medical_information</span>
          <label for="add-pet-notes" class="font-label-bold text-label-bold text-on-surface">{{ t('petForm.healthProfile') }}</label>
        </div>
        <textarea id="add-pet-notes" v-model="petNotes" :placeholder="t('petForm.healthNotesPlaceholder')" rows="3"
          class="w-full glass-input rounded-xl px-4 py-3 font-body-sm text-on-surface resize-none"></textarea>
      </section>

      <!-- Submit -->
      <FormError :id="errorId" :message="errorMessage" class="mb-3" />
      <button type="button" @click="handleSubmit" :disabled="submitting || avatarUploading"
        class="w-full py-3.5 bg-primary text-on-primary rounded-2xl font-label-bold text-label-bold btn-jelly shadow-md disabled:opacity-50 animate-float-up stagger-6">
        {{ submitting ? t('petForm.saving') : t('common.save') }}
      </button>
    </main>
  </div>
</template>
