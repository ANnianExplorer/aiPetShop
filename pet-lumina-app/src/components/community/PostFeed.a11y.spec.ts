import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createMemoryHistory, createRouter } from 'vue-router'
import zhCN from '@/locales/zh-CN.json'
import PostFeed from './PostFeed.vue'
import type { Post } from '@/types'

vi.mock('@/api/post', () => ({
  postApi: {
    toggleLike: vi.fn(),
    toggleFavorite: vi.fn(),
  },
}))

vi.mock('@/composables/useToast', () => ({
  useToast: () => ({ showToast: vi.fn() }),
}))

vi.mock('@/components/common/ShareModal.vue', () => ({
  default: { template: '<div data-test="share-modal" />' },
}))

function makePost(overrides: Partial<Post> = {}): Post {
  return {
    id: 'p1',
    authorId: 'u1',
    content: '今天带毛豆去公园散步，遇到了一只超大的金毛，玩得特别开心，回家就睡倒了。',
    imageList: ['https://example.com/post.jpg'],
    tagList: ['日常', 'topic:公园'],
    likes: 3,
    comments: 2,
    isLiked: 0,
    isFavorited: 0,
    user: {
      id: 'u1',
      nickname: '小鱼干',
      avatar: 'https://example.com/avatar.jpg',
      location: '杭州',
    },
    createTime: '2026-11-24 10:00',
    ...overrides,
  }
}

async function mountFeed(posts: Post[]) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/feed', name: 'feed', component: { template: '<div />' } },
      { path: '/post/:id', name: 'postDetail', component: { template: '<div />' } },
    ],
  })
  await router.push('/feed')
  await router.isReady()

  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  const wrapper = mount(PostFeed, {
    props: { posts },
    attachTo: document.body,
    global: { plugins: [router, i18n] },
  })
  return { wrapper, router }
}

beforeEach(() => {
  document.body.innerHTML = ''
})

afterEach(() => {
  document.body.innerHTML = ''
})

describe('PostFeed 无障碍', () => {
  it('卡片主体是链接，名称包含作者与摘要', async () => {
    const { wrapper } = await mountFeed([makePost()])

    const link = wrapper.get('a[href="/post/p1"]')
    const label = link.attributes('aria-label') ?? ''
    expect(label).toContain('小鱼干')
    expect(label).toContain('今天带毛豆去公园散步')
    expect(link.classes()).toContain('block')

    wrapper.unmount()
  })

  it('头像为装饰图，帖子图有描述，图标按钮有可读名称', async () => {
    const { wrapper } = await mountFeed([makePost()])

    expect(wrapper.find('img[alt=""]').exists()).toBe(true)
    expect(wrapper.get('img[alt="小鱼干 的帖子图片"]').attributes('src')).toBe(
      'https://example.com/post.jpg',
    )

    expect(wrapper.find('button[aria-label="更多操作"]').exists()).toBe(true)
    expect(wrapper.find('button[aria-label="点赞，当前 3 个赞"]').exists()).toBe(true)
    expect(wrapper.find('button[aria-label="评论，当前 2 条评论"]').exists()).toBe(true)
    expect(wrapper.find('button[aria-label="收藏"]').exists()).toBe(true)
    expect(wrapper.find('button[aria-label="分享帖子"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('已点赞/已收藏时按钮名称切换为取消语义', async () => {
    const { wrapper } = await mountFeed([makePost({ isLiked: 1, isFavorited: 1 })])

    expect(wrapper.find('button[aria-label="取消点赞，当前 3 个赞"]').exists()).toBe(true)
    expect(wrapper.find('button[aria-label="取消收藏"]').exists()).toBe(true)

    wrapper.unmount()
  })

  it('作者缺失时链接与图片回退为匿名用户', async () => {
    const { wrapper } = await mountFeed([makePost({ user: undefined })])

    expect(wrapper.get('a[href="/post/p1"]').attributes('aria-label')).toContain('匿名用户')
    expect(wrapper.find('img[alt="匿名用户 的帖子图片"]').exists()).toBe(true)

    wrapper.unmount()
  })
})
