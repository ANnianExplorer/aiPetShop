<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { showToast } from 'vant'
import 'vant/es/toast/style'
import {
  AgentRequestError,
  fetchSessionMessages,
  fetchSessions,
  uploadDocument,
} from '@/api/agent'
import { applyAgentEvent, historyToBubbles } from '@/utils/chatStream'
import { citationRoute } from '@/utils/citationRoute'
import { streamChatResilient } from '@/utils/resilientChat'
import { publishWorkState } from '@/pet/signal'
import { useUserStore } from '@/stores/user'
import type { AgentEvent } from '@/api/agent'
import type { LinkState } from '@/utils/resilientChat'
import type { AgentCitation, AgentSessionItem, ChatBubble, ToolEvent } from '@/types/agent'

const { t } = useI18n()
const router = useRouter()
const userStore = useUserStore()

const SESSION_KEY = 'petlumina-agent-session'

const bubbles = ref<ChatBubble[]>([])
const draft = ref('')
const streaming = ref(false)
const sessionId = ref<string | null>(localStorage.getItem(SESSION_KEY))
const scroller = ref<HTMLElement | null>(null)
const input = ref<HTMLTextAreaElement | null>(null)
const lastError = ref<string>('')
const historyOpen = ref(false)
const historyLoading = ref(false)
const historyError = ref('')
const sessions = ref<AgentSessionItem[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const uploading = ref(false)
// 链路状态：断线自动重连时告诉用户「不是没反应，是在接回去」
const linkState = ref<LinkState>('live')
const retryAttempt = ref(0)
// 无障碍：独立播报区只播「开始回复 / 回复完成」这类状态，不跟随每个 delta，
// 否则读屏会把流式分片逐片念出来（详见 docs/plans/s1.35-chat-a11y.md）
const liveMessage = ref('')
const historyTrigger = ref<HTMLButtonElement | null>(null)
const historyPanel = ref<HTMLElement | null>(null)

let controller: AbortController | null = null
let seqCounter = 0

/** 播报一句状态；空串表示不播报 */
function announce(message: string) {
  liveMessage.value = message
}

/** 历史面板内当前可聚焦的元素（每次按键时重新收集，避免异步列表让焦点表过期） */
function focusableIn(panel: HTMLElement | null): HTMLElement[] {
  if (!panel) return []
  return Array.from(
    panel.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
    ),
  ).filter(el => !el.hasAttribute('disabled') && el.getAttribute('aria-hidden') !== 'true')
}

const petName = computed(() => userStore.currentPet?.name ?? '')
const canSend = computed(() => draft.value.trim().length > 0 && !streaming.value)

const suggestions = computed(() => [
  t('chat.suggest.health'),
  t('chat.suggest.vaccine'),
  t('chat.suggest.food'),
])

const nextId = (prefix: string) => `${prefix}-${Date.now()}-${seqCounter++}`

async function scrollToBottom() {
  await nextTick()
  const el = scroller.value
  if (el) el.scrollTop = el.scrollHeight
}

function rememberSession(id: string) {
  sessionId.value = id
  localStorage.setItem(SESSION_KEY, id)
}

async function loadHistory() {
  if (!sessionId.value) return
  try {
    const history = await fetchSessionMessages(sessionId.value)
    bubbles.value = historyToBubbles(history)
    await scrollToBottom()
  } catch (error) {
    // 会话在服务端已被清理（比如内存模式重启）：换新会话，不打断用户
    if (error instanceof AgentRequestError && (error.code === 'not_found' || error.code === 'http_404')) {
      localStorage.removeItem(SESSION_KEY)
      sessionId.value = null
      return
    }
    showToast(t('chat.historyFailed'))
  }
}

function pickDocument() {
  if (uploading.value) return
  fileInput.value?.click()
}

async function onFilePicked(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  uploading.value = true
  try {
    const doc = await uploadDocument(file, userStore.currentPet ? String(userStore.currentPet.id) : null)
    bubbles.value.push({
      id: nextId('user'),
      role: 'user',
      content: `📄 ${file.name}`,
      citations: [],
      tools: [],
    })
    await scrollToBottom()
    showToast(
      doc.status === 2
        ? t('chat.uploadReady', { name: file.name })
        : t('chat.uploadQueued', { name: file.name }),
    )
  } catch (error) {
    const message = error instanceof AgentRequestError ? error.message : String(error)
    showToast(t('chat.uploadFailed', { reason: message }))
  } finally {
    uploading.value = false
  }
}

