<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/user'
import { userApi } from '@/api/user'

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

const handleSubmit = async () => {
  if (!userName.value.trim()) {
    showToast(t('profile.usernamePlaceholder'), 'error')
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
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">{{ t('profile.editProfile') }}</span>
        <div class="w-10"></div>
      </div>

      <section class="space-y-4 mb-lg">
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('profile.username') }}</label>
          <input
            v-model="userName"
            :placeholder="t('profile.usernamePlaceholder')"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('profile.bio') }}</label>
          <textarea
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
