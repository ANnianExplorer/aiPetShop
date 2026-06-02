<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { authApi } from '@/api/auth'

const router = useRouter()
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)
const phone = ref('')
const code = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const codeLoading = ref(false)
const countdown = ref(0)

const goBack = () => {
  router.back()
}

const sendCode = async () => {
  if (!phone.value) {
    showToast('请先输入手机号')
    return
  }
  codeLoading.value = true
  try {
    await authApi.sendCode(phone.value)
    showToast('验证码已发送')
    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    // handled
  } finally {
    codeLoading.value = false
  }
}

const handleReset = async () => {
  if (!phone.value || !code.value || !newPassword.value) {
    showToast('请填写完整信息')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    showToast('两次密码输入不一致')
    return
  }
  if (newPassword.value.length < 6) {
    showToast('密码长度不能少于6位')
    return
  }
  loading.value = true
  try {
    await authApi.resetPassword({ phone: phone.value, code: code.value, password: newPassword.value })
    showToast('密码重置成功')
    router.push({ name: 'login' })
  } catch (e) {
    // handled
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen relative flex flex-col items-center justify-center p-container-padding overflow-hidden bg-background">
    <!-- Background Decor -->
    <div class="fixed inset-0 bg-pattern -z-10"></div>
    <div class="fixed top-[-10%] right-[-10%] w-[600px] h-[600px] bg-primary/5 rounded-full blur-[120px] -z-10"></div>
    <div class="fixed bottom-[-10%] left-[-10%] w-[500px] h-[500px] bg-secondary/5 rounded-full blur-[100px] -z-10"></div>

    <!-- Navigation Header -->
    <header class="fixed top-0 w-full z-50 flex justify-between items-center px-5 h-16 bg-white/40 backdrop-blur-xl border-b border-white/20 shadow-[0_4px_20px_rgba(0,0,0,0.05)]">
      <button @click="goBack" class="flex items-center justify-center w-10 h-10 rounded-full hover:bg-white/50 active:scale-95 transition-all duration-200">
        <span class="material-symbols-outlined text-primary">arrow_back</span>
      </button>
      <span class="font-title-sm text-on-surface">重置密码</span>
      <div class="w-10"></div>
    </header>

    <main class="w-full max-w-md mt-16 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <!-- Hero Visual Section -->
      <div class="mb-xl text-center">
        <div class="inline-flex items-center justify-center w-20 h-20 rounded-full glass-panel mb-md shadow-sm">
          <span class="material-symbols-outlined text-primary text-[40px]">lock_reset</span>
        </div>
        <h1 class="font-display-lg text-primary mb-xs">设置新密码</h1>
        <p class="font-body-md text-on-surface-variant">请通过验证信息并创建一个安全的密码</p>
      </div>

      <!-- Reset Form Panel -->
      <div class="glass-panel p-lg rounded-[32px] shadow-[0_8px_32px_rgba(75,100,85,0.05)]">
        <form class="space-y-md" @submit.prevent="handleReset">
          <!-- Identifier Input -->
          <div class="space-y-xs">
            <label class="block font-label-bold text-on-surface-variant ml-xs">注册邮箱 / 手机号</label>
            <div class="relative flex items-center">
              <span class="material-symbols-outlined absolute left-4 text-outline">alternate_email</span>
              <input
                v-model="phone"
                type="text"
                class="w-full pl-12 pr-4 py-4 bg-white/40 border border-outline-variant/30 rounded-2xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-body-md placeholder:text-outline/50"
                placeholder="请输入手机号"
              />
            </div>
          </div>

          <!-- Verification Code -->
          <div class="space-y-xs">
            <label class="block font-label-bold text-on-surface-variant ml-xs">验证码</label>
            <div class="flex gap-sm">
              <div class="relative flex-1 flex items-center">
                <span class="material-symbols-outlined absolute left-4 text-outline">verified_user</span>
                <input
                  v-model="code"
                  type="text"
                  class="w-full pl-12 pr-4 py-4 bg-white/40 border border-outline-variant/30 rounded-2xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-body-md placeholder:text-outline/50"
                  placeholder="请输入验证码"
                />
              </div>
              <button
                type="button"
                :disabled="codeLoading || countdown > 0"
                class="px-md py-4 bg-primary-container/30 text-on-primary-container font-label-bold rounded-2xl whitespace-nowrap active:scale-95 transition-transform disabled:opacity-60"
                @click="sendCode"
              >
                {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
              </button>
            </div>
          </div>

          <!-- New Password -->
          <div class="space-y-xs">
            <label class="block font-label-bold text-on-surface-variant ml-xs">新密码</label>
            <div class="relative flex items-center">
              <span class="material-symbols-outlined absolute left-4 text-outline">key</span>
              <input
                v-model="newPassword"
                :type="showNewPassword ? 'text' : 'password'"
                class="w-full pl-12 pr-12 py-4 bg-white/40 border border-outline-variant/30 rounded-2xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-body-md placeholder:text-outline/50"
                placeholder="请输入 6 位以上字符"
              />
              <button 
                type="button" 
                class="absolute right-4 text-outline hover:text-primary transition-colors"
                @click="showNewPassword = !showNewPassword"
              >
                <span class="material-symbols-outlined">{{ showNewPassword ? 'visibility' : 'visibility_off' }}</span>
              </button>
            </div>
          </div>

          <!-- Confirm New Password -->
          <div class="space-y-xs">
            <label class="block font-label-bold text-on-surface-variant ml-xs">确认新密码</label>
            <div class="relative flex items-center">
              <span class="material-symbols-outlined absolute left-4 text-outline">verified_user</span>
              <input
                v-model="confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                class="w-full pl-12 pr-12 py-4 bg-white/40 border border-outline-variant/30 rounded-2xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-body-md placeholder:text-outline/50"
                placeholder="请再次输入新密码"
              />
              <button 
                type="button" 
                class="absolute right-4 text-outline hover:text-primary transition-colors"
                @click="showConfirmPassword = !showConfirmPassword"
              >
                <span class="material-symbols-outlined">{{ showConfirmPassword ? 'visibility' : 'visibility_off' }}</span>
              </button>
            </div>
          </div>

          <!-- Security Hint -->
          <div class="flex items-start gap-2 px-xs pt-xs">
            <span class="material-symbols-outlined text-primary text-[18px]">info</span>
            <p class="font-caption-sm text-on-surface-variant leading-tight">
              建议使用字母、数字和特殊字符的组合，以提高账户安全性。
            </p>
          </div>

          <!-- Primary Action Button -->
          <button
            type="submit"
            :disabled="loading"
            class="w-full mt-lg py-4 bg-primary text-on-primary font-title-sm rounded-full shadow-lg shadow-primary/20 hover:opacity-90 active:scale-95 transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-60"
          >
            <span>{{ loading ? '重置中...' : '重置密码' }}</span>
            <span class="material-symbols-outlined text-[20px]">arrow_forward</span>
          </button>
        </form>
      </div>

      <!-- Footer Help -->
      <footer class="mt-xl text-center">
        <p class="font-caption-sm text-on-surface-variant mb-md">遇到问题？联系 <a class="text-primary font-semibold hover:underline" href="#">客户支持</a></p>
        
        <!-- Branding Image -->
        <div class="relative w-full h-40 mt-8 rounded-[32px] overflow-hidden group">
          <img 
            class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110" 
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBOwPKakVj8-or9TFSv5n6Sw06WFE6IFqhmBEmxAeOVfbLnbt9dcH3XBLQNNcUZtjWKNIru6qgGshEcbgfpgXciCLo7y_qRf_BcwILvigpUz2JhQ8IqryZmQljddbGi90MNnDHmfk0N1a0lQha4Wuno9mocTZx-RzlIanfx-_MzKQeLwcrf-2br7JRt2mBPlLwyba-rnuijvR_d3LmWgByIUia0h2hEJZ5DmHOICtmhyMHUC-yXWnVoBXyD4HmqnK8N2Aj-lXbAf5Gd" 
          />
          <div class="absolute inset-0 bg-gradient-to-t from-primary/60 to-transparent flex items-end p-lg">
            <div class="text-left">
              <p class="text-white/70 font-label-bold uppercase tracking-widest text-[10px]">PetLumina Care</p>
              <p class="text-white font-title-sm">守护您与宠物的每一刻宁静</p>
            </div>
          </div>
        </div>
      </footer>
    </main>

    <!-- Aesthetic Floating Elements -->
    <div class="fixed top-[20%] left-[-50px] w-[200px] h-[200px] border border-primary/10 rounded-full -z-10"></div>
    <div class="fixed bottom-[10%] right-[-30px] w-[150px] h-[150px] border border-primary/10 rounded-full -z-10"></div>
  </div>
</template>
