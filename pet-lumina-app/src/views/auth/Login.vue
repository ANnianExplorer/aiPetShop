<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()
const showPassword = ref(false)
const phone = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!phone.value || !password.value) {
    showToast(t('auth.fillComplete'))
    return
  }
  loading.value = true
  try {
    await userStore.login(phone.value, password.value)
    router.push('/home')
  } catch (e) {
    // error toast handled by interceptor
  } finally {
    loading.value = false
  }
}

const goToSignUp = () => {
  router.push({ name: 'signUp' })
}

const goToResetPassword = () => {
  router.push({ name: 'resetPassword' })
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

    <!-- Ambient decorative glows -->
    <div class="absolute -top-20 -left-20 w-64 h-64 bg-primary/10 rounded-full blur-3xl z-0 animate-breathe"></div>
    <div class="absolute -bottom-20 -right-20 w-80 h-80 bg-secondary/5 rounded-full blur-3xl z-0 animate-breathe" style="animation-delay: -1.5s"></div>

    <!-- Main Login Canvas -->
    <main class="relative z-10 w-full max-w-[380px] px-container-padding pt-lg">
      <!-- Brand Identity -->
      <header class="text-center mb-lg animate-float-up">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-full glass-panel-deep mb-sm shadow-md">
          <span class="material-symbols-outlined text-primary text-[28px] glow-icon">pets</span>
        </div>
        <h1 class="font-display-lg text-display-lg text-primary tracking-tighter mb-xs">PetLumina</h1>
        <p class="font-body-md text-body-md text-primary/80">{{ t('auth.tagline') }}</p>
      </header>

      <!-- Glassmorphism Card -->
      <section class="glass-panel-deep rounded-[32px] p-lg depth-3 animate-float-up stagger-1">
        <h2 class="font-headline-md text-headline-md text-on-surface mb-lg text-center">{{ t('auth.welcomeBack') }}</h2>

        <form class="space-y-sm" @submit.prevent="handleLogin">
          <!-- Account Field -->
          <div class="relative">
            <div class="absolute inset-y-0 left-md flex items-center pointer-events-none text-primary">
              <span class="material-symbols-outlined">person</span>
            </div>
            <input
              v-model="phone"
              type="text"
              class="glass-input w-full h-12 pl-12 pr-md rounded-xl font-body-md text-body-md placeholder-outline"
              :placeholder="t('auth.phonePlaceholder')"
            />
          </div>

          <!-- Password Field -->
          <div class="relative">
            <div class="absolute inset-y-0 left-md flex items-center pointer-events-none text-primary">
              <span class="material-symbols-outlined">lock</span>
            </div>
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              class="glass-input w-full h-12 pl-12 pr-12 rounded-xl font-body-md text-body-md placeholder-outline"
              :placeholder="t('auth.passwordPlaceholder')"
            />
            <button
              type="button"
              class="absolute inset-y-0 right-md flex items-center text-primary/50 hover:text-primary transition-colors"
              @click="showPassword = !showPassword"
            >
              <span class="material-symbols-outlined">{{ showPassword ? 'visibility' : 'visibility_off' }}</span>
            </button>
          </div>

          <!-- Forgot Password Link -->
          <div class="text-right">
            <button
              type="button"
              class="font-label-bold text-label-bold text-primary hover:opacity-70 transition-opacity"
              @click="goToResetPassword"
            >
              {{ t('auth.forgotPassword') }}
            </button>
          </div>

          <!-- Login Button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full h-12 bg-primary text-on-primary font-title-sm text-title-sm rounded-full shadow-lg shadow-primary/25 btn-jelly disabled:opacity-60"
          >
            {{ loading ? t('auth.loggingIn') : t('auth.loginNow') }}
          </button>
        </form>

        <!-- Terms -->
        <div class="mt-sm text-center">
          <p class="font-caption-sm text-caption-sm text-outline">
            {{ t('auth.termsLogin') }} <span class="text-primary font-medium">{{ t('auth.userAgreement') }}</span> {{ t('common.confirm') }} <span class="text-primary font-medium">{{ t('auth.privacyPolicy') }}</span>
          </p>
        </div>
      </section>

      <!-- Footer Actions -->
      <footer class="mt-lg text-center animate-float-up stagger-2">
        <button
          class="font-body-md text-body-md text-on-surface-variant flex items-center justify-center gap-xs"
          @click="goToSignUp"
        >
          {{ t('auth.noAccount') }} <span class="text-primary font-semibold">{{ t('auth.registerNow') }}</span>
        </button>

        <div class="mt-lg flex items-center justify-center gap-xl opacity-60">
          <div class="w-10 h-10 rounded-full glass-panel flex items-center justify-center icon-btn">
            <span class="material-symbols-outlined text-green-500 text-[20px]">chat</span>
          </div>
          <div class="w-10 h-10 rounded-full glass-panel flex items-center justify-center icon-btn">
            <span class="material-symbols-outlined text-primary text-[20px]">smartphone</span>
          </div>
        </div>
      </footer>
    </main>
  </div>
</template>
