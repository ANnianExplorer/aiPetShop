<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { topicApi } from '@/api/topic'
import { fileApi } from '@/api/file'

const router = useRouter()
const { showToast } = useToast()

const form = ref({
  title: '',
  description: '',
  image: '',
  category: '综合'
})

const loading = ref(false)
const uploading = ref(false)
const categoryOptions = ['综合', '健康', '日常', '指南', '活动', '社交']

const goBack = () => router.back()

const handleImageUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (file.size > 5 * 1024 * 1024) { showToast('图片大小不能超过 5MB', 'error'); return }
  uploading.value = true
  try {
    form.value.image = await fileApi.uploadImage(file, 'post/image')
  } catch { showToast('图片上传失败', 'error') } finally { uploading.value = false; input.value = '' }
}

const removeImage = () => { form.value.image = '' }

const submitForm = async () => {
  if (!form.value.title.trim()) { showToast('请输入话题标题', 'warning'); return }
  loading.value = true
  try {
    await topicApi.add({
      title: form.value.title,
      description: form.value.description || undefined,
      image: form.value.image || undefined,
      category: form.value.category,
    })
    showToast('话题创建成功！', 'success')
    setTimeout(() => router.back(), 800)
  } catch { showToast('创建失败，请重试', 'error') } finally { loading.value = false }
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <!-- Header -->
      <div class="flex items-center justify-between py-md mb-md">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">创建话题</span>
        <button @click="submitForm" :disabled="loading" class="active:scale-95 transition-transform px-4 py-2 bg-primary text-white rounded-full font-label-bold text-label-bold disabled:opacity-50">
          {{ loading ? '创建中...' : '创建' }}
        </button>
      </div>

      <section class="space-y-md">
        <!-- Category -->
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">分类</label>
          <div class="flex gap-2 overflow-x-auto no-scrollbar pb-2">
            <button v-for="opt in categoryOptions" :key="opt" @click="form.category = opt"
              class="px-4 py-2 rounded-full whitespace-nowrap text-sm transition-colors"
              :class="form.category === opt ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-on-surface-variant'">
              {{ opt }}
            </button>
          </div>
        </div>

        <!-- Title -->
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">话题标题 *</label>
          <input v-model="form.title" type="text" placeholder="给话题起个名字"
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" />
        </div>

        <!-- Description -->
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">话题描述</label>
          <textarea v-model="form.description" rows="4" placeholder="描述一下这个话题..."
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none"></textarea>
        </div>

        <!-- Cover Image -->
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">封面图片</label>
          <div class="grid grid-cols-3 gap-sm">
            <div v-if="form.image" class="aspect-square rounded-xl overflow-hidden relative group">
              <img :src="form.image" class="w-full h-full object-cover" />
              <button @click="removeImage" class="absolute top-1 right-1 w-6 h-6 bg-black/50 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <span class="material-symbols-outlined text-white text-sm">close</span>
              </button>
            </div>
            <label v-else class="aspect-square bg-surface-container rounded-xl flex flex-col items-center justify-center cursor-pointer hover:bg-surface-container-high transition-colors"
              :class="{ 'opacity-50 pointer-events-none': uploading }">
              <span v-if="uploading" class="material-symbols-outlined text-3xl text-on-surface-variant animate-spin">progress_activity</span>
              <template v-else>
                <span class="material-symbols-outlined text-3xl text-on-surface-variant">add_photo_alternate</span>
                <span class="text-xs text-on-surface-variant mt-1">添加封面</span>
              </template>
              <input type="file" accept="image/jpeg,image/png,image/gif,image/webp" class="hidden" @change="handleImageUpload" />
            </label>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
