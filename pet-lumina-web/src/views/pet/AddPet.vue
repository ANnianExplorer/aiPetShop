<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { fileApi } from '@/api/file'
import { petApi } from '@/api/pet'

const router = useRouter()
const form = ref({
  name: '',
  breed: '',
  type: 'dog',
  age: '',
  notes: '',
})
const photoPreview = ref('')
const photoUrl = ref('')
const photoInputRef = ref<HTMLInputElement | null>(null)
const photoUploading = ref(false)
const submitting = ref(false)

const typeLabel = computed(() => ({ dog: '狗狗', cat: '猫咪', other: '其他' }[form.value.type] || '未选择'))

const triggerPhotoUpload = () => { photoInputRef.value?.click() }

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

const handleSubmit = async () => {
  if (!form.value.name || !form.value.breed) { ElMessage.warning('请填写宠物名称和品种'); return }
  submitting.value = true
  try {
    await petApi.add({ ...form.value, avatar: photoUrl.value || undefined })
    ElMessage.success('宠物添加成功')
    router.push('/pet')
  } catch { ElMessage.error('添加失败') } finally { submitting.value = false }
}

const handleReset = () => {
  form.value = { name: '', breed: '', type: 'dog', age: '', notes: '' }
  photoPreview.value = ''
  photoUrl.value = ''
}
</script>