function handleEvent(event: AgentEvent, assistant: ChatBubble) {
  // 桌宠联动：一轮对话里「在想 / 在查 / 完成 / 出错」各对应一档动画
  // （route→thinking、tool→working、done→success、error→error），与 dsh-pet 的档位映射同源。
  if (event.event === 'route') publishWorkState('thinking')
  else if (event.event === 'tool') publishWorkState('working')
  else if (event.event === 'done') publishWorkState('success')
  else if (event.event === 'error') publishWorkState('error')
  const outcome = applyAgentEvent(assistant, event)
  if (outcome.sessionId) rememberSession(outcome.sessionId)
  if (outcome.dropBubble) {
    bubbles.value = bubbles.value.filter((b) => b.id !== assistant.id)
  }
  if (outcome.error) {
    lastError.value = outcome.error
  }
  if (event.event === 'done') {
    announce(t('chat.a11y.replyDone'))
  }
  if (event.event === 'delta' || event.event === 'done') {
    void scrollToBottom()
  }
}

function handleLink(state: LinkState, attempt: number) {
  linkState.value = state
  retryAttempt.value = attempt
  if (state === 'reconnecting') {
    // 重连中：清掉上一条错误，让桌宠回到「在想」而不是一直摊成错误脸
    lastError.value = ''
    publishWorkState('thinking')
  }
}

async function send(text?: string) {
  const content = (text ?? draft.value).trim()
  if (!content || streaming.value) return

  lastError.value = ''
  linkState.value = 'live'
  retryAttempt.value = 0
  draft.value = ''
  bubbles.value.push({ id: nextId('user'), role: 'user', content, citations: [], tools: [] })

  const assistant: ChatBubble = {
    id: nextId('assistant'),
    role: 'assistant',
    content: '',
    citations: [],
    tools: [],
    streaming: true,
  }
  bubbles.value.push(assistant)
  streaming.value = true
  announce(t('chat.a11y.replyStarted'))
  publishWorkState('thinking')
  controller = new AbortController()
  await scrollToBottom()

  try {
    // 断线重连交给 resilientChat：它拿 run_id + 已收最大 id 去续传，
    // 不重发消息，所以同一轮不会被执行两次。
    await streamChatResilient(
      {
        message: content,
        sessionId: sessionId.value,
        // 后端 id 是 19 位 BigInteger，前端类型标的是 number：统一转字符串再出网
        petId: userStore.currentPet ? String(userStore.currentPet.id) : null,
      },
      { onEvent: (event) => handleEvent(event, assistant), onLink: handleLink },
      { signal: controller.signal },
    )
  } catch (error) {
    assistant.streaming = false
    if ((error as Error).name === 'AbortError') return
    if (error instanceof AgentRequestError) {
      if (error.code === 'unauthorized' || error.code === 'http_401') {
        localStorage.removeItem('satoken')
        showToast(t('chat.loginExpired'))
        void router.push('/login')
        return
      }
      lastError.value = error.message
    } else {
      lastError.value = t('chat.sendFailed')
    }
    if (!assistant.content) {
      bubbles.value = bubbles.value.filter((b) => b.id !== assistant.id)
    }
  } finally {
    streaming.value = false
    linkState.value = 'live'
    retryAttempt.value = 0
    // 出错或断流时也要把桌宠从「工作中」放出来，否则它会一直忙到下次对话
    if (lastError.value !== '') publishWorkState('error')
    controller = null
    await scrollToBottom()
    input.value?.focus()
  }
}

function retry() {
  const lastUser = [...bubbles.value].reverse().find((b) => b.role === 'user')
  if (lastUser) void send(lastUser.content)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    void send()
  }
}

function openCitation(citation: AgentCitation) {
  // 路由由后端随引用一起给出（S1.25）：前端只负责跳，不再按 kind 硬编码
  const target = citationRoute(citation)
  if (target) {
    void router.push(target)
    return
  }
  showToast(citation.label)
}

