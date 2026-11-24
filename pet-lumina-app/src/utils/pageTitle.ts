import { watch } from 'vue'
import type { Router } from 'vue-router'

export const APP_NAME = 'PetLumina'

/**
 * 具名路由 → 页面标题 i18n key。
 *
 * 这里必须覆盖 router/index.ts 里所有具名路由；pageTitle.spec.ts 会遍历真实
 * 路由表守住这一点，新增路由却忘了补标题会直接让测试变红。
 */
export const PAGE_TITLE_KEYS: Readonly<Record<string, string>> = {
  login: 'pageTitle.login',
  signUp: 'pageTitle.signUp',
  resetPassword: 'pageTitle.resetPassword',
  home: 'pageTitle.home',
  petStudio: 'pageTitle.petStudio',
  chat: 'pageTitle.chat',
  community: 'pageTitle.community',
  wellness: 'pageTitle.wellness',
  profile: 'pageTitle.profile',
  lifeLog: 'pageTitle.lifeLog',
  postDetail: 'pageTitle.postDetail',
  logDetail: 'pageTitle.logDetail',
  scheduleList: 'pageTitle.scheduleList',
  addReminder: 'pageTitle.addReminder',
  notifications: 'pageTitle.notifications',
  newLog: 'pageTitle.newLog',
  newTopic: 'pageTitle.newTopic',
  createPost: 'pageTitle.createPost',
  topicDetail: 'pageTitle.topicDetail',
  topicsList: 'pageTitle.topicsList',
  addPlan: 'pageTitle.addPlan',
  weeklyHealthDetail: 'pageTitle.weeklyHealthDetail',
  recordHealthData: 'pageTitle.recordHealthData',
  addPet: 'pageTitle.addPet',
  petDetail: 'pageTitle.petDetail',
  editProfile: 'pageTitle.editProfile',
  myMemory: 'pageTitle.myMemory',
  accountSecurity: 'pageTitle.accountSecurity',
  generalSettings: 'pageTitle.generalSettings',
  helpFeedback: 'pageTitle.helpFeedback',
  userProfile: 'pageTitle.userProfile',
}

/** 只接受字符串路由名；未知/空名返回 null。 */
export function titleKeyForRouteName(name: unknown): string | null {
  if (typeof name !== 'string') return null
  return Object.prototype.hasOwnProperty.call(PAGE_TITLE_KEYS, name)
    ? PAGE_TITLE_KEYS[name]
    : null
}

/** `Home · PetLumina`；拿不到页面名时退化为 `PetLumina`。 */
export function formatDocumentTitle(pageTitle: string | null | undefined): string {
  const trimmed = pageTitle?.trim()
  return trimmed ? `${trimmed} · ${APP_NAME}` : APP_NAME
}

export type DocumentTitleTarget = Pick<Document, 'title'>

/**
 * 把当前路由名翻译成标题写入 document.title，并返回最终标题（便于测试断言）。
 * 副作用只有 `doc.title` 一处，路由与语言变更都由调用方驱动。
 */
export function applyDocumentTitle(
  routeName: unknown,
  translate: (key: string) => string,
  doc: DocumentTitleTarget = document,
): string {
  const key = titleKeyForRouteName(routeName)
  const title = formatDocumentTitle(key ? translate(key) : null)
  doc.title = title
  return title
}

/**
 * 安装路由标题：每次导航后更新，语言切换时用当前路由重算。
 * 返回停止函数，测试或热更新场景可解除订阅。
 */
export function installDocumentTitle(
  router: Router,
  translate: (key: string) => string,
  locale: { readonly value: string },
  doc: DocumentTitleTarget = document,
): () => void {
  const sync = () => {
    applyDocumentTitle(router.currentRoute.value.name, translate, doc)
  }

  const stopAfterEach = router.afterEach((to) => {
    applyDocumentTitle(to.name, translate, doc)
  })
  const stopWatch = watch(() => locale.value, sync)

  sync()

  return () => {
    stopAfterEach()
    stopWatch()
  }
}