<template>
  <div class="space-y-6 animate-float-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <button class="flex items-center gap-2 px-5 py-2.5 rounded-full glass-panel text-primary text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest hover:scale-105 transition-transform group" @click="router.push('/pet')">
        <span class="material-symbols-outlined text-xl group-hover:-translate-x-1 transition-transform">arrow_back</span>
        返回列表
      </button>
    </div>

    <div class="grid grid-cols-12 gap-8">
      <!-- Left: Preview Card -->
      <div class="col-span-12 lg:col-span-4">
        <div class="glass-panel-deep rounded-[32px] overflow-hidden depth-3 sticky top-24">
          <div class="h-48 relative overflow-hidden">
            <img v-if="photoPreview" :src="photoPreview" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full bg-gradient-to-br from-primary-container/30 to-primary/10 flex items-center justify-center">
              <span class="material-symbols-outlined text-white/20" style="font-size: 80px">pets</span>
            </div>
            <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
            <div class="absolute bottom-4 left-4 text-white">
              <h3 class="font-[Plus_Jakarta_Sans] text-xl font-bold drop-shadow-lg">{{ form.name || '宠物名称' }}</h3>
              <p class="text-white/80 text-sm">{{ form.breed || '品种' }} · {{ typeLabel }}</p>
            </div>
          </div>
          <div class="p-6 space-y-3">
            <div class="flex justify-between text-sm">
              <span class="text-slate-500">年龄</span>
              <span class="font-bold text-on-surface">{{ form.age || '-' }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-slate-500">类型</span>
              <span class="font-bold text-on-surface">{{ typeLabel }}</span>
            </div>
            <div class="pt-3 border-t border-white/20">
              <p class="text-xs text-slate-400">备注</p>
              <p class="text-sm text-on-surface-variant mt-1">{{ form.notes || '暂无备注' }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Form -->
      <div class="col-span-12 lg:col-span-8">
        <div class="glass-panel-deep rounded-[32px] p-10 depth-2">
          <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-primary mb-2">添加宠物</h2>
          <p class="text-sm text-on-surface-variant mb-8">为您生命中的重要伙伴建立专属的健康与生活档案</p>

          <form class="space-y-8" @submit.prevent="handleSubmit">
            <!-- Photo Upload -->
            <div class="flex items-center gap-6">
              <input ref="photoInputRef" type="file" accept="image/jpeg,image/png,image/gif,image/webp" class="hidden" @change="onPhotoChange" />
              <div class="relative group cursor-pointer" @click="triggerPhotoUpload">
                <div class="w-24 h-24 rounded-2xl overflow-hidden glass-panel border-2 border-white/40 flex items-center justify-center">
                  <img v-if="photoPreview" :src="photoPreview" class="w-full h-full object-cover" />
                  <span v-else class="material-symbols-outlined text-3xl text-on-surface-variant/50">add_a_photo</span>
                </div>
                <div class="absolute -bottom-1 -right-1 w-7 h-7 bg-primary rounded-full flex items-center justify-center shadow-md">
                  <span class="material-symbols-outlined text-white text-sm">edit</span>
                </div>
              </div>
              <div>
                <p class="text-sm font-bold text-on-surface">上传宠物照片</p>
                <p class="text-xs text-slate-400">支持 JPG, PNG, WebP (最大 5MB)</p>
                <p v-if="photoUploading" class="text-xs text-primary mt-1">上传中...</p>
              </div>
            </div>

            <!-- Section: Basic Info -->
            <div>
              <div class="flex items-center gap-2 mb-4">
                <span class="material-symbols-outlined text-primary text-lg">pets</span>
                <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface">基本信息</h3>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">宠物名称 *</label>
                  <input v-model="form.name" class="glass-input w-full rounded-xl px-4 py-3 text-sm" placeholder="例如：奥利奥" />
                </div>
                <div class="space-y-2">
                  <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">品种 *</label>
                  <input v-model="form.breed" class="glass-input w-full rounded-xl px-4 py-3 text-sm" placeholder="例如：金毛寻回犬" />
                </div>
                <div class="space-y-2">
                  <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">年龄</label>
                  <input v-model="form.age" class="glass-input w-full rounded-xl px-4 py-3 text-sm" placeholder="例如：3岁" />
                </div>
                <div class="space-y-2">
                  <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">宠物类型</label>
                  <div class="flex p-1 bg-white/20 rounded-xl border border-white/10">
                    <label class="flex-1">
                      <input v-model="form.type" value="dog" class="hidden peer" type="radio" name="type" />
                      <div class="text-center py-2.5 rounded-lg cursor-pointer transition-all peer-checked:bg-primary-container peer-checked:text-white text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant">狗狗</div>
                    </label>
                    <label class="flex-1">
                      <input v-model="form.type" value="cat" class="hidden peer" type="radio" name="type" />
                      <div class="text-center py-2.5 rounded-lg cursor-pointer transition-all peer-checked:bg-primary-container peer-checked:text-white text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant">猫咪</div>
                    </label>
                    <label class="flex-1">
                      <input v-model="form.type" value="other" class="hidden peer" type="radio" name="type" />
                      <div class="text-center py-2.5 rounded-lg cursor-pointer transition-all peer-checked:bg-primary-container peer-checked:text-white text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant">其他</div>
                    </label>
                  </div>
                </div>
              </div>
            </div>

            <!-- Section: Health Notes -->
            <div>
              <div class="flex items-center gap-2 mb-4">
                <span class="material-symbols-outlined text-primary text-lg">medical_information</span>
                <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface">健康档案</h3>
              </div>
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">健康状况描述</label>
                <textarea v-model="form.notes" class="glass-input w-full rounded-xl px-4 py-3 text-sm resize-none" placeholder="描述过敏、近期疫苗接种、特殊护理需求等..." rows="4" />
              </div>
            </div>

            <!-- Actions -->
            <div class="flex gap-4 pt-4">
              <button class="flex-1 bg-primary text-white text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest py-4 rounded-xl shadow-[0_8px_20px_-4px_rgba(38,106,81,0.4)] hover:scale-[1.02] active:scale-95 transition-all duration-300 btn-jelly disabled:opacity-50" type="submit" :disabled="submitting || photoUploading">
                {{ submitting ? '添加中...' : '确认添加宠物' }}
              </button>
              <button class="px-8 glass-input text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest text-on-surface-variant py-4 rounded-xl hover:bg-white/40 transition-colors" type="button" @click="handleReset">
                重置
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
