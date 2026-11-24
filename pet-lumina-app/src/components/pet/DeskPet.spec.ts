import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import { useUserStore } from '@/stores/user'
import type { Pet } from '@/types'
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
      ariaNamed: '桌面宠物：{name}',
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
        dance: '本鱼给你扭两下！',
        spin: '转个圈，晕乎乎……',
        stretch: '伸个懒腰，继续吃白饭',
        pat: '摸头就摸头，别揪耳朵',
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
        title: '宠物动作',
        hint: '右键或长按打开动作菜单',
        eat: '吃白饭',
        dance: '跳舞',
        spin: '转圈',
        stretch: '伸懒腰',
        pat: '摸摸头',
        sleep: '打个盹',
        wake: '叫醒它',
        chat: '去聊天',
        hide: '收起',
      },
    },
  },
}

function petOf(type: Pet['type']): Pet {
  return {
    id: 'pet-1',
    userId: 'user-1',
    name: '毛豆',
    avatar: '',
    type,
    breed: '',
    age: '',
    healthScore: 88,
    todaySteps: 0,
    feedingCount: 1,
    feedingTotal: 3,
  }
}

function mountPet(pet: Pet | null = null) {
  const pinia = createPinia()
  if (pet !== null) useUserStore(pinia).currentPet = pet
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages })
  return mount(DeskPet, {
    // 组件用 Teleport 挂到 body；测试里 stub 掉，内容就留在 wrapper 内可断言
    global: { plugins: [pinia, i18n], stubs: { teleport: true } },
    attachTo: document.body,
  })
}

function menuButton(wrapper: ReturnType<typeof mountPet>, label: string) {
  const button = wrapper.findAll('.pet-menu button').find(item => item.text().includes(label))
  if (button === undefined) throw new Error(`菜单里没有「${label}」`)
  return button
}

function openContextMenu(root: Element): MouseEvent {
  const event = new MouseEvent('contextmenu', {
    clientX: 320,
    clientY: 240,
    bubbles: true,
    cancelable: true,
  })
  root.dispatchEvent(event)
  return event
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
  // 桌宠问候会按当前小时选「睡觉/吃饭/陪你」文案；固定成上午，避免 23 点跑测试时结果漂移
  vi.spyOn(Date.prototype, 'getHours').mockReturnValue(10)
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

    const chat = menuButton(wrapper, '去聊天')
    await chat.trigger('click')
    expect(push).toHaveBeenCalledWith({ name: 'chat' })
    wrapper.unmount()
  })

  it('右键打开动作菜单，阻止浏览器默认菜单', async () => {
    const wrapper = mountPet()
    const root = wrapper.find('.desk-pet').element
    const event = openContextMenu(root)
    await wrapper.vm.$nextTick()

    expect(event.defaultPrevented).toBe(true)
    const menu = wrapper.find('.pet-menu')
    expect(menu.exists()).toBe(true)
    expect(menu.attributes('role')).toBe('group')
    expect(menu.attributes('aria-label')).toBe('宠物动作')
    expect(menu.attributes('style')).toContain('left')
    for (const label of ['跳舞', '转圈', '伸懒腰', '摸摸头']) {
      expect(menu.text()).toContain(label)
    }
    wrapper.unmount()
  })

  it('右键菜单里的「跳舞」会播动作并说话', async () => {
    const wrapper = mountPet()
    openContextMenu(wrapper.find('.desk-pet').element)
    await wrapper.vm.$nextTick()

    await menuButton(wrapper, '跳舞').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.pet-bubble').text()).toBe('本鱼给你扭两下！')
    wrapper.unmount()
  })

  it('打盹后动作项禁用，叫醒后恢复', async () => {
    const wrapper = mountPet()
    openContextMenu(wrapper.find('.desk-pet').element)
    await wrapper.vm.$nextTick()
    await menuButton(wrapper, '打个盹').trigger('click')
    await wrapper.vm.$nextTick()

    openContextMenu(wrapper.find('.desk-pet').element)
    await wrapper.vm.$nextTick()
    const sleepingButtons = wrapper.findAll('.pet-menu button')
    expect(sleepingButtons.slice(0, 5).every(item => item.attributes('disabled') !== undefined)).toBe(true)
    await menuButton(wrapper, '叫醒它').trigger('click')
    await wrapper.vm.$nextTick()

    openContextMenu(wrapper.find('.desk-pet').element)
    await wrapper.vm.$nextTick()
    expect(wrapper.findAll('.pet-menu button')[0].attributes('disabled')).toBeUndefined()
    wrapper.unmount()
  })

  it('按宠物类型选动物形象，并读出宠物名字', async () => {
    const cat = mountPet(petOf('cat'))
    expect(cat.find('.desk-pet').attributes('data-sprite-kind')).toBe('cat')
    expect(cat.find('.desk-pet').attributes('aria-label')).toBe('桌面宠物：毛豆')
    cat.unmount()

    const dog = mountPet(petOf('dog'))
    expect(dog.find('.desk-pet').attributes('data-sprite-kind')).toBe('dog')
    dog.unmount()

    const other = mountPet(petOf('other'))
    expect(other.find('.desk-pet').attributes('data-sprite-kind')).toBe('bunny')
    other.unmount()
  })

  it('Escape 或点菜单外部都会关闭菜单', async () => {
    const wrapper = mountPet()
    const root = wrapper.find('.desk-pet').element
    openContextMenu(root)
    await wrapper.vm.$nextTick()
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.pet-menu').exists()).toBe(false)

    openContextMenu(root)
    await wrapper.vm.$nextTick()
    document.body.dispatchEvent(new MouseEvent('pointerdown', { bubbles: true }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.pet-menu').exists()).toBe(false)
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
