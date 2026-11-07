<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fileApi } from '@/api/file'
import { userApi } from '@/api/user'

const router = useRouter()
const form = ref({
  nickname: '',
  role: 'user' as 'user' | 'admin',
  phone: '',
  email: '',
  password: '',
})
const showPassword = ref(false)
const avatarPreview = ref('')
const avatarUrl = ref('')
const avatarInputRef = ref<HTMLInputElement | null>(null)
const avatarUploading = ref(false)
const submitting = ref(false)

const passwordStrength = ref(0)
const passwordLabel = ref('')
const passwordColors = ref<string[]>([])

const checkPasswordStrength = () => {
  const p = form.value.password
  let score = 0
  if (p.length >= 6) score++
  if (p.length >= 8) score++
  if (/[a-zA-Z]/.test(p) && /[0-9]/.test(p)) score++
  if (/[^a-zA-Z0-9]/.test(p)) score++
  passwordStrength.value = score
  const labels = ['', '弱', '中', '强', '极强']
  const colors = ['', 'bg-error', 'bg-amber-500', 'bg-primary-container', 'bg-primary']
  passwordLabel.value = labels[score]
  passwordColors.value = colors.slice(1, score + 1)
}

const handleAvatarUpload = () => {
  avatarInputRef.value?.click()
}

const onAvatarChange = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { ElMessage.warning('图片大小不能超过5MB'); return }
  avatarPreview.value = URL.createObjectURL(file)
  avatarUploading.value = true
  try {
    avatarUrl.value = await fileApi.uploadImage(file)
    ElMessage.success('头像上传成功')
  } catch { avatarPreview.value = '' } finally { avatarUploading.value = false; input.value = '' }
}

