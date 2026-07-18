import { createI18n } from 'vue-i18n'
import zhCN from '@/locales/zh-CN.json'
import enUS from '@/locales/en-US.json'
import jaJP from '@/locales/ja-JP.json'

// 从 localStorage 读取语言设置，默认中文
const savedLang = localStorage.getItem('petlumina-lang') || 'zh-CN'

const i18n = createI18n({
  legacy: false,
  locale: savedLang,
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'en-US': enUS,
    'ja-JP': jaJP,
  },
})

export default i18n

// 切换语言的工具函数
export function setLocale(lang: string) {
  i18n.global.locale.value = lang as any
  localStorage.setItem('petlumina-lang', lang)
}
