import { defineConfig } from '@playwright/test'

const APP_URL = process.env.E2E_APP_URL ?? 'http://127.0.0.1:5174'
const ADMIN_URL = process.env.E2E_ADMIN_URL ?? 'http://127.0.0.1:3000'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 90_000,
  expect: { timeout: 20_000 },
  reporter: [['list']],
  outputDir: '.tmp-playwright',
  use: {
    channel: 'msedge',
    headless: true,
    baseURL: APP_URL,
    viewport: { width: 390, height: 844 },
    locale: 'zh-CN',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'off',
  },
  projects: [{ name: 'msedge' }],
})
