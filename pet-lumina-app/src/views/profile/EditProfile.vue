<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'
import { useFormA11y } from '@/composables/useFormA11y'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import { userApi } from '@/api/user'
import FormError from '@/components/common/FormError.vue'

const { t } = useI18n()
const router = useRouter()
const { showToast } = useToast()
const userStore = useUserStore()
const { currentUser } = storeToRefs(userStore)

const goBack = () => {
  router.back()
}

const userName = ref(currentUser.value?.nickname || '')
const userBio = ref(currentUser.value?.bio || '')
const loading = ref(false)
const nameInput = ref<HTMLInputElement | null>(null)
const attempted = ref(false)
const { errorMessage, errorId, announce, clear } = useFormA11y('edit-profile')

const nameMissing = computed(() => attempted.value && !userName.value.trim())

watch(userName, (value) => {
  if (value.trim()) {
    attempted.value = false
    clear()
  }
})

const handleSubmit = async () => {
  if (!userName.value.trim()) {
    attempted.value = true
    await announce(t('profile.usernamePlaceholder'))
    nameInput.value?.focus()
    return
  }
  loading.value = true
  try {
    await userApi.update({ nickname: userName.value, bio: userBio.value })
    userStore.$patch({
      currentUser: {
        ...currentUser.value,
        nickname: userName.value
      }
    })
    showToast(t('profile.saveSuccess'), 'success')
  } catch (error) {
    showToast(t('profile.saveFailed'), 'error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex items-center justify-between py-md mb-lg">
        <button type="button" @click="goBack" :aria-label="t('common.back')" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700" aria-hidden="true">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">{{ t('profile.editProfile') }}</span>
        <div class="w-10"></div>
      </div>

      <section class="space-y-4 mb-lg">
        <div>
          <label for="profile-nickname" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('profile.username') }}</label>
          <input
            ref="nameInput"
            id="profile-nickname"
            v-model="userName"
            autocomplete="name"
            :aria-invalid="nameMissing || undefined"
            :aria-describedby="errorMessage ? errorId : undefined"
            :placeholder="t('profile.usernamePlaceholder')"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
          />
          <FormError :id="errorId" :message="errorMessage" class="mt-2" />
        </div>

        <div>
          <label for="profile-bio" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('profile.bio') }}</label>
          <textarea
            id="profile-bio"
            v-model="userBio"
            :placeholder="t('profile.bioPlaceholder')"
            rows="4"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          ></textarea>
        </div>
      </section>

      <button
        @click="handleSubmit"
        :disabled="loading"
        class="w-full py-3.5 bg-primary text-on-primary rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform shadow-md disabled:opacity-50"
      >
        {{ loading ? t('profile.saving') : t('common.save') }}
      </button>
    </main>
  </div>
</template>
