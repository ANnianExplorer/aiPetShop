import { describe, expect, it } from 'vitest'
import { nextTick, ref } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'
import router from '@/router'
import zhCN from '@/locales/zh-CN.json'
import enUS from '@/locales/en-US.json'
import jaJP from '@/locales/ja-JP.json'
import {
  APP_NAME,
  PAGE_TITLE_KEYS,
  applyDocumentTitle,
  formatDocumentTitle,
  installDocumentTitle,
  titleKeyForRouteName,
} from './pageTitle'

const messagesByLocale: Record<string, unknown> = {
  'zh-CN': zhCN,
  'en-US': enUS,
  'ja-JP': jaJP,
}

function messageAt(messages: unknown, key: string): unknown {
  return key.split('.').reduce<unknown>((acc, part) => {
    if (acc && typeof acc === 'object') {
      return (acc as Record<string, unknown>)[part]
    }
    return undefined
  }, messages)
}

describe('formatDocumentTitle', () => {
  it('页面名加应用后缀', () => {
    expect(formatDocumentTitle('首页')).toBe(`首页 · ${APP_NAME}`)
  })

  it('空值退化为应用名', () => {
    expect(formatDocumentTitle(null)).toBe(APP_NAME)
    expect(formatDocumentTitle(undefined)).toBe(APP_NAME)
    expect(formatDocumentTitle('   ')).toBe(APP_NAME)
  })
})

describe('titleKeyForRouteName', () => {
  it('已知路由返回 i18n key', () => {
    expect(titleKeyForRouteName('home')).toBe('pageTitle.home')
    expect(titleKeyForRouteName('postDetail')).toBe('pageTitle.postDetail')
  })

  it('未知路由名或非字符串返回 null', () => {
    expect(titleKeyForRouteName('not-exist')).toBeNull()
    expect(titleKeyForRouteName(undefined)).toBeNull()
    expect(titleKeyForRouteName(42)).toBeNull()
  })
})

describe('applyDocumentTitle', () => {
  it('只写 doc.title，返回最终标题', () => {
    const doc = { title: '旧标题' }
    const title = applyDocumentTitle('home', (key) => `T:${key}`, doc)
    expect(title).toBe('T:pageTitle.home · PetLumina')
    expect(doc.title).toBe('T:pageTitle.home · PetLumina')
  })

  it('未知路由写应用名', () => {
    const doc = { title: '' }
    expect(applyDocumentTitle(undefined, (key) => key, doc)).toBe('PetLumina')
  })
})

describe('installDocumentTitle', () => {
  it('导航后更新标题，语言变化后复算，停止后不再更新', async () => {
    const testRouter = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/home', name: 'home', component: { template: '<div />' } },
        { path: '/post/:id', name: 'postDetail', component: { template: '<div />' } },
      ],
    })
    const locale = ref('zh-CN')
    const translate = (key: string) => {
      const value = messageAt(messagesByLocale[locale.value], key)
      return typeof value === 'string' ? value : key
    }
    const doc = { title: '' }

    const stop = installDocumentTitle(testRouter, translate, locale, doc)
    expect(doc.title).toBe('PetLumina')

    await testRouter.push('/home')
    await testRouter.isReady()
    expect(doc.title).toBe('首页 · PetLumina')

    locale.value = 'en-US'
    await nextTick()
    expect(doc.title).toBe('Home · PetLumina')

    await testRouter.push('/post/p1')
    expect(doc.title).toBe('Post Details · PetLumina')

    stop()
    locale.value = 'ja-JP'
    await nextTick()
    expect(doc.title).toBe('Post Details · PetLumina')
  })
})

describe('路由标题覆盖', () => {
  const namedRoutes = router.getRoutes().filter((route) => typeof route.name === 'string')

  it('真实路由表每个具名路由都有标题 key，且没有多余映射', () => {
    expect(namedRoutes.length).toBeGreaterThanOrEqual(31)
    expect(namedRoutes.map((route) => route.name).sort()).toEqual(Object.keys(PAGE_TITLE_KEYS).sort())
  })

  it('三份语言包都覆盖全部 pageTitle key 且非空', () => {
    const keys = Object.values(PAGE_TITLE_KEYS)
    expect(new Set(keys).size).toBe(keys.length)

    for (const [locale, messages] of Object.entries(messagesByLocale)) {
      for (const key of keys) {
        const value = messageAt(messages, key)
        expect(value, `${locale} 缺少 ${key}`).toBeTypeOf('string')
        expect((value as string).trim(), `${locale} 的 ${key} 为空`).not.toBe('')
      }
    }
  })
})
