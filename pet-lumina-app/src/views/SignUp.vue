<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const showPassword = ref(false)

const handleSignUp = () => {
  router.push({ name: 'login' })
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
        <p class="font-body-md text-body-md text-primary/80">开启您的宠物治愈之旅</p>
      </header>

      <!-- Glassmorphism Card -->
      <section class="glass-panel rounded-[32px] p-lg shadow-[0_8px_32px_rgba(0,0,0,0.08)]">
        <h2 class="font-headline-md text-headline-md text-on-surface mb-lg text-center">新用户注册</h2>
        
        <form class="space-y-sm" @submit.prevent="handleSignUp">
          <!-- Mobile / Email Field -->
          <div class="relative">
            <div class="absolute inset-y-0 left-md flex items-center pointer-events-none text-primary">
              <span class="material-symbols-outlined">person</span>
            </div>
            <input 
              type="text" 
              class="w-full h-12 pl-12 pr-md bg-white/40 border-none rounded-xl font-body-md text-body-md placeholder-outline focus:ring-2 focus:ring-primary/20 transition-all" 
              placeholder="手机号或邮箱" 
            />
          </div>

          <!-- Verification Code Field -->
          <div class="flex gap-sm">
            <div class="relative flex-1">
              <div class="absolute inset-y-0 left-md flex items-center pointer-events-none text-primary">
                <span class="material-symbols-outlined">verified_user</span>
              </div>
              <input 
                type="text" 
                class="w-full h-12 pl-12 pr-md bg-white/40 border-none rounded-xl font-body-md text-body-md placeholder-outline focus:ring-2 focus:ring-primary/20 transition-all" 
                placeholder="验证码" 
              />
            </div>
            <button 
              type="button" 
              class="px-md h-12 bg-primary-container/30 text-on-primary-container font-label-bold text-label-bold rounded-xl whitespace-nowrap active:scale-95 transition-transform"
            >
              获取验证码
            </button>
          </div>

          <!-- Password Field -->
          <div class="relative">
            <div class="absolute inset-y-0 left-md flex items-center pointer-events-none text-primary">
              <span class="material-symbols-outlined">lock</span>
            </div>
            <input 
              :type="showPassword ? 'text' : 'password'" 
              class="w-full h-12 pl-12 pr-12 bg-white/40 border-none rounded-xl font-body-md text-body-md placeholder-outline focus:ring-2 focus:ring-primary/20 transition-all" 
              placeholder="设置密码" 
            />
            <button 
              type="button" 
              class="absolute inset-y-0 right-md flex items-center text-primary/50"
              @click="showPassword = !showPassword"
            >
              <span class="material-symbols-outlined">{{ showPassword ? 'visibility' : 'visibility_off' }}</span>
            </button>
          </div>

          <!-- Register Button -->
          <button 
            type="submit" 
            class="w-full h-12 bg-primary text-on-primary font-title-sm text-title-sm rounded-full shadow-lg shadow-primary/20 active:scale-95 transition-all duration-200"
          >
            立即注册
          </button>
        </form>

        <!-- Terms -->
        <div class="mt-sm text-center">
          <p class="font-caption-sm text-caption-sm text-outline">
            注册即代表您同意 <span class="text-primary font-medium">用户协议</span> 和 <span class="text-primary font-medium">隐私政策</span>
          </p>
        </div>
      </section>

      <!-- Footer Actions -->
      <footer class="mt-lg text-center">
        <button 
          class="font-body-md text-body-md text-on-surface-variant flex items-center justify-center gap-xs"
          @click="goToLogin"
        >
          已有账号？ <span class="text-primary font-semibold">前往登录</span>
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
