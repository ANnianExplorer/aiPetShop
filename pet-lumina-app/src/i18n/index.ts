import { createI18n } from 'vue-i18n'
import zhCN from '@/locales/zh-CN.json'
import enUS from '@/locales/en-US.json'
import jaJP from '@/locales/ja-JP.json'

export type SupportedLocale = 'zh-CN' | 'en-US' | 'ja-JP'

export const SUPPORTED_LOCALES: readonly SupportedLocale[] = ['zh-CN', 'en-US', 'ja-JP']

export function isSupportedLocale(value: string): value is SupportedLocale {
  return (SUPPORTED_LOCALES as readonly string[]).includes(value)
}

// 从 localStorage 读取语言设置，默认中文；非法值回退到 zh-CN
const savedLang = localStorage.getItem('petlumina-lang') || 'zh-CN'
const initialLocale: SupportedLocale = isSupportedLocale(savedLang) ? savedLang : 'zh-CN'

const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
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
  const nextLocale: SupportedLocale = isSupportedLocale(lang) ? lang : 'zh-CN'
  i18n.global.locale.value = nextLocale
  localStorage.setItem('petlumina-lang', nextLocale)
}