function startNewChat() {
  localStorage.removeItem(SESSION_KEY)
  sessionId.value = null
  bubbles.value = []
  lastError.value = ''
  linkState.value = 'live'
  retryAttempt.value = 0
  historyOpen.value = false
}

/** 打开历史面板：每次打开都重新拉，避免显示过期列表 */
async function openHistory() {
  if (streaming.value) {
    showToast(t('chat.thinking'))
    return
  }
  historyOpen.value = true
  historyLoading.value = true
  historyError.value = ''
  // 焦点先进入对话框：读屏会读出 aria-label，键盘用户也不会留在背景按钮上
  await nextTick()
  historyPanel.value?.focus()
  try {
    const page = await fetchSessions(1, 20)
    sessions.value = page.items
  } catch (error) {
    if (error instanceof AgentRequestError && (error.code === 'unauthorized' || error.code === 'http_401')) {
      localStorage.removeItem('satoken')
      historyOpen.value = false
      showToast(t('chat.loginExpired'))
      void router.push('/login')
      return
    }
    historyError.value = t('chat.historyLoadFailed')
  } finally {
    historyLoading.value = false
  }
}

/** 关闭历史面板：焦点还给打开它的按钮，不把用户丢在页面顶部 */
async function closeHistory() {
  if (!historyOpen.value) return
  historyOpen.value = false
  await nextTick()
  historyTrigger.value?.focus()
}

/** 历史面板内的键盘闭环：Esc 关闭；Tab 在面板内循环，不跑到背景内容里 */
function onHistoryKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    event.preventDefault()
    void closeHistory()
    return
  }
  if (event.key !== 'Tab') return

  const items = focusableIn(historyPanel.value)
  if (items.length === 0) return
  const first = items[0]
  const last = items[items.length - 1]
  const active = document.activeElement as HTMLElement | null
  const inside = active !== null && historyPanel.value?.contains(active) === true

  if (event.shiftKey) {
    if (!inside || active === first || active === historyPanel.value) {
      event.preventDefault()
      last.focus()
    }
    return
  }
  if (!inside || active === last) {
    event.preventDefault()
    first.focus()
  }
}

/** 切换到某个历史会话：先清空气泡再回读，避免上一条会话的内容串进来 */
function openSession(id: string) {
  void closeHistory()
  if (id === sessionId.value) return
  rememberSession(id)
  bubbles.value = []
  lastError.value = ''
  void loadHistory()
}

function formatWhen(value?: string | null): string {
  return value ? value.slice(0, 16) : ''
}

onMounted(() => {
  void loadHistory()
  void scrollToBottom()
})

onBeforeUnmount(() => {
  controller?.abort()
})
</script>

