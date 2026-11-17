import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import zhCN from '@/locales/zh-CN.json'
import { deleteMemoryFact, exportMemory, fetchMemoryFacts } from '@/api/agent'
import { downloadTextFile } from '@/utils/download'
import { useUserStore } from '@/stores/user'
import type { AgentMemoryFact } from '@/types/agent'
import type { Pet } from '@/types'
import MyMemory from './MyMemory.vue'

vi.mock('@/api/agent', () => ({
  fetchMemoryFacts: vi.fn(),
  deleteMemoryFact: vi.fn(),
  exportMemory: vi.fn(),
}))

vi.mock('@/utils/download', () => ({ downloadTextFile: vi.fn() }))

const back = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ back }),
}))

function pet(id: string, name: string): Pet {
  return {
    id,
    userId: 'u1',
    name,
    avatar: '',
    type: 'cat',
    breed: '狸花',
    age: '2',
    healthScore: 90,
    todaySteps: 0,
    feedingCount: 0,
    feedingTotal: 3,
  }
}

function fact(overrides: Partial<AgentMemoryFact> = {}): AgentMemoryFact {
  return {
    id: '1',
    key: 'pet.name',
    label: '宠物名字',
    value: '豆豆',
    confidence: 0.9,
    update_time: '2026-11-17T08:00:00',
    ...overrides,
  }
}

const generalFacts = [
  fact({
    id: 'g1',
    key: 'user.city',
    label: '城市',
    value: '杭州',
    confidence: 0.72,
    update_time: '2026-11-16T08:00:00',
  }),
]
const doudouFacts = [
  fact({
    id: 'p1',
    key: 'pet.allergy',
    label: '过敏',
    value: '牛奶',
    confidence: 0.95,
    update_time: '2026-11-17T09:00:00',
  }),
]
const huahuaFacts = [
  fact({
    id: 'p2',
    key: 'pet.name',
    label: '宠物名字',
    value: '花花',
    confidence: 0.9,
    update_time: '2026-11-17T08:30:00',
  }),
]

function factsOf(petId: string | null): AgentMemoryFact[] {
  if (petId === '5001') return doudouFacts
  if (petId === '5002') return huahuaFacts
  return generalFacts
}

function mountView() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const store = useUserStore()
  store.pets = [pet('5001', '豆豆'), pet('5002', '花花')]
  const i18n = createI18n({ legacy: false, locale: 'zh-CN', messages: { 'zh-CN': zhCN } })
  return mount(MyMemory, {
    global: { plugins: [pinia, i18n], stubs: { teleport: true } },
  })
}

function buttonByText(wrapper: ReturnType<typeof mountView>, text: string) {
  return wrapper.findAll('button').find(button => button.text() === text)
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(fetchMemoryFacts).mockImplementation(async (petId: string | null = null) => factsOf(petId))
  vi.mocked(exportMemory).mockImplementation(async (petId: string | null = null) => ({
    version: 1,
    exported_at: '2026-11-17T14:00:00Z',
    pet_id: petId,
    facts: factsOf(petId),
  }))
  vi.mocked(deleteMemoryFact).mockResolvedValue(undefined)
})

describe('MyMemory', () => {
  it('按范围拉取后合并展示：置信度最高的排最前，宠物名带在行上', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(vi.mocked(fetchMemoryFacts).mock.calls.map(call => call[0])).toEqual([null, '5001', '5002'])
    expect(wrapper.text()).toContain('3 条记忆')

    const articles = wrapper.findAll('article')
    expect(articles).toHaveLength(3)
    expect(articles[0].text()).toContain('牛奶')
    expect(articles[0].text()).toContain('豆豆')
    expect(articles[0].text()).toContain('置信度 95%')
    expect(articles[1].text()).toContain('花花')
    expect(articles[2].text()).toContain('杭州')
  })

  it('切到某只宠物的分组后只显示该分组', async () => {
    const wrapper = mountView()
    await flushPromises()

    const chip = wrapper.findAll('button').find(button => button.text().startsWith('豆豆'))
    expect(chip).toBeTruthy()
    await chip?.trigger('click')

    expect(wrapper.findAll('article')).toHaveLength(1)
    expect(wrapper.findAll('article')[0].text()).toContain('牛奶')
  })

  it('删除要先确认，确认后按 key + pet_id 调接口并从列表移除', async () => {
    const wrapper = mountView()
    await flushPromises()

    await wrapper.findAll('article')[0].find('button').trigger('click')
    expect(wrapper.text()).toContain('删除记忆')

    const confirm = buttonByText(wrapper, '删除')
    expect(confirm).toBeTruthy()
    await confirm?.trigger('click')
    await flushPromises()

    expect(vi.mocked(deleteMemoryFact)).toHaveBeenCalledWith('pet.allergy', '5001')
    expect(wrapper.findAll('article')).toHaveLength(2)
    expect(wrapper.text()).not.toContain('牛奶')
  })

  it('删除失败时保留该条并提示，不静默吞掉', async () => {
    vi.mocked(deleteMemoryFact).mockRejectedValue(new Error('not_found'))
    const wrapper = mountView()
    await flushPromises()

    await wrapper.findAll('article')[0].find('button').trigger('click')
    await buttonByText(wrapper, '删除')?.trigger('click')
    await flushPromises()

    expect(vi.mocked(deleteMemoryFact)).toHaveBeenCalledTimes(1)
    expect(wrapper.findAll('article')).toHaveLength(3)
    expect(wrapper.text()).toContain('牛奶')
  })

  it('某个分组失败不影响其它分组，并提示部分失败', async () => {
    vi.mocked(fetchMemoryFacts).mockImplementation(async (petId: string | null = null) => {
      if (petId === '5002') throw new Error('boom')
      return factsOf(petId)
    })
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.findAll('article')).toHaveLength(2)
    expect(wrapper.text()).toContain('有 1 个分组没加载出来')
  })

  it('全部失败时显示错误态，重试后恢复', async () => {
    vi.mocked(fetchMemoryFacts).mockRejectedValue(new Error('down'))
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('记忆加载失败')
    expect(wrapper.findAll('article')).toHaveLength(0)

    vi.mocked(fetchMemoryFacts).mockImplementation(async (petId: string | null = null) => factsOf(petId))
    await buttonByText(wrapper, '重试')?.trigger('click')
    await flushPromises()

    expect(wrapper.findAll('article')).toHaveLength(3)
  })

  it('导出按范围各调一次，下载内容含 scopes', async () => {
    const wrapper = mountView()
    await flushPromises()

    const exportButton = wrapper.findAll('button').find(button => button.text().includes('导出'))
    expect(exportButton).toBeTruthy()
    await exportButton?.trigger('click')
    await flushPromises()

    expect(vi.mocked(exportMemory).mock.calls.map(call => call[0])).toEqual([null, '5001', '5002'])
    expect(vi.mocked(downloadTextFile)).toHaveBeenCalledTimes(1)

    const [filename, content] = vi.mocked(downloadTextFile).mock.calls[0]
    expect(filename).toMatch(/^petlumina-memory-\d{8}-\d{4}\.json$/)
    const parsed = JSON.parse(content) as { scopes: { pet_id: string | null; facts: unknown[] }[] }
    expect(parsed.scopes.map(scope => scope.pet_id)).toEqual([null, '5001', '5002'])
    expect(parsed.scopes[1].facts).toHaveLength(1)
  })
})
