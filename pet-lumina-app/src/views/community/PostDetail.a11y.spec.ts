import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createI18n } from 'vue-i18n'
import { createMemoryHistory, createRouter } from 'vue-router'
import zhCN from '@/locales/zh-CN.json'
import type { Post } from '@/types'
import { postApi } from '@/api/post'
import { commentApi } from '@/api/comment'
import PostDetail from './PostDetail.vue'

vi.mock('@/api/post', () => ({
  postApi: {
    add: vi.fn(),
    edit: vi.fn(),
    delete: vi.fn(),
    getById: vi.fn(),
    listPage: vi.fn(),
    toggleLike: vi.fn(),
    toggleFavorite: vi.fn(),
  },
}))

vi.mock('@/api/comment', () => ({
  commentApi: {
    add: vi.fn(),
    delete: vi.fn(),
    listPage: vi.fn(),
    toggleLike: vi.fn(),
  },
}))

const Empty = { template: '<div />' }

const basePost: Post = {
  id: 'p1',
  authorId: 'u1',
  content: '今天带小鱼去体检',
  imageList: [],
  tagList: [],
  likes: 3,
  comments: 0,
  isLiked: 0,
  isFavorited: 0,
  createTime: '2026-11-26T10:00:00',
  user: { id: 'u1', nickname: '小鱼', avatar: '' },
}

async function mountPostDetail(post: Post) {
  vi.mocked(postApi.getById).mockResolvedValue(post)
  vi.mocked(commentApi.listPage).mockResolvedValue({ records: [], total: 0 })

  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: Empty },
      { path: '/post/:id', name: 'postDetail', component: Empty },
      { path: '/user/:id', name: 'userProfile', component: Empty },
    ],
  })
  await router.push('/post/p1')
  await router.isReady()

  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  const wrapper = mount(PostDetail, {
    attachTo: document.body,
    global: {
      plugins: [router, i18n],
      stubs: { ShareModal: true, CommentModal: true },
    },
  })
  await flushPromises()
  return wrapper
}

describe('PostDetail 作者信息无障碍', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
    vi.clearAllMocks()
  })

  it('作者头像与昵称是通往用户主页的链接', async () => {
    const wrapper = await mountPostDetail(basePost)

    const authorLink = wrapper.find('a[href="/user/u1"]')
    expect(authorLink.exists()).toBe(true)
    expect(authorLink.attributes('aria-label')).toContain('小鱼')
    expect(authorLink.find('img').attributes('alt')).toBe('')

    wrapper.unmount()
  })

  it('没有作者 id 时不渲染用户主页链接', async () => {
    const postWithoutUser: Post = { ...basePost, user: undefined }
    const wrapper = await mountPostDetail(postWithoutUser)

    expect(wrapper.find('a[href^="/user/"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('今天带小鱼去体检')

    wrapper.unmount()
  })
})
