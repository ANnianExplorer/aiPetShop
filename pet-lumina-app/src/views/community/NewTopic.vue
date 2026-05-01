<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { showToast } = useToast()

const form = ref({
  title: '',
  description: '',
  images: [] as string[],
  tags: [] as string[],
  tagInput: ''
})

const tagOptions = ['猫咪', '狗狗', '日常', '健康', '户外', '美食', '训练', '医疗']

const goBack = () => {
  router.back()
}

const addTag = (tag: string) => {
  if (tag && !form.value.tags.includes(tag)) {
    form.value.tags.push(tag)
  }
}

const removeTag = (tag: string) => {
  form.value.tags = form.value.tags.filter(t => t !== tag)
}

const submitForm = () => {
  if (!form.value.title) {
    showToast('请输入标题', 'warning')
    return
  }
  
  showToast('发布成功！', 'success')
  setTimeout(() => {
    router.back()
  }, 800)
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto space-y-lg">
      <div class="flex items-center justify-between py-md mb-md">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">发布记录</span>
        <button @click="submitForm" class="active:scale-95 transition-transform px-4 py-2 bg-primary text-white rounded-full font-label-bold text-label-bold">
          发布
        </button>
      </div>

      <section class="space-y-md">
        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">标题 *</label>
          <input 
            v-model="form.title" 
            type="text" 
            placeholder="给这个精彩瞬间起个标题" 
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">描述</label>
          <textarea 
            v-model="form.description" 
            rows="4" 
            placeholder="记录这个美好时刻..." 
            class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none"
          ></textarea>
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">添加图片</label>
          <div class="grid grid-cols-3 gap-sm">
            <div class="aspect-square bg-surface-container rounded-xl flex flex-col items-center justify-center cursor-pointer hover:bg-surface-container-high transition-colors">
              <span class="material-symbols-outlined text-3xl text-on-surface-variant">add_photo_alternate</span>
              <span class="text-xs text-on-surface-variant mt-1">添加图片</span>
            </div>
          </div>
        </div>

        <div>
          <label class="font-label-bold text-label-bold text-on-surface mb-2 block">标签</label>
          <div class="flex flex-wrap gap-sm mb-sm">
            <span 
              v-for="tag in form.tags" 
              :key="tag"
              class="px-3 py-1 bg-primary-container text-primary rounded-full text-xs font-label-bold flex items-center gap-1"
            >
              {{ tag }}
              <button @click="removeTag(tag)" class="hover:opacity-70">
                <span class="material-symbols-outlined text-sm">close</span>
              </button>
            </span>
          </div>
          <div class="flex flex-wrap gap-sm">
            <button 
              v-for="tag in tagOptions" 
              :key="tag"
              @click="addTag(tag)"
              class="px-3 py-1 bg-surface-container-high text-on-surface-variant rounded-full text-xs font-label-bold hover:bg-primary-fixed transition-colors"
              :class="{ 'bg-primary text-white': form.tags.includes(tag) }"
            >
              {{ tag }}
            </button>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
