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

const showPassword = ref(false)
const oldPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const oldInput = ref<HTMLInputElement | null>(null)
const newInput = ref<HTMLInputElement | null>(null)
const confirmInput = ref<HTMLInputElement | null>(null)
const attempted = ref(false)
const { errorMessage, errorId, announce, clear } = useFormA11y('account-security')

const oldMissing = computed(() => attempted.value && !oldPassword.value)
const newMissing = computed(() => attempted.value && !newPassword.value)
const confirmMissing = computed(() => attempted.value && !confirmPassword.value)
const confirmMismatch = computed(() =>
  attempted.value &&
  !!newPassword.value &&
  !!confirmPassword.value &&
  newPassword.value !== confirmPassword.value
)

watch([oldPassword, newPassword, confirmPassword], () => {
  if (
    oldPassword.value &&
    newPassword.value &&
    confirmPassword.value &&
    newPassword.value === confirmPassword.value
  ) {
    attempted.value = false
    clear()
  }
})

const handleChangePassword = async () => {
  if (!oldPassword.value || !newPassword.value || !confirmPassword.value) {
    attempted.value = true
    await announce(t('profile.fillAllPassword'))
    if (!oldPassword.value) {
      oldInput.value?.focus()
    } else if (!newPassword.value) {
      newInput.value?.focus()
    } else {
      confirmInput.value?.focus()
    }
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    attempted.value = true
    await announce(t('profile.passwordMismatch'))
    confirmInput.value?.focus()
    return
  }
  loading.value = true
  try {
    await userApi.updatePassword({ oldPassword: oldPassword.value, newPassword: newPassword.value })
    showToast(t('profile.passwordChanged'), 'success')
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (error) {
    showToast(t('profile.passwordChangeFailed'), 'error')
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
        <span class="font-title-sm text-on-surface">{{ t('profile.accountSecurity') }}</span>
        <div class="w-10"></div>
      </div>

      <section class="space-y-4 mb-lg">
        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">{{ t('profile.bindingInfo') }}</h3>
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-on-surface-variant">phone</span>
                <span class="text-sm text-on-surface">{{ t('profile.phone') }}</span>
              </div>
              <span class="text-sm text-on-surface-variant">{{ currentUser?.phone || t('profile.unbound') }}</span>
            </div>
            <div class="flex justify-between items-center">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-on-surface-variant">mail</span>
                <span class="text-sm text-on-surface">{{ t('profile.email') }}</span>
              </div>
              <span class="text-sm text-on-surface-variant">{{ currentUser?.email || t('profile.unbound') }}</span>
            </div>
          </div>
        </div>

        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">{{ t('profile.changePassword') }}</h3>
          <div class="space-y-3">
            <div>
              <label for="security-old-password" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('profile.oldPassword') }}</label>
              <input
                ref="oldInput"
                id="security-old-password"
                v-model="oldPassword"
                type="password"
                autocomplete="current-password"
                :aria-invalid="oldMissing || undefined"
                :aria-describedby="errorMessage ? errorId : undefined"
                :placeholder="t('profile.oldPasswordPlaceholder')"
                class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label for="security-new-password" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('profile.newPassword') }}</label>
              <input
                ref="newInput"
                id="security-new-password"
                v-model="newPassword"
                type="password"
                autocomplete="new-password"
                :aria-invalid="newMissing || undefined"
                :aria-describedby="errorMessage ? errorId : undefined"
                :placeholder="t('profile.newPasswordPlaceholder')"
                class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label for="security-confirm-password" class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('profile.confirmPassword') }}</label>
              <input
                ref="confirmInput"
                id="security-confirm-password"
                v-model="confirmPassword"
                type="password"
                autocomplete="new-password"
                :aria-invalid="confirmMissing || confirmMismatch || undefined"
                :aria-describedby="errorMessage ? errorId : undefined"
                :placeholder="t('profile.confirmPasswordPlaceholder')"
                class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
              />
            </div>
            <FormError :id="errorId" :message="errorMessage" />
            <button
              type="button"
              @click="handleChangePassword"
              :disabled="loading"
              class="w-full py-3 bg-primary text-on-primary rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform disabled:opacity-50"
            >
              {{ loading ? t('profile.changing') : t('profile.changePassword') }}
            </button>
          </div>
        </div>

        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">{{ t('profile.loginDevices') }}</h3>
          <div class="flex items-center justify-between py-2">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-on-surface-variant">phone_iphone</span>
              <div>
                <p class="text-sm text-on-surface">{{ t('profile.currentDevice') }}</p>
                <p class="text-xs text-tertiary">iPhone 15 Pro</p>
              </div>
            </div>
            <span class="text-xs text-emerald-500 font-label-bold">{{ t('profile.online') }}</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
