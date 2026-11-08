import { afterEach, describe, expect, it, vi } from 'vitest'
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

/**
 * jsdom 的 MouseEvent.clientX 是只读 getter，@vue/test-utils 的 trigger 会直接赋值 →
 * 只能自己 new MouseEvent 再 dispatch（PointerEvent 在 jsdom 里也没有可用构造器）。
 */
function firePointer(el: Element, type: string, x = 0, y = 0) {
  el.dispatchEvent(
    new MouseEvent(type, { clientX: x, clientY: y, bubbles: true, cancelable: true }),
  )
}

afterEach(() => {
  localStorage.clear()
})

describe('DeskPet', () => {
  it('渲染分层角色：7 个可动部件都在', () => {
    const wrapper = mountPet()
    expect(wrapper.find('.desk-pet').exists()).toBe(true)
    expect(wrapper.find('.desk-pet').attributes('aria-label')).toBe('桌面宠物')

    const parts = wrapper.findAll('[data-part]').map((node) => node.attributes('data-part'))
    expect(parts.sort()).toEqual(['arms', 'body', 'ears', 'eyes', 'hair', 'head', 'tail'])
    wrapper.unmount()
  })

  it('挂载后主动打招呼，点气泡进入对话页', async () => {
    vi.useFakeTimers()
    const wrapper = mountPet()
    await vi.advanceTimersByTimeAsync(900)
    await wrapper.vm.$nextTick()

    const bubble = wrapper.find('.pet-bubble')
    expect(bubble.exists()).toBe(true)
    expect(bubble.text()).toContain('在这儿陪你')

    await bubble.trigger('click')
    expect(push).toHaveBeenCalledWith({ name: 'chat' })
    wrapper.unmount()
    vi.useRealTimers()
  })

  it('单击角色：出现爱心并有气泡（不是"只换一句台词"）', async () => {
    const wrapper = mountPet()
    const root = wrapper.find('.desk-pet').element
    firePointer(root, 'pointerdown', 10, 10)
    firePointer(root, 'pointerup', 10, 10)
    await wrapper.vm.$nextTick()

    expect(wrapper.findAll('.pet-heart').length).toBeGreaterThan(0)
    expect(wrapper.find('.pet-bubble').exists()).toBe(true)
    // 位置没动过，不应该写 localStorage
    expect(localStorage.getItem('petlumina-deskpet-pos')).toBeNull()
    wrapper.unmount()
  })

  it('拖拽超过阈值算移动：写位置，不再当作点击', async () => {
    const wrapper = mountPet()
    const root = wrapper.find('.desk-pet').element
    firePointer(root, 'pointerdown', 10, 10)
    firePointer(root, 'pointermove', 60, 40)
    firePointer(root, 'pointerup', 60, 40)
    await wrapper.vm.$nextTick()

    expect(localStorage.getItem('petlumina-deskpet-pos')).toContain('right')
    expect(wrapper.find('.pet-bubble').exists()).toBe(false)
    wrapper.unmount()
  })

  it('双击收起，并把选择记到 localStorage', async () => {
    const wrapper = mountPet()
    await wrapper.find('.desk-pet').trigger('dblclick')
    expect(wrapper.find('.desk-pet').exists()).toBe(false)
    expect(localStorage.getItem('petlumina-deskpet-hidden')).toBe('1')
    wrapper.unmount()
  })
})
