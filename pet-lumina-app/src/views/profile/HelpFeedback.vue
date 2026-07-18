<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'

const { t } = useI18n()
const router = useRouter()
const { showToast } = useToast()

const goBack = () => {
  router.back()
}

const feedbackType = ref('')
const feedbackContent = ref('')
const contactInfo = ref('')

const feedbackTypes = computed(() => [
  { id: 'bug', name: t('profile.bugReport'), icon: 'bug_report' },
  { id: 'suggestion', name: t('profile.featureSuggestion'), icon: 'lightbulb' },
  { id: 'other', name: t('profile.other'), icon: 'help' }
])

const faqs = computed(() => [
  { question: t('profile.faqAddPet'), answer: t('profile.faqAddPetAnswer') },
  { question: t('profile.faqHealthData'), answer: t('profile.faqHealthDataAnswer') },
  { question: t('profile.faqHealthPlan'), answer: t('profile.faqHealthPlanAnswer') }
])

const expandedFaq = ref<number | null>(null)

const toggleFaq = (index: number) => {
  expandedFaq.value = expandedFaq.value === index ? null : index
}

const selectFeedbackType = (id: string) => {
  feedbackType.value = id
}

const handleSubmit = () => {
  if (!feedbackType.value || !feedbackContent.value) {
    showToast(t('profile.fillRequired'), 'error')
    return
  }
  showToast(t('profile.feedbackSubmitted'), 'success')
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
        <span class="font-title-sm text-on-surface">{{ t('profile.helpFeedback') }}</span>
        <div class="w-10"></div>
      </div>

      <section class="mb-lg">
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">{{ t('profile.faq') }}</h3>
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
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">{{ t('profile.submitFeedback') }}</h3>
        <div class="space-y-4">
          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('profile.feedbackType') }}</label>
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
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('profile.feedbackContent') }}</label>
            <textarea
              v-model="feedbackContent"
              :placeholder="t('profile.feedbackPlaceholder')"
              rows="4"
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            ></textarea>
          </div>

          <div>
            <label class="font-label-bold text-label-bold text-on-surface mb-2 block">{{ t('profile.contactInfo') }}</label>
            <input
              v-model="contactInfo"
              :placeholder="t('profile.contactPlaceholder')"
              class="w-full bg-surface-container rounded-xl px-4 py-3 font-body-sm text-on-surface focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <button
            @click="handleSubmit"
            class="w-full py-3.5 bg-primary text-on-primary rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform shadow-md"
          >
            {{ t('profile.submitFeedback') }}
          </button>
        </div>
      </section>

      <section>
        <h3 class="font-label-bold text-label-bold text-on-surface mb-3">{{ t('profile.contactUs') }}</h3>
        <div class="bg-surface-container-low rounded-xl p-4 space-y-3">
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined text-on-surface-variant">mail</span>
            <div>
              <p class="text-xs text-tertiary">{{ t('profile.emailLabel') }}</p>
              <p class="text-sm text-on-surface">support@petlumina.com</p>
            </div>
          </div>
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined text-on-surface-variant">phone</span>
            <div>
              <p class="text-xs text-tertiary">{{ t('profile.phoneLabel') }}</p>
              <p class="text-sm text-on-surface">400-123-4567</p>
            </div>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>
