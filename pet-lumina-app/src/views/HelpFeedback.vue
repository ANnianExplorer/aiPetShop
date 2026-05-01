<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'

const router = useRouter()
const { showToast } = useToast()

const goBack = () => {
  router.back()
}

const feedbackType = ref('')
const feedbackContent = ref('')
const contactInfo = ref('')

const feedbackTypes = [
  { id: 'bug', name: '问题反馈', icon: 'bug_report' },
  { id: 'suggestion', name: '功能建议', icon: 'lightbulb' },
  { id: 'other', name: '其他', icon: 'help' }
]

const faqs = [
  { question: '如何添加宠物？', answer: '在个人中心页面点击"我的宠物"区域的"添加"按钮，填写宠物信息即可。' },
  { question: '如何录入健康数据？', answer: '在健康管理页面点击"录入数据"按钮，填写各项健康指标后提交分析。' },
  { question: '如何创建健康计划？', answer: '在健康管理页面点击"新增计划"按钮，选择计划类型并设置完成标准。' }
]

const expandedFaq = ref<number | null>(null)

const toggleFaq = (index: number) => {
  expandedFaq.value = expandedFaq.value === index ? null : index
}

const selectFeedbackType = (id: string) => {
  feedbackType.value = id
}

const handleSubmit = () => {
  if (!feedbackType.value || !feedbackContent.value) {
    showToast('请填写完整信息', 'error')
    return
  }
  showToast('反馈提交成功', 'success')
  feedbackType.value = ''
  feedbackContent.value = ''
  contactInfo.value = ''
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex items-center justify-between py-md mb-lg">
        <button @click="goBack" class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100">
          <span class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <span class="font-title-sm text-on-surface">帮助与反馈</span>
        <div class="w-10"></div>
      </div>

      <section class="mb-lg">
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">常见问题</h3>
        <div class="space-y-2">
          <div 
            v-for="(faq, index) in faqs" 
            :key="index"
            class="bg-surface-container-low rounded-xl overflow-hidden"
          >
            <button 
              @click="toggleFaq(index)"
              class="w-full flex items-center justify-between p-4 text-left"
            >
              <span class="text-sm font-label-bold text-on-surface">{{ faq.question }}</span>
              <span class="material-symbols-outlined text-on-surface-variant transition-transform" :class="{ 'rotate-180': expandedFaq === index }">
                expand_more
              </span>
            </button>
            <div v-if="expandedFaq === index" class="px-4 pb-4">
              <p class="text-sm text-on-surface-variant">{{ faq.answer }}</p>
            </div>
          </div>
        </div>
      </section>

      <section class="mb-lg">
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">提交反馈</h3>
        <div class="space-y-4">
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">反馈类型</label>
            <div class="grid grid-cols-3 gap-3">
              <button 
                v-for="type in feedbackTypes" 
                :key="type.id"
                @click="selectFeedbackType(type.id)"
                class="flex flex-col items-center gap-2 p-3 rounded-xl transition-all active:scale-95"
                :class="feedbackType === type.id ? 'bg-primary text-on-primary shadow-md' : 'bg-surface-container text-on-surface-variant hover:bg-surface-container-high'"
              >
                <span class="material-symbols-outlined text-2xl">{{ type.icon }}</span>
                <span class="text-xs font-label-bold">{{ type.name }}</span>
              </button>
            </div>
          </div>

          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">反馈内容</label>
            <textarea 
              v-model="feedbackContent" 
              placeholder="请详细描述您的问题或建议..." 
              rows="4"
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none" 
            ></textarea>
          </div>

          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">联系方式（选填）</label>
            <input 
              v-model="contactInfo" 
              placeholder="手机号或邮箱" 
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary" 
            />
          </div>

          <button 
            @click="handleSubmit" 
            class="w-full py-3.5 bg-primary text-on-primary rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform shadow-md"
          >
            提交反馈
          </button>
        </div>
      </section>

      <section>
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">联系我们</h3>
        <div class="bg-surface-container-low rounded-xl p-4 space-y-3">
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined text-on-surface-variant">mail</span>
            <div>
              <p class="text-xs text-tertiary">邮箱</p>
              <p class="text-sm text-on-surface">support@petlumina.com</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined text-on-surface-variant">phone</span>
            <div>
              <p class="text-xs text-tertiary">客服电话</p>
              <p class="text-sm text-on-surface">400-123-4567</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
