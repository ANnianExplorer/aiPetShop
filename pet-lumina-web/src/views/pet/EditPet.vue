<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { petApi } from '@/api/pet'
import { fileApi } from '@/api/file'

const route = useRoute()
const router = useRouter()
const loading = ref(false)

const form = ref({ name: '', breed: '', type: 'dog', age: '', notes: '', avatar: '' })
const photoPreview = ref('')
const photoInputRef = ref<HTMLInputElement | null>(null)
const photoUploading = ref(false)

const typeLabel = computed(() => ({ dog: '狗狗', cat: '猫咪', other: '其他' }[form.value.type] || '-'))

const triggerPhotoUpload = () => { photoInputRef.value?.click() }

const onPhotoChange = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { ElMessage.warning('图片大小不能超过5MB'); return }
  photoPreview.value = URL.createObjectURL(file)
  photoUploading.value = true
  try {
    form.value.avatar = await fileApi.uploadImage(file, 'pet/image')
    ElMessage.success('照片上传成功')
  } catch { photoPreview.value = '' } finally { photoUploading.value = false; input.value = '' }
}

onMounted(async () => {
  loading.value = true
  try {
    const res = await petApi.getDetail(route.params.id as string) as any
    if (res) {
      form.value = { name: res.name || '', breed: res.breed || '', type: res.type || 'dog', age: res.age || '', notes: res.notes || '', avatar: res.avatar || '' }
    }
  } catch (e) { console.error(e) } finally { loading.value = false }
})

const handleSubmit = async () => {
  if (!form.value.name || !form.value.breed) { ElMessage.warning('请填写宠物名称和品种'); return }
  try {
    await petApi.edit({ id: Number(route.params.id), ...form.value })
    ElMessage.success('宠物信息已更新')
    router.push(`/pet/${route.params.id}`)
  } catch { ElMessage.error('更新失败') }
}
</script>

<template>
  <div v-loading="loading" class="space-y-6 animate-float-up">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <button class="flex items-center gap-2 px-5 py-2.5 rounded-full glass-panel text-primary text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest hover:scale-105 transition-transform group" @click="router.back()">
        <span class="material-symbols-outlined text-xl group-hover:-translate-x-1 transition-transform">arrow_back</span>
        返回详情
      </button>
    </div>

    <div class="grid grid-cols-12 gap-8">
      <!-- Left: Preview -->
      <div class="col-span-12 lg:col-span-4">
        <div class="glass-panel-deep rounded-[32px] overflow-hidden depth-3 sticky top-24">
          <div class="h-48 relative overflow-hidden">
            <img v-if="photoPreview || form.avatar" :src="photoPreview || form.avatar" class="w-full h-full object-cover" />
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
          <h2 class="font-[Plus_Jakarta_Sans] text-2xl font-bold text-primary mb-2">编辑宠物信息</h2>
          <p class="text-sm text-on-surface-variant mb-8">修改宠物的基本资料与健康档案</p>

          <form class="space-y-8" @submit.prevent="handleSubmit">
            <!-- Photo -->
            <div class="flex items-center gap-6">
              <input ref="photoInputRef" type="file" accept="image/jpeg,image/png,image/gif,image/webp" class="hidden" @change="onPhotoChange" />
              <div class="relative group cursor-pointer" @click="triggerPhotoUpload">
                <div class="w-24 h-24 rounded-2xl overflow-hidden glass-panel border-2 border-white/40">
                  <img v-if="photoPreview || form.avatar" :src="photoPreview || form.avatar" class="w-full h-full object-cover" />
                  <div v-else class="w-full h-full flex items-center justify-center"><span class="material-symbols-outlined text-3xl text-on-surface-variant/50">add_a_photo</span></div>
                </div>
                <div class="absolute -bottom-1 -right-1 w-7 h-7 bg-primary rounded-full flex items-center justify-center shadow-md">
                  <span class="material-symbols-outlined text-white text-sm">edit</span>
                </div>
              </div>
              <div>
                <p class="text-sm font-bold text-on-surface">更换宠物照片</p>
                <p class="text-xs text-slate-400">支持 JPG, PNG, WebP (最大 5MB)</p>
                <p v-if="photoUploading" class="text-xs text-primary mt-1">上传中...</p>
              </div>
            </div>

            <!-- Basic Info -->
            <div>
              <div class="flex items-center gap-2 mb-4">
                <span class="material-symbols-outlined text-primary text-lg">pets</span>
                <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface">基本信息</h3>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">宠物名称 *</label>
                  <div class="relative">
                    <span class="absolute left-4 top-1/2 -translate-y-1/2 material-symbols-outlined text-slate-400">pets</span>
                    <input v-model="form.name" class="glass-input w-full pl-12 pr-4 py-3 rounded-xl text-sm" />
                  </div>
                </div>
                <div class="space-y-2">
                  <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">品种 *</label>
                  <input v-model="form.breed" class="glass-input w-full rounded-xl px-4 py-3 text-sm" />
                </div>
                <div class="space-y-2">
                  <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">年龄</label>
                  <input v-model="form.age" class="glass-input w-full rounded-xl px-4 py-3 text-sm" placeholder="例如：3岁" />
                </div>
                <div class="space-y-2">
                  <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">宠物类型</label>
                  <div class="flex p-1 bg-white/20 rounded-xl border border-white/10">
                    <label class="flex-1"><input v-model="form.type" value="dog" class="hidden peer" type="radio" name="type" /><div class="text-center py-2.5 rounded-lg cursor-pointer transition-all peer-checked:bg-primary-container peer-checked:text-white text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant">狗狗</div></label>
                    <label class="flex-1"><input v-model="form.type" value="cat" class="hidden peer" type="radio" name="type" /><div class="text-center py-2.5 rounded-lg cursor-pointer transition-all peer-checked:bg-primary-container peer-checked:text-white text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant">猫咪</div></label>
                    <label class="flex-1"><input v-model="form.type" value="other" class="hidden peer" type="radio" name="type" /><div class="text-center py-2.5 rounded-lg cursor-pointer transition-all peer-checked:bg-primary-container peer-checked:text-white text-xs font-[Plus_Jakarta_Sans] font-semibold text-on-surface-variant">其他</div></label>
                  </div>
                </div>
              </div>
            </div>

            <!-- Health Notes -->
            <div>
              <div class="flex items-center gap-2 mb-4">
                <span class="material-symbols-outlined text-primary text-lg">medical_information</span>
                <h3 class="font-[Plus_Jakarta_Sans] font-bold text-on-surface">健康档案</h3>
              </div>
              <div class="space-y-2">
                <label class="text-xs text-on-surface-variant font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest">健康状况描述</label>
                <textarea v-model="form.notes" class="glass-input w-full rounded-xl px-4 py-3 text-sm resize-none" rows="4" placeholder="描述过敏、近期疫苗接种、特殊护理需求等..." />
              </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center justify-end gap-4 pt-4">
              <button class="px-8 py-3 rounded-xl text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest text-on-surface-variant hover:bg-white/30 transition-all" type="button" @click="router.back()">取消</button>
              <button class="px-10 py-3 bg-primary text-white rounded-xl text-xs font-[Plus_Jakarta_Sans] font-semibold uppercase tracking-widest shadow-[0_10px_20px_-5px_rgba(38,106,81,0.4)] hover:scale-105 active:scale-95 transition-all duration-300 flex items-center gap-2 btn-jelly" type="submit">
                <span class="material-symbols-outlined text-lg">save</span>
                保存修改
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