const handleSubmit = async () => {
  if (!form.value.phone) {
    ElMessage.warning('请填写手机号')
    return
  }
  if (!/^1\d{10}$/.test(form.value.phone)) {
    ElMessage.warning('手机号格式不正确')
    return
  }
  if (!form.value.password || form.value.password.length < 6) {
    ElMessage.warning('初始密码至少 6 位')
    return
  }
  submitting.value = true
  try {
    const id = await userApi.add({
      phone: form.value.phone.trim(),
      password: form.value.password,
      nickname: form.value.nickname.trim() || undefined,
      email: form.value.email.trim() || undefined,
      avatar: avatarUrl.value || undefined,
      role: form.value.role,
      status: 1,
    })
    ElMessage.success(`用户创建成功（ID ${id}）`)
    router.push('/user')
  } catch (e: any) {
    ElMessage.error(e?.message || '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleReset = () => {
  form.value = { nickname: '', role: 'user', phone: '', email: '', password: '' }
  passwordStrength.value = 0
}
</script>

<template>
  <div class="space-y-8">
    <!-- Back Button -->
    <div class="animate-float-up">
      <button
        class="inline-flex items-center gap-2 px-5 py-2.5 rounded-full glass-panel text-primary font-[Plus_Jakarta_Sans] text-xs font-semibold uppercase tracking-widest hover:scale-105 transition-transform duration-300"
        @click="router.push('/user')"
      >
        <span class="material-symbols-outlined text-lg">arrow_back</span>
        返回用户列表
      </button>
    </div>

    <!-- Form Section -->
    <div class="max-w-4xl mx-auto animate-float-up stagger-1">
      <div class="glass-panel-deep rounded-[32px] overflow-hidden depth-3">
        <!-- Form Header -->
        <div class="px-10 py-8 border-b border-white/10">
          <h1 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-on-surface tracking-tight">新增系统用户</h1>
          <p class="text-sm text-on-surface-variant mt-1">请填写以下信息以创建新的 PetLumina 管理平台账户</p>
        </div>

        <!-- Form Content -->
        <form class="p-10" @submit.prevent="handleSubmit">
          <div class="grid grid-cols-12 gap-10">
            <!-- Avatar Upload Side -->
            <div class="col-span-12 lg:col-span-4 flex flex-col items-center">
              <input ref="avatarInputRef" type="file" accept="image/jpeg,image/png,image/gif,image/webp" class="hidden" @change="onAvatarChange" />
              <div class="relative group cursor-pointer" @click="handleAvatarUpload">
                <div class="w-48 h-48 rounded-3xl overflow-hidden glass-panel border-2 border-white/40 flex items-center justify-center transition-all duration-500 group-hover:border-primary-container/60 group-hover:shadow-[0_0_30px_rgba(109,175,146,0.2)]">
                  <div v-if="!avatarPreview" class="w-full h-full bg-gradient-to-br from-primary-container/20 to-primary/10 flex items-center justify-center">
                    <span class="material-symbols-outlined text-white/30" style="font-size: 80px">person</span>
                  </div>
                  <img v-else :src="avatarPreview" class="w-full h-full object-cover" />
                  <div class="absolute inset-0 bg-black/20 opacity-0 group-hover:opacity-100 flex flex-col items-center justify-center text-white transition-all">
                    <span class="material-symbols-outlined text-3xl">add_a_photo</span>
                    <span class="text-xs font-bold mt-2">上传头像</span>
                  </div>
                </div>
                <div class="absolute -bottom-3 -right-3 w-12 h-12 bg-primary rounded-2xl flex items-center justify-center shadow-lg text-white btn-jelly">
                  <span class="material-symbols-outlined">edit</span>
                </div>
              </div>
              <p class="text-sm text-slate-500 mt-6 text-center px-4 leading-relaxed">
                支持 JPG, PNG 格式<br />建议尺寸 512x512px
              </p>
            </div>

            <!-- Main Form Fields -->
            <div class="col-span-12 lg:col-span-8 flex flex-col gap-8">
              <div class="grid grid-cols-2 gap-6">
                <!-- Username -->
                <div class="col-span-2 sm:col-span-1">
                  <label class="text-xs text-slate-600 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-2 block">昵称</label>
                  <input v-model="form.nickname" class="glass-input w-full px-5 py-4 rounded-2xl text-sm" placeholder="例如：森林语者（留空自动生成）" type="text" />
                </div>
                <!-- User Role -->
                <div class="col-span-2 sm:col-span-1">
                  <label class="text-xs text-slate-600 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-2 block">系统角色</label>
                  <el-select v-model="form.role" style="width: 100%">
                    <el-option label="普通用户" value="user" />
                    <el-option label="系统管理员" value="admin" />
                  </el-select>
                </div>
                <!-- Phone -->
                <div class="col-span-2 sm:col-span-1">
                  <label class="text-xs text-slate-600 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-2 block">手机号</label>
                  <input v-model="form.phone" class="glass-input w-full px-5 py-4 rounded-2xl text-sm" placeholder="请输入11位手机号码" type="tel" />
                </div>
                <!-- Email -->
                <div class="col-span-2 sm:col-span-1">
                  <label class="text-xs text-slate-600 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-2 block">电子邮箱</label>
                  <input v-model="form.email" class="glass-input w-full px-5 py-4 rounded-2xl text-sm" placeholder="example@petlumina.com" type="email" />
                </div>
                <!-- Password -->
                <div class="col-span-2">
                  <label class="text-xs text-slate-600 font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-2 block">初始密码设置</label>
                  <div class="relative">
                    <input
                      v-model="form.password"
                      class="glass-input w-full px-5 py-4 rounded-2xl text-sm pr-12"
                      placeholder="输入至少8位包含字母和数字的密码"
                      :type="showPassword ? 'text' : 'password'"
                      @input="checkPasswordStrength"
                    />
                    <button
                      class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-primary transition-colors"
                      type="button"
                      @click="showPassword = !showPassword"
                    >
                      <span class="material-symbols-outlined">{{ showPassword ? 'visibility_off' : 'visibility' }}</span>
                    </button>
                  </div>
                  <div v-if="form.password" class="mt-3 flex items-center gap-1">
                    <div
                      v-for="i in 4"
                      :key="i"
                      class="h-1 flex-1 rounded-full"
                      :class="i <= passwordStrength ? passwordColors[i - 1] : 'bg-white/20'"
                    />
                    <span class="text-[10px] font-bold text-primary ml-2 uppercase">{{ passwordLabel }}密码</span>
                  </div>
                </div>
              </div>

              <!-- Form Actions -->
              <div class="mt-4 pt-8 border-t border-white/10 flex justify-end gap-4">
                <button
                  class="px-8 py-3.5 rounded-2xl glass-panel text-on-surface text-xs font-semibold uppercase tracking-widest hover:bg-white/50 transition-all duration-300"
                  type="button"
                  @click="handleReset"
                >
                  重置表单
                </button>
                <button
                  class="px-10 py-3.5 rounded-2xl bg-primary-container text-white text-xs font-semibold uppercase tracking-widest shadow-[0_10px_25px_-5px_rgba(109,175,146,0.4)] hover:shadow-[0_15px_30px_-5px_rgba(109,175,146,0.6)] hover:scale-[1.02] active:scale-95 transition-all duration-300 btn-jelly disabled:opacity-60 disabled:cursor-not-allowed"
                  type="submit"
                  :disabled="submitting"
                >
                  {{ submitting ? '创建中…' : '创建用户账号' }}
                </button>
              </div>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
