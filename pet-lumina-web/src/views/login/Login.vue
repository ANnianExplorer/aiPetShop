<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/admin'
import { ElMessage } from 'element-plus'

const router = useRouter()
const adminStore = useAdminStore()

const phone = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!phone.value || !password.value) {
    ElMessage.warning('请输入手机号和密码')
    return
  }
  loading.value = true
  try {
    await adminStore.login(phone.value, password.value)
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch (e) {
    ElMessage.error('登录失败，请检查手机号和密码')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-8">
    <!-- Login Card -->
    <div class="w-full max-w-md">
      <div class="glass-panel rounded-[32px] overflow-hidden shadow-2xl p-10">
        <!-- Header -->
        <div class="text-center mb-10">
          <div class="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-primary-container/20 mb-6">
            <span class="material-symbols-outlined text-4xl text-primary-container" style="font-variation-settings: 'FILL' 1;">pets</span>
          </div>
          <h1 class="font-[Plus_Jakarta_Sans] text-3xl font-bold text-on-surface tracking-tight">PetLumina</h1>
          <p class="text-on-surface-variant text-sm mt-2">管理后台 · Management Portal</p>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleLogin" class="space-y-6">
          <div>
            <label class="font-[Plus_Jakarta_Sans] text-xs font-semibold text-slate-600 mb-2 block uppercase tracking-wider">手机号</label>
            <div class="relative">
              <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-lg">phone</span>
              <input
                v-model="phone"
                type="tel"
                placeholder="请输入手机号"
                class="w-full pl-12 pr-4 py-4 rounded-2xl bg-white/15 backdrop-blur-[10px] border border-white/30 text-on-surface placeholder-slate-400 focus:border-primary-container focus:ring-2 focus:ring-primary-container/30 outline-none transition-all"
              />
            </div>
          </div>

          <div>
            <label class="font-[Plus_Jakarta_Sans] text-xs font-semibold text-slate-600 mb-2 block uppercase tracking-wider">密码</label>
            <div class="relative">
              <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 text-lg">lock</span>
              <input
                v-model="password"
                type="password"
                placeholder="请输入密码"
                @keyup.enter="handleLogin"
                class="w-full pl-12 pr-12 py-4 rounded-2xl bg-white/15 backdrop-blur-[10px] border border-white/30 text-on-surface placeholder-slate-400 focus:border-primary-container focus:ring-2 focus:ring-primary-container/30 outline-none transition-all"
              />
            </div>
          </div>

          <div class="flex justify-end">
            <a href="#" class="text-sm text-primary-container hover:text-primary font-medium transition-colors">忘记密码?</a>
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="w-full py-4 rounded-2xl bg-primary-container text-white font-[Plus_Jakarta_Sans] font-bold text-sm shadow-[0_10px_25px_-5px_rgba(109,175,146,0.4)] hover:shadow-[0_15px_30px_-5px_rgba(109,175,146,0.6)] hover:scale-[1.02] active:scale-95 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span v-if="loading" class="material-symbols-outlined animate-spin text-lg mr-2">refresh</span>
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>

        <!-- Footer -->
        <div class="mt-8 pt-6 border-t border-white/10 text-center">
          <p class="text-xs text-slate-500">PetLumina 宠物生活管理平台 &copy; 2026</p>
        </div>
      </div>
    </div>
  </div>
</template>
