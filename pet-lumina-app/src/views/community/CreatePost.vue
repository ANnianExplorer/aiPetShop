<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { postApi } from '@/api/post'
import { topicApi } from '@/api/topic'
import { fileApi } from '@/api/file'

const router = useRouter()
const route = useRoute()
const { showToast } = useToast()

const topicId = route.query.topicId as string | undefined
const topicTitle = ref('')

const form = ref({
  content: '',
  images: [] as string[],
  tags: [] as string[],
  category: (route.query.category as string) || 'daily'
})

const loading = ref(false)
const uploading = ref(false)
const tagOptions = ['猫咪', '狗狗', '日常', '健康', '户外', '美食', '训练', '医疗']

onMounted(async () => {
  if (topicId) {
    try {
      const topic = await topicApi.getById(topicId)
      topicTitle.value = topic?.title || ''
    } catch (e) {
      console.error('Failed to fetch topic:', e)
    }
  }
})

const goBack = () => router.back()

const addTag = (tag: string) => {
  if (tag && !form.value.tags.includes(tag)) form.value.tags.push(tag)
}
const removeTag = (tag: string) => {
  form.value.tags = form.value.tags.filter(t => t !== tag)
}

const handleImageUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) return
  for (const file of Array.from(files)) {
    if (file.size > 5 * 1024 * 1024) { showToast('图片大小不能超过 5MB', 'error'); continue }
    if (form.value.images.length >= 9) { showToast('最多上传 9 张图片', 'warning'); break }
    uploading.value = true
    try {
      const url = await fileApi.uploadImage(file, 'post/image')
      form.value.images.push(url)
    } catch { showToast('图片上传失败', 'error') } finally { uploading.value = false }
  }
  input.value = ''
}

const removeImage = (index: number) => form.value.images.splice(index, 1)

const submitForm = async () => {
  if (!form.value.content.trim()) { showToast('请输入内容', 'warning'); return }
  loading.value = true
  try {
    const tags = [...form.value.tags]
    await postApi.add({
      content: form.value.content,
      category: form.value.category,
      // 话题走显式字段，不再塞进 tags（后端 E12：post.topic_id）
      topicId: topicId ? String(topicId) : undefined,
      images: form.value.images.length > 0 ? JSON.stringify(form.value.images) : undefined,
      tags: tags.length > 0 ? JSON.stringify(tags) : undefined,
    })
    showToast('发帖成功！', 'success')
    setTimeout(() => router.back(), 800)
  } catch { showToast('发帖失败，请重试', 'error') } finally { loading.value = false }
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
        <span class="font-title-sm text-on-surface">发布帖子</span>
        <button @click="submitForm" :disabled="loading" class="active:scale-95 transition-transform px-4 py-2 bg-primary text-white rounded-full font-label-bold text-label-bold disabled:opacity-50">
          {{ loading ? '发布中...' : '发布' }}
        </button>
      </div>

      <!-- Topic hint -->
      <div v-if="topicTitle" class="flex items-center gap-2 px-4 py-2.5 bg-primary/10 rounded-xl">
        <span class="material-symbols-outlined text-primary text-[18px]">forum</span>
        <span class="text-sm text-primary font-label-bold">话题：{{ topicTitle }}</span>
      </div>

      <section class="space-y-md">
        <!-- Content -->
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">内容 *</label>
          <textarea v-model="form.content" rows="5" placeholder="分享你和宠物的故事..."
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none"></textarea>
        </div>

        <!-- Images -->
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">添加图片 <span class="text-xs text-outline">({{ form.images.length }}/9)</span></label>
          <div class="grid grid-cols-3 gap-sm">
            <div v-for="(img, index) in form.images" :key="index" class="aspect-square rounded-xl overflow-hidden relative group">
              <img :src="img" class="w-full h-full object-cover" />
              <button @click="removeImage(index)" class="absolute top-1 right-1 w-6 h-6 bg-black/50 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <span class="material-symbols-outlined text-white text-sm">close</span>
              </button>
            </div>
            <label v-if="form.images.length < 9" class="aspect-square bg-surface-container rounded-xl flex flex-col items-center justify-center cursor-pointer hover:bg-surface-container-high transition-colors"
              :class="{ 'opacity-50 pointer-events-none': uploading }">
              <span v-if="uploading" class="material-symbols-outlined text-3xl text-on-surface-variant animate-spin">progress_activity</span>
              <template v-else>
                <span class="material-symbols-outlined text-3xl text-on-surface-variant">add_photo_alternate</span>
                <span class="text-xs text-on-surface-variant mt-1">添加图片</span>
              </template>
              <input type="file" accept="image/jpeg,image/png,image/gif,image/webp" multiple class="hidden" @change="handleImageUpload" />
            </label>
          </div>
        </div>

        <!-- Tags -->
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">标签</label>
          <div class="flex flex-wrap gap-sm mb-sm">
            <span v-for="tag in form.tags" :key="tag" class="px-3 py-1 bg-primary-container text-primary rounded-full text-xs font-label-bold flex items-center gap-1">
              {{ tag }}
              <button @click="removeTag(tag)" class="hover:opacity-70"><span class="material-symbols-outlined text-sm">close</span></button>
            </span>
          </div>
          <div class="flex flex-wrap gap-sm">
            <button v-for="tag in tagOptions" :key="tag" @click="addTag(tag)"
              class="px-3 py-1 bg-surface-container-high text-on-surface-variant rounded-full text-xs font-label-bold hover:bg-primary-fixed transition-colors"
              :class="{ 'bg-primary text-white': form.tags.includes(tag) }">
              {{ tag }}
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
