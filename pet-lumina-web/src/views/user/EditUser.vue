<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

const form = ref({
  username: '森林语者',
  phone: '138-xxxx-8888',
  status: true,
})

const avatarUrl = ref('')

onMounted(async () => {
  loading.value = true
  try { /* const res = await userApi.getDetail(route.params.id) */ } catch (e) { console.error(e) } finally { loading.value = false }
})

const handleSubmit = () => {
  if (!form.value.username || !form.value.phone) {
    ElMessage.warning('请填写必填项')
    return
  }
  ElMessage.success('用户信息已更新')
  router.push('/user')
}
</script>

<template>
  <div class="space-y-8 animate-float-up">
    <!-- Back Button -->
    <div class="flex items-center justify-between">
      <button
        class="flex items-center gap-2 px-5 py-2.5 rounded-full glass-panel text-primary text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest hover:scale-105 transition-transform duration-300 group"
        @click="router.push('/user')"
      >
        <span class="material-symbols-outlined text-xl group-hover:-translate-x-1 transition-transform">arrow_back</span>
        返回列表
      </button>
    </div>

    <!-- Edit Form -->
    <div class="flex items-start justify-center pt-8">
      <section class="glass-panel-deep w-full max-w-2xl rounded-3xl p-10 depth-3 relative overflow-hidden">
        <!-- Decorative Background -->
        <div class="absolute -top-24 -right-24 w-64 h-64 bg-primary-container/10 rounded-full blur-3xl" />

        <div class="relative z-10">
          <!-- Title -->
          <div class="mb-10 text-center">
            <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-primary mb-2">编辑用户信息</h2>
            <p class="text-sm text-on-surface-variant">管理用户权限、个人资料及账户状态</p>
          </div>

          <form class="space-y-8" @submit.prevent="handleSubmit">
            <!-- Avatar Section -->
            <div class="flex flex-col items-center gap-4 mb-10">
              <div class="relative group">
                <div class="w-32 h-32 rounded-full border-4 border-white/50 shadow-xl overflow-hidden glass-panel">
                  <div v-if="!avatarUrl" class="w-full h-full bg-gradient-to-br from-primary-container to-primary flex items-center justify-center text-white text-4xl font-bold font-[Plus_Jakarta_Sans]">
                    {{ form.username.charAt(0) }}
                  </div>
                  <img v-else :src="avatarUrl" class="w-full h-full object-cover" />
                </div>
                <label class="absolute bottom-0 right-0 w-10 h-10 bg-primary text-white rounded-full flex items-center justify-center cursor-pointer shadow-lg hover:scale-110 transition-transform">
                  <span class="material-symbols-outlined text-xl">photo_camera</span>
                  <input class="hidden" type="file" />
                </label>
              </div>
              <span class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-primary">点击图标修改头像</span>
            </div>

            <!-- Input Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">用户名</label>
                <div class="relative">
                  <span class="absolute left-4 top-1/2 -translate-y-1/2 material-symbols-outlined text-slate-400">person</span>
                  <input v-model="form.username" class="glass-input w-full pl-12 pr-4 py-3 rounded-xl text-sm" type="text" />
                </div>
              </div>
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">手机号</label>
                <div class="relative">
                  <span class="absolute left-4 top-1/2 -translate-y-1/2 material-symbols-outlined text-slate-400">smartphone</span>
                  <input v-model="form.phone" class="glass-input w-full pl-12 pr-4 py-3 rounded-xl text-sm" type="tel" />
                </div>
              </div>
            </div>

            <!-- Status Toggle -->
            <div class="glass-panel p-6 rounded-2xl flex items-center justify-between border-white/10 bg-white/10">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-secondary-container/30 flex items-center justify-center">
                  <span class="material-symbols-outlined text-secondary glow-icon">verified_user</span>
                </div>
                <div>
                  <p class="font-bold text-on-surface">账户状态</p>
                  <p class="text-xs text-on-surface-variant">切换用户访问系统的权限</p>
                </div>
              </div>
              <div class="flex items-center gap-3">
                <span class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-slate-500">禁用</span>
                <el-switch v-model="form.status" active-color="#6daf92" />
                <span class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-primary font-bold">正常</span>
              </div>
            </div>

            <!-- Form Actions -->
            <div class="flex items-center justify-end gap-4 pt-6">
              <button
                class="px-8 py-3 rounded-xl text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest text-on-surface-variant hover:bg-white/30 transition-all"
                type="button"
                @click="router.push('/user')"
              >
                取消
              </button>
              <button
                class="px-10 py-3 bg-primary text-white rounded-xl text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest shadow-[0_10px_20px_-5px_rgba(38,106,81,0.4)] hover:scale-105 active:scale-95 transition-all duration-300 flex items-center gap-2 btn-jelly"
                type="submit"
              >
                <span class="material-symbols-outlined text-lg">save</span>
                保存修改
              </button>
            </div>
          </form>
        </div>
      </section>
    </div>
  </div>
</template>
