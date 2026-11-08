import { describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import DeskPet from './DeskPet.vue'

// 组件只依赖路由的 push，组件测试里不需要真路由
const push = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

const messages = {
  'zh-CN': {
    pet: {
      aria: '桌面宠物',
      hide: '收起桌宠',
      hint: {
        sleepy: '这么晚了，{name} 已经睡啦，有事明天再说',
        worried: '{name} 的健康分有点低，去看看它的记录吧',
        reminder: '你有 {count} 条未读提醒，{name} 提醒你别错过',
        hungry: '{name} 今天还没喂完，记得投喂',
        happy: '{name} 今天状态不错，陪你待一会儿',
        idle: '{name} 在这儿陪你，有事点我说话',
      },
    },
  },
}

function mountPet() {
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages })
  return mount(DeskPet, {
    // 组件用 Teleport 挂到 body；测试里 stub 掉，内容就留在 wrapper 内可断言
    global: { plugins: [createPinia(), i18n], stubs: { teleport: true } },
    attachTo: document.body,
  })
}

describe('DeskPet', () => {
  it('渲染成 SVG 宠物，并带无障碍标签', () => {
    const wrapper = mountPet()
    expect(wrapper.find('.desk-pet').exists()).toBe(true)
    expect(wrapper.find('svg.pet-svg').exists()).toBe(true)
    expect(wrapper.find('.desk-pet').attributes('aria-label')).toBe('桌面宠物')
  })

  it('挂载后主动打招呼，点击气泡进入对话页', async () => {
    vi.useFakeTimers()
    const wrapper = mountPet()
    await vi.advanceTimersByTimeAsync(900)
    await wrapper.vm.$nextTick()

    const bubble = wrapper.find('.pet-bubble')
    expect(bubble.exists()).toBe(true)
    expect(bubble.text()).toContain('在这儿陪你')

    await bubble.trigger('click')
    expect(push).toHaveBeenCalledWith({ name: 'chat' })
    vi.useRealTimers()
  })

  it('点关闭后隐藏并把选择记到 localStorage', async () => {
    const wrapper = mountPet()
    await wrapper.find('.pet-close').trigger('click')
    expect(wrapper.find('.desk-pet').exists()).toBe(false)
    expect(localStorage.getItem('petlumina-deskpet-hidden')).toBe('1')
    localStorage.removeItem('petlumina-deskpet-hidden')
    wrapper.unmount()
  })
})
