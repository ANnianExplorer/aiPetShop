<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fileApi } from '@/api/file'

const router = useRouter()
const form = ref({
  name: '',
  breed: '',
  age: '',
  gender: 'male',
  ownerSearch: '',
  healthNote: '',
})
const photoPreview = ref('')
const photoUrl = ref('')
const photoInputRef = ref<HTMLInputElement | null>(null)
const photoUploading = ref(false)

const triggerPhotoUpload = () => {
  photoInputRef.value?.click()
}

const onPhotoChange = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { ElMessage.warning('图片大小不能超过5MB'); return }
  photoPreview.value = URL.createObjectURL(file)
  photoUploading.value = true
  try {
    photoUrl.value = await fileApi.uploadImage(file, 'pet/image')
    ElMessage.success('照片上传成功')
  } catch { photoPreview.value = '' } finally { photoUploading.value = false; input.value = '' }
}

const handleSubmit = () => {
  if (!form.value.name || !form.value.breed) {
    ElMessage.warning('请填写宠物名称和品种')
    return
  }
  ElMessage.success('宠物添加成功')
  router.push('/pet')
}

const handleReset = () => {
  form.value = { name: '', breed: '', age: '', gender: 'male', ownerSearch: '', healthNote: '' }
  photoPreview.value = ''
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-120px)] animate-float-up">
    <div class="w-full max-w-5xl glass-panel-deep rounded-[32px] overflow-hidden depth-3 flex flex-col md:flex-row">
      <!-- Left Side: Visual/Context -->
      <div class="w-full md:w-2/5 p-12 bg-primary-container/10 flex flex-col justify-between border-b md:border-b-0 md:border-r border-white/20">
        <div>
          <button
            class="group flex items-center gap-2 text-primary text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest mb-12 hover:opacity-70 transition-opacity"
            @click="router.push('/pet')"
          >
            <span class="material-symbols-outlined">arrow_back</span>
            <span>返回列表</span>
          </button>
          <h1 class="font-[Plus_Jakarta_Sans] text-[40px] font-bold text-on-primary-container mb-4 leading-tight">添加宠物</h1>
          <p class="text-lg text-on-surface-variant leading-relaxed">为您生命中的重要伙伴建立专属的健康与生活档案。</p>
        </div>

        <!-- Photo Upload -->
        <input ref="photoInputRef" type="file" accept="image/jpeg,image/png,image/gif,image/webp" class="hidden" @change="onPhotoChange" />
        <div class="relative group mt-12" @click="triggerPhotoUpload">
          <div
            class="aspect-square w-full rounded-3xl overflow-hidden glass-panel border-2 border-white/40 flex flex-col items-center justify-center cursor-pointer hover:border-primary-container transition-all"
          >
            <div v-if="!photoPreview" class="absolute inset-0 bg-gradient-to-br from-primary-container/20 to-primary/10" />
            <img v-else :src="photoPreview" class="absolute inset-0 w-full h-full object-cover opacity-60 group-hover:opacity-80 transition-opacity" />
            <div class="relative z-10 flex flex-col items-center">
              <div class="w-16 h-16 rounded-full bg-primary-container text-white flex items-center justify-center mb-4 shadow-lg group-hover:scale-110 transition-transform">
                <span class="material-symbols-outlined text-3xl">add_a_photo</span>
              </div>
              <span class="text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-primary-container uppercase tracking-widest">上传照片</span>
              <span class="text-[10px] text-on-surface-variant/70 mt-1">支持 JPG, PNG (Max 5MB)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Side: Form Fields -->
      <div class="w-full md:w-3/5 p-12 overflow-y-auto">
        <form class="space-y-6" @submit.prevent="handleSubmit">
          <!-- Basic Info Grid -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">宠物名称</label>
              <input v-model="form.name" class="glass-input w-full rounded-xl px-4 py-3 text-sm" placeholder="例如：奥利奥" type="text" />
            </div>
            <div class="space-y-2">
              <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">品种</label>
              <el-select v-model="form.breed" placeholder="选择品种" style="width: 100%">
                <el-option label="拉布拉多" value="拉布拉多" />
                <el-option label="金毛寻回犬" value="金毛寻回犬" />
                <el-option label="布偶猫" value="布偶猫" />
                <el-option label="英短蓝猫" value="英短蓝猫" />
                <el-option label="哈士奇" value="哈士奇" />
                <el-option label="其他" value="其他" />
              </el-select>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-2">
              <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">年龄</label>
              <input v-model="form.age" class="glass-input w-full rounded-xl px-4 py-3 text-sm" placeholder="岁" type="number" />
            </div>
            <div class="space-y-2">
              <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">性别</label>
              <div class="flex p-1 bg-white/20 rounded-xl border border-white/10">
                <label class="flex-1">
                  <input v-model="form.gender" value="male" class="hidden peer" type="radio" name="gender" />
                  <div class="text-center py-2 rounded-lg cursor-pointer transition-all peer-checked:bg-primary-container peer-checked:text-white text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant">
                    雄性
                  </div>
                </label>
                <label class="flex-1">
                  <input v-model="form.gender" value="female" class="hidden peer" type="radio" name="gender" />
                  <div class="text-center py-2 rounded-lg cursor-pointer transition-all peer-checked:bg-primary-container peer-checked:text-white text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant">
                    雌性
                  </div>
                </label>
              </div>
            </div>
          </div>

          <!-- Owner Search -->
          <div class="space-y-2">
            <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">关联主人</label>
            <div class="relative">
              <span class="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
              <input v-model="form.ownerSearch" class="glass-input w-full rounded-xl pl-12 pr-4 py-3 text-sm" placeholder="输入用户名或手机号搜索..." type="text" />
            </div>
          </div>

          <!-- Health Status -->
          <div class="space-y-2">
            <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest ml-1">健康状况描述</label>
            <textarea v-model="form.healthNote" class="glass-input w-full rounded-xl px-4 py-3 text-sm resize-none" placeholder="描述过敏、近期疫苗接种或特别护理需求..." rows="4" />
          </div>

          <!-- Action Buttons -->
          <div class="pt-8 flex gap-4">
            <button
              class="flex-1 bg-primary text-white text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest py-4 rounded-xl shadow-[0_8px_20px_-4px_rgba(38,106,81,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-300 btn-jelly"
              type="submit"
            >
              确认添加宠物
            </button>
            <button
              class="px-8 glass-input text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest text-on-surface-variant py-4 rounded-xl hover:bg-white/40 transition-colors"
              type="button"
              @click="handleReset"
            >
              重置
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
