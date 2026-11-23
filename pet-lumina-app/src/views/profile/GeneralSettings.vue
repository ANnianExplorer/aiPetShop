<script setup lang="ts">
import { ref, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from '@/composables/useToast'
import { useDarkMode } from '@/composables/useDarkMode'
import { setLocale } from '@/i18n'

const router = useRouter()
const { t } = useI18n()
const { showToast } = useToast()
const { isDark, toggleDarkMode } = useDarkMode()

const goBack = () => {
  router.back()
}

// TODO: 热点帖子推送功能 — 后续实现自动推送热门内容通知
const notificationsEnabled = ref(false)

// 国际化设置
const languages = [
  { code: 'zh-CN', label: '简体中文', flag: '🇨🇳' },
  { code: 'en-US', label: 'English', flag: '🇺🇸' },
  { code: 'ja-JP', label: '日本語', flag: '🇯🇵' },
]
const currentLang = ref(localStorage.getItem('petlumina-lang') || 'zh-CN')
const showLangPicker = ref(false)
const langTrigger = ref<HTMLButtonElement | null>(null)
const langDialog = ref<HTMLElement | null>(null)

/** 弹窗内当前可聚焦元素；每次按键重新收集，避免焦点表过期 */
const focusableInDialog = (): HTMLElement[] => {
  if (!langDialog.value) return []
  return Array.from(
    langDialog.value.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    ),
  ).filter(el => !el.hasAttribute('disabled') && el.getAttribute('aria-hidden') !== 'true')
}

const openLangPicker = async () => {
  showLangPicker.value = true
  await nextTick()
  langDialog.value?.focus()
}

const closeLangPicker = async () => {
  if (!showLangPicker.value) return
  showLangPicker.value = false
  await nextTick()
  langTrigger.value?.focus()
}

const onLangDialogKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    event.stopPropagation()
    void closeLangPicker()
    return
  }
  if (event.key !== 'Tab') return

  const items = focusableInDialog()
  if (items.length === 0) return
  const first = items[0]
  const last = items[items.length - 1]
  const focused = document.activeElement

  if (event.shiftKey && (focused === first || focused === langDialog.value)) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && focused === last) {
    event.preventDefault()
    first.focus()
  }
}

const currentLangLabel = computed(() => {
  const lang = languages.find(l => l.code === currentLang.value)
  return lang ? `${lang.flag} ${lang.label}` : '简体中文'
})

const selectLang = (code: string) => {
  currentLang.value = code
  setLocale(code)
  void closeLangPicker()
}

const toggleSetting = (setting: string) => {
  switch (setting) {
    case 'notifications':
      showToast(t('settings.hotPushDeveloping'), 'info')
      break
    case 'darkMode':
      toggleDarkMode()
      showToast(isDark.value ? t('settings.darkModeOn') : t('settings.darkModeOff'), 'success')
      break
  }
}
</script>

