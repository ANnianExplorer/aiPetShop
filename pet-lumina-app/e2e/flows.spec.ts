import { expect, test, type Page } from '@playwright/test'

const APP_URL = process.env.E2E_APP_URL ?? 'http://127.0.0.1:5174'
const ADMIN_URL = process.env.E2E_ADMIN_URL ?? 'http://127.0.0.1:3000'

// 管理端用例依赖第一条用例创建的会话；429 用例依赖独立用户的配额，故整体串行。
test.describe.configure({ mode: 'serial' })

test.beforeEach(async ({ page }) => {
  // 登录页有外部背景图；只放行本机地址，避免 CI/离线环境被外网拖住。
  await page.route('**/*', (route) => {
    const url = route.request().url()
    if (
      url.startsWith(APP_URL) ||
      url.startsWith(ADMIN_URL) ||
      url.startsWith('http://localhost') ||
      url.startsWith('http://127.0.0.1') ||
      url.startsWith('data:')
    ) {
      return route.continue()
    }
    return route.abort()
  })
})

async function loginApp(page: Page, phone: string): Promise<void> {
  await page.goto(`${APP_URL}/#/login`, { waitUntil: 'domcontentloaded' })
  await page.getByTestId('login-phone').fill(phone)
  await page.getByTestId('login-password').fill('secret123')
  await page.getByTestId('login-submit').click()
  await expect(page).toHaveURL(/#\/home/, { timeout: 30_000 })
}

async function sendChat(page: Page, text: string): Promise<void> {
  await page.getByTestId('chat-input').fill(text)
  await page.getByTestId('chat-send').click()
}

test('App：登录 → 对话 → 引用 → 回跳记录', async ({ page }) => {
  await loginApp(page, '13800001001')
  await page.goto(`${APP_URL}/#/chat`, { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('chat-input')).toBeVisible()

  await sendChat(page, '帮我看看疫苗记录')

  const assistant = page.getByTestId('chat-assistant').last()
  await expect(assistant).toContainText('9月1日打过疫苗', { timeout: 45_000 })

  const citation = assistant.getByTestId('chat-citation').first()
  await expect(citation).toContainText('疫苗记录')
  await citation.click()
  await expect(page).toHaveURL(/#\/log\/7001/, { timeout: 15_000 })
})

test.describe('管理端', () => {
  test.use({ baseURL: ADMIN_URL, viewport: { width: 1440, height: 900 } })

  test('管理员：登录 → 会话列表 → 会话详情', async ({ page }) => {
    await page.goto('/#/login', { waitUntil: 'domcontentloaded' })
    await page.getByTestId('admin-login-phone').fill('13900000000')
    await page.getByTestId('admin-login-password').fill('admin123')
    await page.getByTestId('admin-login-submit').click()
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 30_000 })

    await page.goto('/#/agent/sessions', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('admin-session-table')).toBeVisible()

    const open = page.getByTestId('admin-session-open').first()
    await expect(open).toBeVisible({ timeout: 30_000 })
    await open.click()
    await expect(page).toHaveURL(/#\/agent\/sessions\/\d+/, { timeout: 15_000 })

    const detail = page.getByTestId('admin-session-detail')
    await expect(detail).toBeVisible()
    await expect(detail.getByText('对话流')).toBeVisible()
    await expect(detail.getByText('帮我看看疫苗记录')).toBeVisible()
    await expect(detail.getByText(/9月1日打过疫苗/)).toBeVisible()
    await expect(detail.getByText(/引用.*疫苗记录/).first()).toBeVisible()
    await expect(detail.getByText('运行轨迹')).toBeVisible()
  })
})

test('App：429 → 提示「请求太频繁」+ 重试按钮', async ({ page }) => {
  await loginApp(page, '13800001002')
  await page.goto(`${APP_URL}/#/chat`, { waitUntil: 'domcontentloaded' })
  await expect(page.getByTestId('chat-input')).toBeVisible()

  // 该 Agent 进程配置为每分钟 1 次；第一问放行，第二问触发 429。
  await sendChat(page, '你好')
  await expect(page.getByTestId('chat-assistant').last()).toContainText('我在呢', { timeout: 30_000 })

  await sendChat(page, '再说一次')
  const error = page.getByTestId('chat-error')
  await expect(error).toContainText('请求太频繁', { timeout: 15_000 })
  await expect(page.getByTestId('chat-retry')).toBeVisible()

  await page.getByTestId('chat-retry').click()
  await expect(page.getByTestId('chat-error')).toContainText('请求太频繁', { timeout: 15_000 })
})
