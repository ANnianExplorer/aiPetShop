import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import DeskPet from './DeskPet.vue'

// 组件只依赖路由的 push 与当前路径，组件测试里不需要真路由
const push = vi.fn()
const route = reactive({ path: '/home' })
vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
  useRoute: () => route,
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
      say: {
        tap1: '干嘛呀，我正忙着吃白饭呢',
        tap2: '摸摸头，本鱼今天心情不错',
        tap3: '你点的这一下，我记住了哦',
        tap4: '要不要去问问 Lumina 正经事？',
        eat: '吃白饭！这碗是 token 味的',
        sleep: '打个盹……',
        wake: '醒啦，找我干嘛',
      },
      work: {
        thinking: '让我想想…',
        working: '我去查一下',
        result: '正在整理线索',
        waiting: '等你确认一下',
        success: '好啦！',
        error: '呜……出错了',
      },
      menu: {
        eat: '吃白饭',
        sleep: '打个盹',
        wake: '叫醒它',
        chat: '去聊天',
        hide: '收起',
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
  el.dispatchEvent(new MouseEvent(type, { clientX: x, clientY: y, bubbles: true, cancelable: true }))
}

afterEach(() => {
  localStorage.clear()
  push.mockClear()
  vi.useRealTimers()
  vi.restoreAllMocks()
})

beforeEach(() => {
  route.path = '/home'
  // jsdom 没装 canvas 包：getContext 会往控制台刷 "Not implemented"，这里直接给 null，
  // 引擎本来就会退化成空渲染（动画逻辑照跑）
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
})

describe('DeskPet 外壳', () => {
  it('挂载一棵 canvas 桌宠，没有残留的 SVG 分层部件', () => {
    const wrapper = mountPet()
    const root = wrapper.find('.desk-pet')
    expect(root.exists()).toBe(true)
    expect(root.attributes('aria-label')).toBe('桌面宠物')
    expect(wrapper.find('canvas.desk-pet-canvas').exists()).toBe(true)
    expect(wrapper.findAll('[data-part]')).toHaveLength(0)
    wrapper.unmount()
  })

  it('挂载后主动打招呼，点气泡进入对话页', async () => {
    const wrapper = mountPet()
    await wrapper.vm.$nextTick()

    const bubble = wrapper.find('.pet-bubble')
    expect(bubble.exists()).toBe(true)
    expect(bubble.text()).toContain('在这儿陪你')

    await bubble.trigger('click')
    expect(push).toHaveBeenCalledWith({ name: 'chat' })
    wrapper.unmount()
  })

  it('单击角色会说话（不是「只换个颜色」）', async () => {
    vi.spyOn(Math, 'random').mockReturnValue(0)
    const wrapper = mountPet()
    const root = wrapper.find('.desk-pet').element
    firePointer(root, 'pointerdown', 10, 10)
    firePointer(root, 'pointerup', 10, 10)
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.pet-bubble').text()).toBe('干嘛呀，我正忙着吃白饭呢')
    // 没拖动就不该写位置
    expect(localStorage.getItem('petlumina-deskpet-pos-v2')).toBeNull()
    wrapper.unmount()
  })

  it('拖拽超过阈值算移动：写归一化位置，不当成点击', async () => {
    const wrapper = mountPet()
    const root = wrapper.find('.desk-pet').element
    firePointer(root, 'pointerdown', 10, 10)
    firePointer(root, 'pointermove', 80, 60)
    firePointer(root, 'pointerup', 80, 60)
    await wrapper.vm.$nextTick()

    const saved = JSON.parse(localStorage.getItem('petlumina-deskpet-pos-v2') ?? '{}')
    expect(typeof saved.rx).toBe('number')
    expect(typeof saved.ry).toBe('number')
    wrapper.unmount()
  })

  it('长按开菜单，菜单里能喂它吃白饭', async () => {
    vi.useFakeTimers()
    const wrapper = mountPet()
    const root = wrapper.find('.desk-pet').element
    firePointer(root, 'pointerdown', 10, 10)
    await vi.advanceTimersByTimeAsync(600)
    await wrapper.vm.$nextTick()

    const menu = wrapper.find('.pet-menu')
    expect(menu.exists()).toBe(true)
    const eat = wrapper.findAll('.pet-menu button')[0]
    await eat.trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.pet-bubble').text()).toBe('吃白饭！这碗是 token 味的')
    wrapper.unmount()
  })

  it('菜单里的「去聊天」跳对话页', async () => {
    vi.useFakeTimers()
    const wrapper = mountPet()
    const root = wrapper.find('.desk-pet').element
    firePointer(root, 'pointerdown', 10, 10)
    await vi.advanceTimersByTimeAsync(600)
    await wrapper.vm.$nextTick()

    const chat = wrapper.findAll('.pet-menu button')[3]
    await chat.trigger('click')
    expect(push).toHaveBeenCalledWith({ name: 'chat' })
    wrapper.unmount()
  })

  it('右侧小叉收起桌宠，并把选择记到 localStorage', async () => {
    const wrapper = mountPet()
    await wrapper.find('.pet-close').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.desk-pet').exists()).toBe(false)
    expect(localStorage.getItem('petlumina-deskpet-hidden')).toBe('1')
    wrapper.unmount()
  })

  it('上次收起过就不再出现（也不建引擎）', async () => {
    localStorage.setItem('petlumina-deskpet-hidden', '1')
    const wrapper = mountPet()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.desk-pet').exists()).toBe(false)
    expect(wrapper.find('canvas').exists()).toBe(false)
    wrapper.unmount()
  })

  it('登录页不挂桌宠：还没登录不该有个角色飘在上面', async () => {
    route.path = '/login'
    const wrapper = mountPet()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.desk-pet').exists()).toBe(false)
    expect(wrapper.find('canvas').exists()).toBe(false)
    wrapper.unmount()
  })

  it('登录后进入应用页才出现，退回登录页又消失', async () => {
    route.path = '/login'
    const wrapper = mountPet()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.desk-pet').exists()).toBe(false)

    route.path = '/home'
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.desk-pet').exists()).toBe(true)

    route.path = '/login'
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.desk-pet').exists()).toBe(false)
    wrapper.unmount()
  })
})
