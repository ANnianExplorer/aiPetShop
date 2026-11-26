<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'
import FormError from '@/components/common/FormError.vue'
import { useFormA11y } from '@/composables/useFormA11y'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const showPassword = ref(false)
const phone = ref('')
const code = ref('')
const password = ref('')
const loading = ref(false)
const codeLoading = ref(false)
const countdown = ref(0)
const phoneInput = ref<HTMLInputElement | null>(null)
const codeInput = ref<HTMLInputElement | null>(null)
const passwordInput = ref<HTMLInputElement | null>(null)
const attempted = ref(false)
const codeAttempted = ref(false)
const { errorMessage, errorId, announce, clear } = useFormA11y('signup')

const phoneMissing = computed(() => (attempted.value || codeAttempted.value) && !phone.value.trim())
const codeMissing = computed(() => attempted.value && !code.value.trim())
const passwordMissing = computed(() => attempted.value && !password.value)

watch([phone, code, password], () => {
  if (codeAttempted.value && phone.value.trim()) {
    codeAttempted.value = false
  }
  if (attempted.value && phone.value.trim() && code.value.trim() && password.value) {
    attempted.value = false
  }
  if (!attempted.value && !codeAttempted.value) {
    clear()
  }
})

const handleSignUp = async () => {
  if (!phone.value.trim() || !code.value.trim() || !password.value) {
    attempted.value = true
    await announce(t('auth.fillComplete'))
    if (!phone.value.trim()) {
      phoneInput.value?.focus()
    } else if (!code.value.trim()) {
      codeInput.value?.focus()
    } else {
      passwordInput.value?.focus()
    }
    return
  }
  loading.value = true
  try {
    await userStore.register(phone.value, code.value, password.value)
    router.push('/home')
  } catch (e) {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}

const sendCode = async () => {
  if (!phone.value.trim()) {
    codeAttempted.value = true
    await announce(t('auth.enterPhoneFirst'))
    phoneInput.value?.focus()
    return
  }
  codeLoading.value = true
  try {
    await authApi.sendCode(phone.value)
    showToast(t('auth.codeSent'))
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    // error handled by interceptor
  } finally {
    codeLoading.value = false
  }
}

const goToLogin = () => {
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="fixed inset-0 flex items-center justify-center bg-background overflow-hidden">
    <!-- Background Image -->
    <div class="absolute inset-0 z-0">
      <img
        src="https://lh3.googleusercontent.com/aida-public/AB6AXuC4tKRCQtXUHxvAU4jCMAatjrjEDhlY4SQc6AIQXFy_z_sHvwyK9RJDeF3TXsvnVW2NsQ0JjRqnH7Oyn4F-duH9k499_ofjNrys2WaA9DevC9v8lOKM6-g9nGIxPAqaq5GZGVYC4fWEEWCTe1cxW8rSDQ61bZoa4GDV-lj5hR-GJq5ZdWR9oMRqZ2ExZKjE0dGIUAXP8rqAdXKLht2fsKL94MeK7w0_JvIIx6WDR8JTaZzCh-wTRcSnYuUUMdoN_5Tg8MuSu77UbqzL"
        class="w-full h-full object-cover scale-105 blur-sm"
      />
      <div class="absolute inset-0 bg-white/20"></div>
    </div>

    <!-- Decorative Elements -->
    <div class="absolute -top-20 -left-20 w-64 h-64 bg-primary/10 rounded-full blur-3xl z-0"></div>
    <div class="absolute -bottom-20 -right-20 w-80 h-80 bg-secondary/5 rounded-full blur-3xl z-0"></div>

    <!-- Main Registration Canvas -->
    <main class="relative z-10 w-full max-w-[380px] px-container-padding pt-lg">
      <!-- Brand Identity -->
      <header class="text-center mb-lg">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-white/40 backdrop-blur-xl mb-sm shadow-sm">
          <span class="material-symbols-outlined text-primary text-[28px]">pets</span>
        </div>
        <h1 class="font-display-lg text-display-lg text-primary tracking-tighter mb-xs">PetLumina</h1>
        <p class="font-body-md text-body-md text-primary/80">{{ t('auth.startJourney') }}</p>
      </header>

      <!-- Glassmorphism Card -->
      <section class="glass-panel rounded-[32px] p-lg shadow-[0_8px_32px_rgba(0,0,0,0.08)]">
        <h2 class="font-headline-md text-headline-md text-on-surface mb-lg text-center">{{ t('auth.newUserRegister') }}</h2>

        <form class="space-y-sm" @submit.prevent="handleSignUp">
          <!-- Mobile / Email Field -->
          <div class="relative">
            <div class="absolute inset-y-0 left-md flex items-center pointer-events-none text-primary">
              <span class="material-symbols-outlined">person</span>
            </div>
            <input
              ref="phoneInput"
              v-model="phone"
              id="signup-phone"
              type="text"
              :aria-label="t('auth.phone')"
              autocomplete="tel"
              inputmode="tel"
              :aria-invalid="phoneMissing || undefined"
              :aria-describedby="errorMessage ? errorId : undefined"
              class="w-full h-12 pl-12 pr-md bg-white/40 border-none rounded-xl font-body-md text-body-md placeholder-outline focus:ring-2 focus:ring-primary/20 transition-all"
              :placeholder="t('auth.phonePlaceholder')"
            />
          </div>

          <!-- Verification Code Field -->
          <div class="flex gap-sm">
            <div class="relative flex-1">
              <div class="absolute inset-y-0 left-md flex items-center pointer-events-none text-primary">
                <span class="material-symbols-outlined">verified_user</span>
              </div>
              <input
                ref="codeInput"
                v-model="code"
                id="signup-code"
                type="text"
                :aria-label="t('auth.verifyCode')"
                autocomplete="one-time-code"
                inputmode="numeric"
                :aria-invalid="codeMissing || undefined"
                :aria-describedby="errorMessage ? errorId : undefined"
                class="w-full h-12 pl-12 pr-md bg-white/40 border-none rounded-xl font-body-md text-body-md placeholder-outline focus:ring-2 focus:ring-primary/20 transition-all"
                :placeholder="t('auth.verifyCode')"
              />
            </div>
            <button
              type="button"
              :disabled="codeLoading || countdown > 0"
              class="px-md h-12 bg-primary-container/30 text-on-primary-container font-label-bold text-label-bold rounded-xl whitespace-nowrap active:scale-95 transition-transform disabled:opacity-60"
              @click="sendCode"
            >
              {{ countdown > 0 ? `${countdown}s` : t('auth.getCode') }}
            </button>
          </div>

          <!-- Password Field -->
          <div class="relative">
            <div class="absolute inset-y-0 left-md flex items-center pointer-events-none text-primary">
              <span class="material-symbols-outlined">lock</span>
            </div>
            <input
              ref="passwordInput"
              v-model="password"
              id="signup-password"
              :type="showPassword ? 'text' : 'password'"
              :aria-label="t('auth.password')"
              autocomplete="new-password"
              :aria-invalid="passwordMissing || undefined"
              :aria-describedby="errorMessage ? errorId : undefined"
              class="w-full h-12 pl-12 pr-12 bg-white/40 border-none rounded-xl font-body-md text-body-md placeholder-outline focus:ring-2 focus:ring-primary/20 transition-all"
              :placeholder="t('auth.setPassword')"
            />
            <button
              type="button"
              :aria-label="showPassword ? t('auth.hidePassword') : t('auth.showPassword')"
              class="absolute inset-y-0 right-md flex items-center text-primary/50"
              @click="showPassword = !showPassword"
            >
              <span class="material-symbols-outlined" aria-hidden="true">{{ showPassword ? 'visibility' : 'visibility_off' }}</span>
            </button>
          </div>

          <FormError :id="errorId" :message="errorMessage" />

          <!-- Register Button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full h-12 bg-primary text-on-primary font-title-sm text-title-sm rounded-full shadow-lg shadow-primary/20 active:scale-95 transition-all duration-200 disabled:opacity-60"
          >
            {{ loading ? t('auth.registering') : t('auth.registerNow') }}
          </button>
        </form>

        <!-- Terms -->
        <div class="mt-sm text-center">
          <p class="font-caption-sm text-caption-sm text-outline">
            {{ t('auth.termsRegister') }} <span class="text-primary font-medium">{{ t('auth.userAgreement') }}</span> {{ t('common.confirm') }} <span class="text-primary font-medium">{{ t('auth.privacyPolicy') }}</span>
          </p>
        </div>
      </section>

      <!-- Footer Actions -->
      <footer class="mt-lg text-center">
        <button
          class="font-body-md text-body-md text-on-surface-variant flex items-center justify-center gap-xs"
          @click="goToLogin"
        >
          {{ t('auth.hasAccount') }} <span class="text-primary font-semibold">{{ t('auth.goToLogin') }}</span>
        </button>

        <div class="mt-lg flex items-center justify-center gap-xl opacity-60">
          <div class="w-10 h-10 rounded-full glass-panel flex items-center justify-center">
            <span class="material-symbols-outlined text-green-500 text-[20px]">chat</span>
          </div>
          <div class="w-10 h-10 rounded-full glass-panel flex items-center justify-center">
            <span class="material-symbols-outlined text-primary text-[20px]">smartphone</span>
          </div>
        </div>
      </footer>
    </main>
  </div>
</template>