<template>
  <div class="pb-32 bg-background min-h-screen">
    <main class="pt-4 px-container-padding max-w-screen-xl mx-auto">
      <div class="flex items-center justify-between py-md mb-lg">
        <button
          type="button"
          :aria-label="t('common.back')"
          @click="goBack"
          class="active:scale-95 transition-transform p-2 rounded-full hover:bg-zinc-100"
        >
          <span aria-hidden="true" class="material-symbols-outlined text-emerald-700">arrow_back</span>
        </button>
        <h1 class="font-title-sm text-on-surface">{{ t('settings.title') }}</h1>
        <div class="w-10"></div>
      </div>

      <section class="space-y-4 mb-lg">
        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">{{ t('settings.notificationSettings') }}</h3>
          <div class="flex items-center justify-between py-2">
            <div class="flex items-center gap-3">
              <span aria-hidden="true" class="material-symbols-outlined text-on-surface-variant">notifications</span>
              <div>
                <span class="text-sm text-on-surface">{{ t('settings.hotPush') }}</span>
                <span class="ml-2 text-[10px] px-2 py-0.5 bg-amber-100 text-amber-600 rounded-full">{{ t('settings.developing') }}</span>
              </div>
            </div>
            <button
              type="button"
              role="switch"
              :aria-checked="notificationsEnabled"
              aria-disabled="true"
              :aria-label="t('settings.hotPush')"
              @click="toggleSetting('notifications')"
              class="w-12 h-6 rounded-full transition-colors relative bg-surface-variant"
            >
              <div class="w-5 h-5 bg-white rounded-full absolute top-0.5 translate-x-0.5 shadow-sm"></div>
            </button>
          </div>
        </div>

        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">{{ t('settings.displaySettings') }}</h3>
          <div class="flex items-center justify-between py-2">
            <div class="flex items-center gap-3">
              <span aria-hidden="true" class="material-symbols-outlined text-on-surface-variant">dark_mode</span>
              <span class="text-sm text-on-surface">{{ t('settings.darkMode') }}</span>
            </div>
            <button
              type="button"
              role="switch"
              :aria-checked="isDark"
              :aria-label="t('settings.darkMode')"
              @click="toggleSetting('darkMode')"
              class="w-12 h-6 rounded-full transition-colors relative"
              :class="isDark ? 'bg-primary' : 'bg-surface-variant'"
            >
              <div
                class="w-5 h-5 bg-white rounded-full absolute top-0.5 transition-transform shadow-sm"
                :class="isDark ? 'translate-x-6' : 'translate-x-0.5'"
              ></div>
            </button>
          </div>
        </div>

        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">{{ t('settings.languageSettings') }}</h3>
          <button
            ref="langTrigger"
            type="button"
            aria-haspopup="dialog"
            :aria-expanded="showLangPicker"
            @click="openLangPicker"
            class="w-full flex items-center justify-between py-2"
          >
            <div class="flex items-center gap-3">
              <span aria-hidden="true" class="material-symbols-outlined text-on-surface-variant">language</span>
              <span class="text-sm text-on-surface">{{ t('settings.language') }}</span>
            </div>
            <div class="flex items-center gap-1 text-sm text-on-surface-variant">
              <span>{{ currentLangLabel }}</span>
              <span aria-hidden="true" class="material-symbols-outlined text-sm">chevron_right</span>
            </div>
          </button>
        </div>

        <div class="bg-surface-container-low rounded-xl p-4">
          <h3 class="font-label-bold text-label-bold text-on-surface mb-3">{{ t('settings.cacheManagement') }}</h3>
          <button
            @click="showToast(t('settings.cacheCleared'), 'success')"
            class="w-full py-3 bg-surface-container text-on-surface rounded-xl font-label-bold text-label-bold active:scale-95 transition-transform"
          >
            {{ t('settings.clearCache') }}
          </button>
        </div>
      </section>
    </main>

    <!-- 语言选择弹窗 -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showLangPicker" class="fixed inset-0 z-50 flex items-center justify-center p-6">
          <div class="absolute inset-0 bg-black/40" @click="closeLangPicker"></div>
          <div
            ref="langDialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="lang-dialog-title"
            tabindex="-1"
            class="relative w-full max-w-sm bg-surface-container-low dark:bg-surface-container-low rounded-3xl p-6 animate-scale-in z-10 focus:outline-none"
            @keydown="onLangDialogKeydown"
          >
            <div class="flex justify-between items-center mb-6">
              <h3 id="lang-dialog-title" class="font-title-sm text-title-sm text-on-surface">{{ t('settings.selectLanguage') }}</h3>
              <button
                type="button"
                :aria-label="t('common.close')"
                @click="closeLangPicker"
                class="p-2 rounded-full hover:bg-surface-container-high transition-colors"
              >
                <span aria-hidden="true" class="material-symbols-outlined text-on-surface-variant">close</span>
              </button>
            </div>
            <div class="space-y-2">
              <button
                v-for="lang in languages"
                :key="lang.code"
                type="button"
                @click="selectLang(lang.code)"
                class="w-full flex items-center justify-between p-4 rounded-xl transition-all"
                :class="currentLang === lang.code ? 'bg-primary/10 ring-2 ring-primary/30' : 'hover:bg-surface-container-high'"
              >
                <div class="flex items-center gap-3">
                  <span aria-hidden="true" class="text-2xl">{{ lang.flag }}</span>
                  <span class="text-sm text-on-surface">{{ lang.label }}</span>
                </div>
                <span v-if="currentLang === lang.code" class="material-symbols-outlined text-primary" aria-hidden="true">check_circle</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
</style>
