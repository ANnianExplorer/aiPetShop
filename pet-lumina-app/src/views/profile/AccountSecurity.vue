<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { showToast } = useToast()

const goBack = () => {
  router.back()
}

const phone = ref('138****8888')
const email = ref('user@example.com')
const showPassword = ref(false)
const newPassword = ref('')
const confirmPassword = ref('')

const handleChangePassword = () => {
  if (!newPassword.value || !confirmPassword.value) {
    showToast('请填写密码', 'error')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    showToast('两次密码输入不一致', 'error')
    return
  }
  showToast('密码修改成功', 'success')
  newPassword.value = ''
  confirmPassword.value = ''
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex items-center justify-between py-md mb-lg">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">账号与安全</span>
        <div class="w-10"></div>
      </div>

      <section class="space-y-4 mb-lg">
        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">绑定信息</h3>
          <div class="space-y-3">
            <div class="flex justify-between items-center">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-on-surface-variant">phone</span>
                <span class="text-sm text-on-surface">手机号</span>
              </div>
              <span class="text-sm text-on-surface-variant">{{ phone }}</span>
            </div>
            <div class="flex justify-between items-center">
              <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-on-surface-variant">mail</span>
                <span class="text-sm text-on-surface">邮箱</span>
              </div>
              <span class="text-sm text-on-surface-variant">{{ email }}</span>
            </div>
          </div>
        </div>

        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">修改密码</h3>
          <div class="space-y-3">
            <div>
              <label class="font-label-bold text-label-bold text-on-surface mb-2 block">新密码</label>
              <input 
                v-model="newPassword" 
                type="password"
                placeholder="请输入新密码" 
                class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
              />
            </div>
            <div>
              <label class="font-label-bold text-label-bold text-on-surface mb-2 block">确认密码</label>
              <input 
                v-model="confirmPassword" 
                type="password"
                placeholder="请再次输入新密码" 
                class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
              />
            </div>
            <button 
              @click="handleChangePassword" 
              class="w-full py-3 bg-primary text-on-primary rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform"
            >
              修改密码
            </button>
          </div>
        </div>

        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">登录设备</h3>
          <div class="flex items-center justify-between py-2">
            <div class="flex items-center gap-3">
              <span class="material-symbols-outlined text-on-surface-variant">phone_iphone</span>
              <div>
                <p class="text-sm text-on-surface">当前设备</p>
                <p class="text-xs text-tertiary">iPhone 15 Pro</p>
              </div>
            </div>
            <span class="text-xs text-emerald-500 font-label-bold">在线</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