<template>
  <div class="flex min-h-screen flex-col bg-background">
    <!-- 顶部：返回 + 身份 + 新会话 -->
    <header class="sticky top-0 z-20 bg-background/80 px-4 pb-3 pt-safe backdrop-blur-xl">
      <div class="flex items-center gap-3 pt-4">
        <button
          class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-low text-on-surface"
          :aria-label="t('common.back')"
          @click="router.back()"
        >
          <span class="material-symbols-outlined">arrow_back</span>
        </button>
        <div class="flex flex-1 items-center gap-3">
          <div class="relative flex h-11 w-11 items-center justify-center rounded-full bg-primary/10">
            <span class="material-symbols-outlined text-2xl text-primary">pets</span>
            <span class="absolute bottom-0 right-0 h-3 w-3 rounded-full border-2 border-background bg-emerald-500" />
          </div>
          <div class="leading-tight">
            <h1 class="font-title-md text-on-surface">Lumina</h1>
            <p class="text-xs text-on-surface-variant">
              {{ petName ? t('chat.subtitlePet', { name: petName }) : t('chat.subtitle') }}
            </p>
          </div>
        </div>
        <button
          ref="historyTrigger"
          class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant"
          :aria-label="t('chat.history')"
          @click="openHistory"
        >
          <span class="material-symbols-outlined">history</span>
        </button>
        <button
          class="flex h-10 w-10 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant"
          :aria-label="t('chat.newChat')"
          @click="startNewChat"
        >
          <span class="material-symbols-outlined">edit_square</span>
        </button>
      </div>
    </header>

    <!-- 读屏播报区：只报状态（开始/完成），不报流式分片 -->
    <p data-testid="chat-live" class="sr-only" role="status" aria-live="polite" aria-atomic="true">
      {{ liveMessage }}
    </p>

    <!-- 消息区 -->
    <main
      ref="scroller"
      class="flex-1 space-y-4 overflow-y-auto px-4 pb-40 no-scrollbar"
      role="region"
      :aria-label="t('chat.a11y.logLabel')"
      :aria-busy="streaming"
      tabindex="0"
    >
      <div v-if="bubbles.length === 0" class="mt-10 space-y-6">
        <div class="glass-card rounded-3xl p-6">
          <p class="font-title-md text-on-surface">{{ t('chat.emptyTitle') }}</p>
          <p class="mt-2 text-sm leading-relaxed text-on-surface-variant">
            {{ t('chat.emptyBody') }}
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="item in suggestions"
            :key="item"
            class="rounded-full border border-outline-variant/60 px-4 py-2 text-sm text-on-surface-variant active:scale-95"
            @click="send(item)"
          >
            {{ item }}
          </button>
        </div>
      </div>

      <template v-for="bubble in bubbles" :key="bubble.id">
        <div v-if="bubble.role === 'user'" class="flex justify-end">
          <div class="max-w-[78%] rounded-3xl rounded-br-lg bg-primary px-4 py-3 text-sm leading-relaxed text-on-primary">
            {{ bubble.content }}
          </div>
        </div>

        <div v-else class="flex justify-start" data-testid="chat-assistant">
          <div class="max-w-[85%] space-y-2">
            <div class="glass-card rounded-3xl rounded-bl-lg px-4 py-3">
              <p v-if="bubble.content" class="whitespace-pre-wrap text-sm leading-relaxed text-on-surface">
                {{ bubble.content }}<span v-if="bubble.streaming" class="ml-0.5 animate-pulse" aria-hidden="true">▍</span>
              </p>
              <p v-else-if="bubble.streaming" class="text-sm text-on-surface-variant animate-pulse">
                {{ t('chat.thinking') }}
              </p>

              <div v-if="bubble.tools.length" class="mt-2 flex flex-wrap gap-1.5">
                <span
                  v-for="(tool, index) in bubble.tools"
                  :key="`${tool.name}-${index}`"
                  class="inline-flex items-center gap-1 rounded-full bg-surface-container-low px-2 py-1 text-[11px] text-on-surface-variant"
                >
                  <span class="material-symbols-outlined text-[13px]">travel_explore</span>
                  {{ t(`chat.tool.${tool.name}`, tool.name) }}
                </span>
              </div>

              <div v-if="bubble.citations.length" class="mt-3 flex flex-wrap gap-1.5 border-t border-outline-variant/40 pt-2">
                <button
                  v-for="citation in bubble.citations"
                  :key="`${citation.kind}-${citation.id}`"
                  data-testid="chat-citation"
                  class="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-[11px] text-primary active:scale-95"
                  @click="openCitation(citation)"
                >
                  <span class="material-symbols-outlined text-[13px]">link</span>
                  {{ citation.label }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>

      <div
        v-if="linkState === 'reconnecting'"
        class="flex items-center gap-2 rounded-2xl bg-secondary-container/60 px-4 py-3 text-sm text-on-secondary-container"
        role="status"
      >
        <span class="material-symbols-outlined animate-spin text-base">progress_activity</span>
        <p>{{ t('chat.reconnecting', { n: retryAttempt }) }}</p>
      </div>

      <div v-if="lastError" data-testid="chat-error" class="rounded-2xl bg-error/10 px-4 py-3 text-sm text-error" role="alert">
        <p>{{ lastError }}</p>
        <button data-testid="chat-retry" class="mt-2 font-label-bold text-primary" @click="retry">{{ t('chat.retry') }}</button>
      </div>
    </main>

    <!-- 输入区 -->
    <div class="fixed bottom-0 left-0 right-0 z-30 border-t border-outline-variant/40 bg-background/90 px-4 pb-safe pt-3 backdrop-blur-xl">
      <div class="flex items-end gap-2">
        <button
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant transition-transform active:scale-90 disabled:opacity-50"
          :disabled="uploading || streaming"
          :aria-label="t('chat.upload')"
          @click="pickDocument"
        >
          <span class="material-symbols-outlined">{{ uploading ? 'progress_activity' : 'attach_file' }}</span>
        </button>
        <input
          ref="fileInput"
          type="file"
          class="hidden"
          accept=".txt,.md,.markdown,.csv,.json,.log,.yaml,.yml,.pdf,text/plain,application/pdf"
          @change="onFilePicked"
        />
        <textarea
          ref="input"
          v-model="draft"
          data-testid="chat-input"
          rows="1"
          :placeholder="t('chat.placeholder')"
          :aria-label="t('chat.a11y.inputLabel')"
          aria-describedby="chat-disclaimer"
          class="max-h-32 flex-1 resize-none rounded-2xl bg-surface-container-low px-4 py-3 text-sm text-on-surface outline-none placeholder:text-on-surface-variant/60"
          @keydown="onKeydown"
        />
        <button
          data-testid="chat-send"
          class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full transition-transform active:scale-90"
          :class="canSend ? 'bg-primary text-on-primary' : 'bg-surface-container-high text-on-surface-variant/50'"
          :disabled="!canSend"
          :aria-label="t('chat.send')"
          @click="send()"
        >
          <span class="material-symbols-outlined">{{ streaming ? 'more_horiz' : 'send' }}</span>
        </button>
      </div>
      <p id="chat-disclaimer" class="pb-2 pt-1.5 text-center text-[10px] text-on-surface-variant/60">
        {{ t('chat.disclaimer') }}
      </p>
    </div>

    <!-- 历史会话面板 -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      leave-active-class="transition duration-150 ease-in"
      leave-to-class="opacity-0"
    >
      <div v-if="historyOpen" class="fixed inset-0 z-40">
        <div class="absolute inset-0 bg-black/30" aria-hidden="true" @click="closeHistory" />
        <transition
          enter-active-class="transition duration-200 ease-out"
          enter-from-class="translate-y-full"
          leave-active-class="transition duration-150 ease-in"
          leave-to-class="translate-y-full"
          appear
        >
          <section
            ref="historyPanel"
            class="absolute bottom-0 left-0 right-0 flex max-h-[70vh] flex-col rounded-t-3xl bg-surface pb-safe shadow-2xl"
            role="dialog"
            aria-modal="true"
            tabindex="-1"
            :aria-label="t('chat.history')"
            @keydown="onHistoryKeydown"
          >
            <div class="flex items-center justify-between px-5 pb-2 pt-4">
              <p class="font-title-md text-on-surface">{{ t('chat.history') }}</p>
              <button
                class="flex h-8 w-8 items-center justify-center rounded-full bg-surface-container-low text-on-surface-variant"
                :aria-label="t('common.back')"
                @click="closeHistory"
              >
                <span class="material-symbols-outlined text-lg">close</span>
              </button>
            </div>

            <div class="min-h-0 flex-1 overflow-y-auto px-3 pb-4 no-scrollbar">
              <p v-if="historyLoading" class="px-2 py-6 text-center text-sm text-on-surface-variant">
                {{ t('common.loading') }}
              </p>
              <p v-else-if="historyError" class="px-2 py-6 text-center text-sm text-error">
                {{ historyError }}
              </p>
              <p v-else-if="sessions.length === 0" class="px-2 py-6 text-center text-sm text-on-surface-variant">
                {{ t('chat.historyEmpty') }}
              </p>
              <button
                v-for="item in sessions"
                :key="item.id"
                class="mb-1 flex w-full items-start gap-3 rounded-2xl px-3 py-3 text-left active:bg-surface-container-low"
                :class="item.id === sessionId ? 'bg-primary/10' : ''"
                @click="openSession(item.id)"
              >
                <span class="material-symbols-outlined mt-0.5 text-xl text-primary/70">forum</span>
                <span class="min-w-0 flex-1">
                  <span class="block truncate text-sm text-on-surface">{{ item.title || t('chat.newChat') }}</span>
                  <span class="mt-0.5 block text-[11px] text-on-surface-variant">
                    {{ formatWhen(item.create_time) }} · {{ t('chat.messageCount', { count: item.message_count }) }}
                  </span>
                </span>
              </button>
            </div>
          </section>
        </transition>
      </div>
    </transition>
  </div>
</template>
